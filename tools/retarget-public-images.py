#!/usr/bin/env python3
"""Point selected static HTML images at generated WebP variants safely."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import urlsplit


IMG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE | re.DOTALL)
SRC_RE = re.compile(r"(\bsrc\s*=\s*[\"'])([^\"']+)([\"'])", re.IGNORECASE)


def add_attr(tag: str, name: str, value: str) -> str:
    if re.search(rf"\b{name}\s*=", tag, re.IGNORECASE):
        return tag
    closing = " />" if tag.rstrip().endswith("/>") else ">"
    body = tag.rstrip()
    body = body[:-2].rstrip() if body.endswith("/>") else body[:-1].rstrip()
    return body + f' {name}="{value}"' + closing


def retarget_tag(tag: str, page: Path) -> str:
    # Normalize output from an earlier version that inserted attributes after
    # the XHTML slash ("/ loading=...").
    tag = re.sub(r"\s+/\s+(?=[\w:-]+=)", " ", tag)
    match = SRC_RE.search(tag)
    if not match:
        return tag
    raw_src = match.group(2)
    parsed = urlsplit(raw_src)
    if parsed.scheme or raw_src.startswith(("//", "data:", "#")):
        return add_attr(add_attr(tag, "loading", "lazy"), "decoding", "async")
    source_path = (page.parent / parsed.path).resolve()
    if not source_path.is_file() or source_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        return add_attr(add_attr(tag, "loading", "lazy"), "decoding", "async")

    variants = []
    for width in (480, 960, 1600):
        candidate = source_path.with_name(f"{source_path.stem}-{width}.webp")
        if candidate.is_file():
            relative = candidate.relative_to(page.parent.resolve()).as_posix()
            variants.append((width, relative))
    if not variants:
        return add_attr(add_attr(tag, "loading", "lazy"), "decoding", "async")

    original = raw_src
    new_src = variants[-2][1] if len(variants) > 1 else variants[-1][1]
    new_src = new_src + (f"?{parsed.query}" if parsed.query else "")
    tag = tag[: match.start(2)] + new_src + tag[match.end(2) :]
    srcset = ", ".join(f"{path}{('?' + parsed.query) if parsed.query else ''} {width}w" for width, path in variants)
    tag = add_attr(tag, "srcset", srcset)
    sizes = "(max-width: 680px) 100vw, 720px"
    if "/daily/" in raw_src:
        sizes = "(max-width: 680px) 100vw, 280px"
    elif "hero" in raw_src.lower() or "workshop" in raw_src.lower():
        sizes = "(max-width: 680px) 100vw, 52vw"
    tag = add_attr(tag, "sizes", sizes)
    tag = add_attr(tag, "data-image-fallback", original)
    tag = add_attr(tag, "loading", "lazy")
    return add_attr(tag, "decoding", "async")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", action="append", required=True, type=Path)
    args = parser.parse_args()
    for page in args.file:
        text = page.read_text(encoding="utf-8")
        updated = IMG_RE.sub(lambda match: retarget_tag(match.group(0), page), text)
        if updated != text:
            page.write_text(updated, encoding="utf-8", newline="")
            print(f"updated {page}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
