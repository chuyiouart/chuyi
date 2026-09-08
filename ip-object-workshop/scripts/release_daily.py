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
from typing import Callable

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
    require_no_git_operation(repo)
    # This checkout is shared by several lanes. A plain git commit includes
    # the entire index, not just the path used by a previous diff command.
    dirty = git(repo, "status", "--porcelain", "-uall").stdout.splitlines()
    if dirty and not allow_dirty:
        raise RuntimeError(f"workshop tree is not clean before release:\n{dirty}")
    return dirty


def require_no_git_operation(repo: Path) -> None:
    """An interrupted merge/rebase is not an ordinary publication checkpoint."""
    for marker in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply"):
        state = Path(git(repo, "rev-parse", "--git-path", marker).stdout.strip())
        if not state.is_absolute():
            state = repo / state
        if state.exists():
            raise RuntimeError(f"unfinished Git operation; manual review required: {marker}")


def require_clean_git_state(repo: Path) -> None:
    """Never stash, reset, or inherit another writer's operation/index."""
    require_no_git_operation(repo)
    if git(repo, "status", "--porcelain", "-uall").stdout.strip():
        raise RuntimeError("shared checkout is dirty; preserving all files and index")
    if git(repo, "branch", "--show-current").stdout.strip() != "main":
        raise RuntimeError("shared checkout is no longer on main")


def is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    result = git(repo, "merge-base", "--is-ancestor", ancestor, descendant, check=False)
    if result.returncode not in (0, 1):
        raise RuntimeError(f"cannot establish Git ancestry: {result.stderr.strip()}")
    return result.returncode == 0


def preflight_merge_tree(repo: Path, left: str, right: str) -> str:
    """Git >= 2.38 computes the merge without touching HEAD/index/worktree."""
    preview = git(repo, "merge-tree", "--write-tree", left, right, check=False)
    if preview.returncode:
        raise RuntimeError(
            "upstream reconciliation blocked; merge conflict or unsupported merge-tree; "
            "HEAD/index/worktree unchanged, manual review required:\n"
            + preview.stdout.strip() + "\n" + preview.stderr.strip()
        )
    tree = preview.stdout.splitlines()[0].strip() if preview.stdout.strip() else ""
    if not re.fullmatch(r"[0-9a-f]{40,64}", tree):
        raise RuntimeError("merge-tree returned no verifiable tree; refusing merge")
    return tree


def verify_pending_release_commits(repo: Path, upstream: str, allowlist: list[str], day: str) -> None:
    """Only recover this manifest's commits; never auto-push arbitrary user work."""
    allowed = set(allowlist)
    content_subject = f"content: publish workshop update {day}"
    merge_subject = f"sync: reconcile workshop release {day} with origin/main"
    commits = git(repo, "rev-list", f"{upstream}..HEAD").stdout.splitlines()
    for commit in commits:
        subject = git(repo, "show", "-s", "--format=%s", commit).stdout.strip()
        parents = git(repo, "show", "-s", "--format=%P", commit).stdout.split()
        if len(parents) == 2 and subject == merge_subject:
            expected_tree = preflight_merge_tree(repo, parents[0], parents[1])
            actual_tree = git(repo, "rev-parse", f"{commit}^{{tree}}").stdout.strip()
            if expected_tree != actual_tree or not is_ancestor(repo, parents[1], upstream):
                raise RuntimeError(f"unrecognized pending reconciliation commit: {commit}")
            continue
        if len(parents) != 1 or subject != content_subject:
            raise RuntimeError(f"unrecognized unpublished commit {commit}: {subject}; preserving it for review")
        paths = git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", commit).stdout.splitlines()
        if not paths or any(path not in allowed for path in paths):
            raise RuntimeError(f"unpublished commit exceeds current release allowlist: {commit}: {paths}")


def reconcile_upstream(repo: Path, allowlist: list[str], day: str) -> dict:
    """Run under the existing ouart-content-publish.lock held by the wrapper.

    Preserve both histories: fast-forward when possible, otherwise perform only
    a previewed, conflict-free merge of recognized current-day release commits.
    No force-push, rebase, stash, reset, or automatic conflict resolution.
    """
    require_clean_git_state(repo)
    git_with_retry(repo, "fetch", "--no-tags", "origin", "main")
    upstream = git(repo, "rev-parse", "FETCH_HEAD").stdout.strip()
    before = git(repo, "rev-parse", "HEAD").stdout.strip()
    verify_pending_release_commits(repo, upstream, allowlist, day)
    if is_ancestor(repo, upstream, before):
        return {"action": "already_integrated", "upstream": upstream, "head": before}
    if is_ancestor(repo, before, upstream):
        git(repo, "merge", "--ff-only", "--no-autostash", upstream)
        return {"action": "fast_forward", "upstream": upstream, "head": upstream}
    expected_tree = preflight_merge_tree(repo, before, upstream)
    # Hooks or an uncoordinated writer must not silently change the preflight.
    require_clean_git_state(repo)
    if git(repo, "rev-parse", "HEAD").stdout.strip() != before:
        raise RuntimeError("HEAD changed during reconciliation; refusing merge")
    merged = git(
        repo, "merge", "--no-ff", "--no-edit", "--no-autostash", "-m",
        f"sync: reconcile workshop release {day} with origin/main", upstream, check=False,
    )
    if merged.returncode:
        # Do not abort someone else's subsequent edits. Leave exact evidence.
        raise RuntimeError(f"preflighted merge failed; manual review required: {merged.stdout}\n{merged.stderr}")
    if git(repo, "rev-parse", "HEAD^{tree}").stdout.strip() != expected_tree:
        raise RuntimeError("merged tree differs from preflight; refusing push")
    require_clean_git_state(repo)
    return {"action": "verified_merge", "upstream": upstream, "head": git(repo, "rev-parse", "HEAD").stdout.strip()}


