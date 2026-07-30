#!/usr/bin/env python3
"""Fail closed when the newest Daily Art entry relies on a remote/hotlinked image."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

CARD_RE = re.compile(
    r'<a\s+class="daily-card"\s+href="(?P<href>[^"]+)">\s*'
    r'<img\s+src="(?P<src>[^"]+)"\s+alt="(?P<alt>[^"]*)"',
    re.S,
)
ARTICLE_IMAGE_RE = re.compile(
    r'<figure\s+class="daily-artwork">\s*<img\s+src="(?P<src>[^"]+)"',
    re.S,
)
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def fail(message: str) -> None:
    raise ValueError(message)


def local_target(page: Path, src: str) -> Path:
    parsed = urlparse(src)
    if parsed.scheme or parsed.netloc or src.startswith("//"):
        fail(f"remote image URL is forbidden: {src}")
    path = (page.parent / parsed.path).resolve()
    return path


def valid_image(path: Path) -> tuple[int, str]:
    if not path.is_file():
        fail(f"image file does not exist: {path}")
    data = path.read_bytes()
    if data.startswith(b"\xff\xd8\xff"):
        kind = "jpeg"
    elif data.startswith(b"\x89PNG\r\n\x1a\n"):
        kind = "png"
    else:
        fail(f"image has an invalid JPEG/PNG signature: {path}")
    if len(data) < 10_000:
        fail(f"image is unexpectedly small ({len(data)} bytes): {path}")
    return len(data), kind


def first_card(page: Path) -> tuple[str, str, str]:
    match = CARD_RE.search(page.read_text(encoding="utf-8"))
    if not match:
        fail(f"cannot find first daily card in {page}")
    return match.group("href"), match.group("src"), match.group("alt")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--date", help="expected YYYY-MM-DD; defaults to newest card date")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    index = root / "index.html"
    listing = root / "daily-art.html"

    index_href, index_src, index_alt = first_card(index)
    list_href, list_src, list_alt = first_card(listing)

    if index_href != list_href:
        fail(f"index/list newest article mismatch: {index_href} != {list_href}")
    if index_src != list_src:
        fail(f"index/list newest image mismatch: {index_src} != {list_src}")
    if not index_alt.strip() or not list_alt.strip():
        fail("newest card image alt text must not be empty")

    date_match = DATE_RE.search(index_href)
    if not date_match:
        fail(f"newest article href has no YYYY-MM-DD date: {index_href}")
    date = date_match.group(1)
    if args.date and date != args.date:
        fail(f"newest article date is {date}, expected {args.date}")

    if not index_src.startswith(f"./assets/daily/{date}-"):
        fail(
            "newest card image must use a dated local path under "
            f"./assets/daily/{date}-*: {index_src}"
        )

    image_path = local_target(index, index_src)
    size, kind = valid_image(image_path)

    article = (index.parent / index_href).resolve()
    if not article.is_file():
        fail(f"newest article does not exist: {article}")
    article_match = ARTICLE_IMAGE_RE.search(article.read_text(encoding="utf-8"))
    if not article_match:
        fail(f"cannot find daily artwork image in {article}")
    article_src = article_match.group("src")
    article_image_path = local_target(article, article_src)
    if article_image_path != image_path:
        fail(
            "article and cards must resolve to the same local image: "
            f"{article_image_path} != {image_path}"
        )

    print(
        "DAILY_ART_IMAGE_GATE_PASS "
        f"date={date} article={article.relative_to(root)} "
        f"image={image_path.relative_to(root)} type={kind} bytes={size}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(f"DAILY_ART_IMAGE_GATE_FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
