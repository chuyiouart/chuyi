#!/usr/bin/env python
"""Safely release one workshop daily manifest from a clean Git checkout."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PUBLIC_BASE = "https://chuyiouart.github.io/chuyi/ip-object-workshop/"
EXPECTED_REPO_PATH = "chuyiouart/chuyi"
TRANSIENT_GIT_ERRORS = (
    "connection closed",
    "connection reset",
    "connection timed out",
    "timed out",
    "could not resolve host",
    "failed to connect",
    "network is unreachable",
    "remote end hung up unexpectedly",
    "ssh_exchange_identification",
    "tls connection",
)


def run(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if check and result.returncode:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(args)}\n"
            f"stdout: {result.stdout.strip()}\nstderr: {result.stderr.strip()}"
        )
    return result


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], repo, check=check)


def git_with_retry(
    repo: Path,
    *args: str,
    attempts: int = 3,
    delays: tuple[int, ...] = (5, 15),
) -> subprocess.CompletedProcess[str]:
    """Retry only transient Git transport failures; fail fast on logical errors."""
    last: subprocess.CompletedProcess[str] | None = None
    for attempt in range(attempts):
        last = git(repo, *args, check=False)
        if last.returncode == 0:
            return last
        diagnostic = f"{last.stdout}\n{last.stderr}".lower()
        transient = any(marker in diagnostic for marker in TRANSIENT_GIT_ERRORS)
        if not transient or attempt == attempts - 1:
            raise RuntimeError(
                f"git command failed after {attempt + 1} attempt(s): git {' '.join(args)}\n"
                f"stdout: {last.stdout.strip()}\nstderr: {last.stderr.strip()}"
            )
        time.sleep(delays[min(attempt, len(delays) - 1)])
    raise RuntimeError(f"git command failed without a result: git {' '.join(args)}")


def is_expected_remote(remote: str) -> bool:
    """Accept any SSH host alias or HTTPS host that targets the expected repo path."""
    return bool(
        re.search(
            rf"(?:[:/]){re.escape(EXPECTED_REPO_PATH)}(?:\.git)?/?$",
            remote.strip(),
            flags=re.IGNORECASE,
        )
    )


def verify_repo(repo: Path, workshop: Path) -> None:
    if not (repo / ".git").exists():
        raise RuntimeError(f"not a git checkout: {repo}")
    if not (workshop / "scripts" / "workshop_publish.py").exists():
        raise RuntimeError("workshop publisher is missing")
    remote = git(repo, "remote", "get-url", "origin").stdout.strip()
    if not is_expected_remote(remote):
        raise RuntimeError(f"unexpected origin remote: {remote}")
    branch = git(repo, "branch", "--show-current").stdout.strip()
    if branch != "main":
        raise RuntimeError(f"expected main branch, got: {branch}")
    dirty = git(repo, "status", "--porcelain", "--", "ip-object-workshop").stdout.strip()
    if dirty:
        raise RuntimeError(f"workshop tree is not clean before release:\n{dirty}")


def verify_live(url: str, expected_title: str, attempts: int = 18, delay: int = 10) -> None:
    last_error = ""
    for _ in range(attempts):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "workshop-release-verifier/1.0"})
            with urllib.request.urlopen(request, timeout=20) as response:
                body = response.read().decode("utf-8", "ignore")
                if response.status == 200 and expected_title in body:
                    return
                last_error = f"HTTP {response.status}; title missing={expected_title not in body}"
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = repr(exc)
        time.sleep(delay)
    raise RuntimeError(f"live verification failed for {url}: {last_error}")


def article_url_from_manifest(manifest: dict) -> str:
    return f"{PUBLIC_BASE}updates/{manifest['date']}-{manifest['slug']}.html"


def release(repo: Path, manifest_path: Path, verify_only: bool = False) -> dict:
    repo = repo.resolve()
    workshop = repo / "ip-object-workshop"
    manifest_path = manifest_path.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    live_url = article_url_from_manifest(manifest)

    if verify_only:
        verify_live(live_url, manifest["title"], attempts=2, delay=2)
        return {"status": "verified", "url": live_url, "title": manifest["title"]}

    verify_repo(repo, workshop)
    git_with_retry(repo, "pull", "--ff-only", "origin", "main")

    publisher = workshop / "scripts" / "workshop_publish.py"
    result = run(
        [sys.executable, str(publisher), "publish", "--root", str(workshop), "--manifest", str(manifest_path)],
        repo,
    )
    published = json.loads(result.stdout)
    run([sys.executable, str(publisher), "validate", "--root", str(workshop)], repo)

    article_rel = Path(published["article"]).resolve().relative_to(repo).as_posix()
    date = manifest["date"]
    allowlist = [
        "ip-object-workshop/course-calendar.json",
        "ip-object-workshop/course-updates.js",
        article_rel,
        f"ip-object-workshop/assets/updates/{date}",
    ]
    git(repo, "add", "--", *allowlist)
    staged = git(repo, "diff", "--cached", "--name-only", "--", "ip-object-workshop").stdout.splitlines()
    allowed_prefixes = (
        "ip-object-workshop/course-calendar.json",
        "ip-object-workshop/course-updates.js",
        article_rel,
        f"ip-object-workshop/assets/updates/{date}/",
    )
    unexpected = [path for path in staged if not path.startswith(allowed_prefixes)]
    if unexpected:
        git(repo, "reset", "--", *staged)
        raise RuntimeError(f"unexpected staged paths: {unexpected}")

    if staged:
        git(repo, "commit", "-m", f"content: publish workshop update {date}")
        git_with_retry(repo, "push", "origin", "main")
    verify_live(live_url, manifest["title"])
    commit = git(repo, "rev-parse", "HEAD").stdout.strip()
    return {
        "status": "published" if staged else "already_published",
        "url": live_url,
        "title": manifest["title"],
        "commit": commit,
        "staged_paths": staged,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    print(json.dumps(release(args.repo, args.manifest, args.verify_only), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