def push_release_with_reconciliation(
    repo: Path, allowlist: list[str], day: str, validate: Callable[[], object], attempts: int = 3,
) -> dict:
    """Retry a bounded push race even when this invocation created no commit."""
    if attempts < 1:
        raise ValueError("attempts must be positive")
    actions = []
    for attempt in range(attempts):
        sync = reconcile_upstream(repo, allowlist, day)
        actions.append(sync)
        validate()
        require_clean_git_state(repo)
        if sync["upstream"] == git(repo, "rev-parse", "HEAD").stdout.strip():
            return {"pushed": False, "already_remote": True, "attempts": attempt + 1, "sync": actions}
        pushed = git(repo, "push", "--porcelain", "origin", "HEAD:refs/heads/main", check=False)
        if pushed.returncode == 0:
            return {"pushed": True, "already_remote": False, "attempts": attempt + 1, "sync": actions}
        diagnostic = f"{pushed.stdout}\n{pushed.stderr}".lower()
        race = "[rejected]" in diagnostic and any(word in diagnostic for word in ("fetch first", "non-fast-forward"))
        transient = any(word in diagnostic for word in TRANSIENT_GIT_ERRORS)
        if not (race or transient) or attempt == attempts - 1:
            raise RuntimeError(f"release push failed after {attempt + 1} attempt(s); local commit preserved:\n{pushed.stdout}\n{pushed.stderr}")
        if transient:
            time.sleep((5, 15)[min(attempt, 1)])
    raise RuntimeError("release push retry exhausted")


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


def build_release_allowlist(repo: Path, manifest: dict, published: dict, *, require_existing: bool = True) -> list[str]:
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
    assets = published.get("webImageAssets") or manifest.get("webImageAssets") or []
    for asset in assets:
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
    if not assets:
        qa = manifest.get("webImageQA") if isinstance(manifest.get("webImageQA"), dict) else {}
        for role in manifest.get("imageRoles") or []:
            role_name = str(role.get("role") or "")
            filename = str(role.get("filename") or "")
            receipts = qa.get(role_name) if isinstance(qa.get(role_name), dict) else {}
            stem = Path(filename).stem
            if not role_name or not stem or not receipts:
                continue
            for key in receipts:
                if key == "fallback":
                    paths.append(asset_root / f"{stem}-fallback.png")
                elif str(key).isdigit():
                    paths.append(asset_root / f"{stem}-{key}.webp")
    result: list[str] = []
    for path in paths:
        try:
            relative = path.relative_to(repo).as_posix()
        except ValueError as exc:
            raise RuntimeError(f"release path escapes repository: {path}") from exc
        if require_existing and not path.is_file():
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
    checkpoint_allowlist = build_release_allowlist(repo, manifest, checkpoint_published, require_existing=False)
    if dirty:
        classify_checkpoint_dirty_paths(dirty, checkpoint_allowlist)
        resumed_checkpoint = True
    else:
        reconcile_upstream(repo, checkpoint_allowlist, str(manifest["date"]))
        resumed_checkpoint = False

    publisher = workshop / "scripts" / "workshop_publish.py"
    result = run(
        [sys.executable, str(publisher), "publish", "--root", str(workshop), "--manifest", str(manifest_path)],
        cwd=repo,
    )
    published = json.loads(result.stdout)
    run([sys.executable, str(publisher), "validate", "--root", str(workshop)], cwd=repo)

    allowlist = build_release_allowlist(repo, manifest, published)
    git(repo, "add", "--", *allowlist)
    staged = git(repo, "diff", "--cached", "--name-only").stdout.splitlines()
    unexpected = [path for path in staged if path not in set(allowlist)]
    if unexpected:
        raise RuntimeError(f"unexpected staged paths: {unexpected}")

    if staged:
        git(repo, "commit", "-m", f"content: publish workshop update {manifest['date']}")
    git_delivery = push_release_with_reconciliation(
        repo, allowlist, str(manifest["date"]),
        validate=lambda: run([sys.executable, str(publisher), "validate", "--root", str(workshop)], cwd=repo),
    )
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
        "git_delivery": git_delivery,
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
