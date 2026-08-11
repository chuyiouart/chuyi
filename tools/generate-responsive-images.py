#!/usr/bin/env python3
"""Build the Daily Art responsive website chain while preserving the museum source."""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import date
from pathlib import Path

HERMES_LIB = Path("/root/.hermes/lib")
if str(HERMES_LIB) not in sys.path:
    sys.path.insert(0, str(HERMES_LIB))

from web_image_delivery import (  # noqa: E402
    DEFAULT_WIDTHS,
    EFFECTIVE_DATE,
    build_picture_html,
    derive_responsive_assets,
)
from PIL import Image  # noqa: E402


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def repository_relative(root: Path, value: str) -> str:
    path = Path(value).resolve()
    try:
        return path.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError(f"generated asset escapes root: {path}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--file", action="append", dest="files", required=True, help="repository-relative original JPEG/PNG")
    parser.add_argument("--date", required=True, help="publication date (YYYY-MM-DD)")
    parser.add_argument("--role", choices=("hero", "card"), default="hero")
    parser.add_argument("--original-url")
    parser.add_argument("--force", action="store_true", help="accepted for durable-worker idempotency")
    args = parser.parse_args()

    publication_date = date.fromisoformat(args.date)
    if publication_date < date.fromisoformat(EFFECTIVE_DATE):
        raise SystemExit(f"responsive Daily Art chain is effective {EFFECTIVE_DATE}")
    root = args.root.absolute()
    count = 0
    for relative in args.files:
        source = (root / relative).absolute()
        try:
            source.relative_to(root)
        except ValueError as exc:
            raise SystemExit(f"source escapes root: {relative}") from exc
        if not source.name.startswith(f"{args.date}-"):
            raise SystemExit(f"source filename must start with {args.date}-: {relative}")
        if source.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            raise SystemExit(f"Daily Art original must be JPEG or PNG: {relative}")
        with Image.open(source) as opened:
            opened.verify()

        manifest = derive_responsive_assets(
            source,
            source.parent,
            source.stem,
            widths=DEFAULT_WIDTHS,
            page_role=args.role,
            original_url=args.original_url,
            require_text_qa=False,
        )
        # Manifests are committed and must remain portable across checkout paths.
        manifest["original_path"] = repository_relative(root, manifest["original_path"])
        for row in [*manifest["derivatives"], manifest["fallback"]]:
            row["path"] = repository_relative(root, row["path"])
        receipt = source.with_name(f"{source.stem}-responsive-vision.json")
        manifest["qa_policy"] = {
            "ocr_exact_match": "N/A",
            "ocr_reason": "official_collection_image_has_no_GPT_generated_text",
            "vision_mobile_readable_required": True,
            "artifacts_must_be_false": True,
            "receipt_must_bind_prompt_and_every_asset_sha256": True,
        }
        manifest["qa_receipt_path"] = receipt.relative_to(root).as_posix()
        manifest_path = source.with_name(f"{source.stem}-responsive.json")
        atomic_json(manifest_path, manifest)

        # Worker-ready snippets; receipt validation still happens in the publication gate.
        runtime_manifest = dict(manifest)
        runtime_manifest["original_path"] = str(root / manifest["original_path"])
        runtime_manifest["derivatives"] = [dict(row, path=str(root / row["path"])) for row in manifest["derivatives"]]
        runtime_manifest["fallback"] = dict(manifest["fallback"], path=str(root / manifest["fallback"]["path"]))
        print(json.dumps({
            "manifest": manifest_path.relative_to(root).as_posix(),
            "vision_receipt": receipt.relative_to(root).as_posix(),
            "widths": [row["width"] for row in manifest["derivatives"]],
            "article_picture_template": build_picture_html(runtime_manifest, alt="REPLACE_WITH_ARTWORK_ALT", lcp=True, relative_prefix="../../assets/daily/"),
            "card_picture_template": build_picture_html(runtime_manifest, alt="REPLACE_WITH_ARTWORK_ALT", lcp=True, relative_prefix="./assets/daily/"),
        }, ensure_ascii=False))
        count += 1
    print(f"DAILY_ART_RESPONSIVE_ASSETS_READY count={count} widths=480,768,1280 source_preserved=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
