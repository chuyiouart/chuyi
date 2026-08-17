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


def verify_repo(repo: Path, workshop: Path, *, allow_dirty: bool = False) -> list[str]:
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
    dirty = git(repo, "status", "--porcelain", "-uall", "--", "ip-object-workshop").stdout.splitlines()
    if dirty and not allow_dirty:
        raise RuntimeError(f"workshop tree is not clean before release:\n{dirty}")
    return dirty


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


def build_release_allowlist(repo: Path, manifest: dict, published: dict) -> list[str]:
    """Return exact existing release files; never stage a directory by assumption."""
    repo = repo.resolve()
    workshop = repo / "ip-object-workshop"
    article = Path(str(published.get("article") or "")).resolve()
    paths = [
        workshop / "course-calendar.json",
        workshop / "course-updates.js",
        workshop / "index.html",
        article,
    ]
    asset_root = (workshop / "assets" / "updates" / str(manifest["date"])).resolve()
    for asset in published.get("webImageAssets") or manifest.get("webImageAssets") or []:
        rows = list(asset.get("derivatives") or [])
        fallback = asset.get("fallback")
        if isinstance(fallback, dict):
            rows.append(fallback)
        for row in rows:
            path = Path(str(row.get("path") or "")).resolve()
            try:
                path.relative_to(asset_root)
            except ValueError as exc:
                raise RuntimeError(f"release asset escapes date allowlist: {path}") from exc
            paths.append(path)
    result: list[str] = []
    for path in paths:
        try:
            relative = path.relative_to(repo).as_posix()
        except ValueError as exc:
            raise RuntimeError(f"release path escapes repository: {path}") from exc
        if not path.is_file():
            raise RuntimeError(f"release allowlist file is missing: {relative}")
        if relative not in result:
            result.append(relative)
    return result


def classify_checkpoint_dirty_paths(status_lines: list[str], allowlist: list[str]) -> list[str]:
    """Accept only interrupted-release bytes already in the exact allowlist."""
    allowed = set(allowlist)
    observed: list[str] = []
    for line in status_lines:
        if len(line) < 4 or " -> " in line:
            raise RuntimeError(f"unsupported dirty checkpoint status: {line}")
        path = line[3:].strip()
        if path not in allowed:
            raise RuntimeError(f"unexpected dirty checkpoint path: {path}")
        observed.append(path)
    return observed


def release(repo: Path, manifest_path: Path, verify_only: bool = False) -> dict:
    repo = repo.resolve()
    workshop = repo / "ip-object-workshop"
    manifest_path = manifest_path.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    live_url = article_url_from_manifest(manifest)

    if verify_only:
        verify_live(live_url, manifest["title"], attempts=2, delay=2)
        return {"status": "verified", "url": live_url, "title": manifest["title"]}

    dirty = verify_repo(repo, workshop, allow_dirty=True)
    article_path = workshop / "updates" / f"{manifest['date']}-{manifest['slug']}.html"
    checkpoint_published = {
        "status": "partial_media_published" if manifest.get("missingRoles") else "published",
        "missingRoles": manifest.get("missingRoles", []),
        "media_status": manifest.get("media_status"),
        "passedRoles": manifest.get("passedRoles", []),
        "pendingRoles": manifest.get("pendingRoles", manifest.get("missingRoles", [])),
        "article": str(article_path),
        "webImageAssets": manifest.get("webImageAssets", []),
    }
    checkpoint_allowlist = build_release_allowlist(repo, manifest, checkpoint_published) if dirty else []
    if dirty:
        classify_checkpoint_dirty_paths(dirty, checkpoint_allowlist)
        published = checkpoint_published
        resumed_checkpoint = True
    else:
        git_with_retry(repo, "pull", "--ff-only", "origin", "main")
        publisher = workshop / "scripts" / "workshop_publish.py"
        result = run(
            [sys.executable, str(publisher), "publish", "--root", str(workshop), "--manifest", str(manifest_path)],
            repo,
        )
        published = json.loads(result.stdout)
        run([sys.executable, str(publisher), "validate", "--root", str(workshop)], repo)
        resumed_checkpoint = False

    allowlist = build_release_allowlist(repo, manifest, published)
    git(repo, "add", "--", *allowlist)
    staged = git(repo, "diff", "--cached", "--name-only", "--", "ip-object-workshop").stdout.splitlines()
    unexpected = [path for path in staged if path not in set(allowlist)]
    if unexpected:
        git(repo, "reset", "--", *staged)
        raise RuntimeError(f"unexpected staged paths: {unexpected}")

    if staged:
        git(repo, "commit", "-m", f"content: publish workshop update {manifest['date']}")
        git_with_retry(repo, "push", "origin", "main")
    verify_live(live_url, manifest["title"])
    commit = git(repo, "rev-parse", "HEAD").stdout.strip()
    release_status = published.get("status", "published")
    return {
        "status": release_status if staged else "already_published",
        "missing_roles": published.get("missingRoles", []),
        "media_status": published.get("media_status"),
        "passed_roles": published.get("passedRoles", []),
        "pending_roles": published.get("pendingRoles", []),
        "url": live_url,
        "title": manifest["title"],
        "commit": commit,
        "staged_paths": staged,
        "resumed_checkpoint": resumed_checkpoint,
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
