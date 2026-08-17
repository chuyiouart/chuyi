#!/usr/bin/env python3
"""Fail-closed eligibility and public-text validator for the canonical Chuyi site.

This module is intentionally rendering-agnostic: callers must validate release
metadata before staging/rendering, and the repository pre-push hook validates the
complete public tree before any production push.
"""
from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PUBLIC_SUFFIXES = {".html", ".htm", ".js", ".json", ".xml", ".txt", ".css", ".webmanifest"}
IGNORED_PARTS = {".git", ".github", ".githooks", "tests", "scripts", "__pycache__", "node_modules"}
FORBIDDEN_PUBLIC_LITERALS = (
    "ouart-exact-one-canary",
    "ouart_exact_one_canary",
    "internal_fixture_only",
    "daily six未完成",
    "exact-one canary",
    "exact_one_canary",
    "canary-releases/",
    '"run_kind":"public_test"',
    '"run_kind": "public_test"',
    "run_kind=public_test",
    'data-run-kind="public_test"',
    'data-daily-six-complete="false"',
    '"daily_six_complete":false',
    '"daily_six_complete": false',
)
TARGET_COUNT_RE = re.compile(r"data-target-count\s*=\s*(['\"])(?!6\1)([^'\"]+)\1", re.IGNORECASE)
JSON_TARGET_COUNT_RE = re.compile(r'"target_count"\s*:\s*(\d+)', re.IGNORECASE)


def _same_path(left: Path, right: Path) -> bool:
    return left.expanduser().resolve() == right.expanduser().resolve()


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def validate_release_metadata(
    metadata: dict[str, Any],
    *,
    publication_root: Path,
    production_root: Path,
    now: datetime | None = None,
) -> list[str]:
    """Validate eligibility before rendering or staging any public bytes."""
    errors: list[str] = []
    run_kind = str(metadata.get("run_kind") or "").strip().lower()
    content_kind = str(metadata.get("content_kind") or "").strip().lower()
    internal_fixture = metadata.get("internal_fixture_only") is True
    telegram_enabled = metadata.get("telegram_enabled") is True
    inject_home = metadata.get("inject_main_homepage") is True
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)

    if internal_fixture:
        errors.append("internal_fixture_only is never eligible for website publication")
        if run_kind == "public_test":
            errors.append("internal_fixture_only is never eligible for public_test")
        if telegram_enabled:
            errors.append("internal_fixture_only is never eligible for telegram")

    if run_kind == "public_test":
        if _same_path(publication_root, production_root):
            errors.append("public_test requires a separate non-production publication root")
        if metadata.get("authorized_test_root") is not True:
            errors.append("public_test requires an explicitly authorized test root")
        fresh_until = _parse_time(metadata.get("fresh_until"))
        if fresh_until is None:
            errors.append("public_test requires a timezone-aware fresh_until")
        elif fresh_until <= current:
            errors.append("public_test freshness expired")
        if inject_home:
            errors.append("public_test must never inject the production main homepage")
    elif run_kind != "production":
        errors.append(f"unsupported run_kind: {run_kind or '[missing]'}")

    if content_kind == "daily_six" and _same_path(publication_root, production_root):
        if metadata.get("target_count") != 6:
            errors.append("production Daily Six requires target_count=6")
        if metadata.get("daily_six_complete") is not True:
            errors.append("production Daily Six requires daily_six_complete=true")

    return errors


def scan_public_text(relative: Path, text: str) -> list[str]:
    errors: list[str] = []
    lowered = text.lower()
    for literal in FORBIDDEN_PUBLIC_LITERALS:
        if literal in lowered:
            errors.append(f"{relative.as_posix()}: forbidden public marker {literal!r}")
    for match in TARGET_COUNT_RE.finditer(text):
        errors.append(f"{relative.as_posix()}: non-six public data-target-count={match.group(2)!r}")
    if "daily_six" in lowered or "daily-six" in lowered or "daily six" in lowered:
        for match in JSON_TARGET_COUNT_RE.finditer(text):
            if int(match.group(1)) != 6:
                errors.append(f"{relative.as_posix()}: non-six Daily Six target_count={match.group(1)}")
    return errors


def public_text_files(root: Path):
    root = root.resolve()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if IGNORED_PARTS.intersection(relative.parts):
            continue
        if path.suffix.lower() in PUBLIC_SUFFIXES:
            yield path, relative


def validate_public_tree(root: Path | str) -> list[str]:
    root_path = Path(root).resolve()
    errors: list[str] = []
    for path, relative in public_text_files(root_path):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"{relative.as_posix()}: public text is not valid UTF-8")
            continue
        errors.extend(scan_public_text(relative, text))
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Chuyi production public-content policy")
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    errors = validate_public_tree(args.root)
    if errors:
        print("PUBLIC_CONTENT_POLICY_BLOCKED")
        print("\n".join(errors))
        return 1
    print("PUBLIC_CONTENT_POLICY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
