#!/usr/bin/env python3
"""Fail closed when the newest Daily Art entry lacks one valid local image."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NoReturn
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
MIN_BYTES = 10_000
MAX_BYTES = 50 * 1024 * 1024
MIN_DIMENSION = 300
MAX_DIMENSION = 20_000


def fail(message: str) -> NoReturn:
    raise ValueError(message)


def local_target(root: Path, page: Path, src: str) -> Path:
    parsed = urlparse(src)
    if parsed.scheme or parsed.netloc or src.startswith("//"):
        fail(f"remote image URL is forbidden: {src}")
    path = (page.parent / parsed.path).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        fail(f"image path escapes repository root: {src}")
    return path


def decode_dimensions(path: Path) -> tuple[int, int, str]:
    ffprobe = shutil.which("ffprobe")
    ffmpeg = shutil.which("ffmpeg")
    if ffprobe and ffmpeg:
        probe = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if probe.returncode != 0:
            fail(f"image dimension probe failed: {path}: {probe.stderr.strip()}")
        try:
            streams = json.loads(probe.stdout).get("streams", [])
            width = int(streams[0]["width"])
            height = int(streams[0]["height"])
        except (ValueError, KeyError, IndexError, TypeError, json.JSONDecodeError):
            fail(f"image dimensions missing from decoder output: {path}")
        decoded = subprocess.run(
            [ffmpeg, "-v", "error", "-xerror", "-i", str(path), "-f", "null", "-"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if decoded.returncode != 0:
            fail(f"full image decode failed: {path}: {decoded.stderr.strip()}")
        return width, height, "ffmpeg/ffprobe"

    try:
        from PIL import Image
    except ImportError:
        fail("image decode unavailable: install Pillow or provide ffmpeg and ffprobe")
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            image.load()
            width, height = image.size
    except Exception as exc:
        fail(f"Pillow image decode failed: {path}: {exc}")
    return int(width), int(height), "Pillow"


def valid_image(path: Path) -> dict[str, object]:
    if not path.is_file():
        fail(f"image file does not exist: {path}")
    data = path.read_bytes()
    suffix = path.suffix.lower()
    if data.startswith(b"\xff\xd8\xff"):
        kind, mime, allowed_suffixes = "jpeg", "image/jpeg", {".jpg", ".jpeg"}
        if not data.endswith(b"\xff\xd9"):
            fail(f"JPEG end-of-image marker is missing: {path}")
    elif data.startswith(bytes.fromhex("89504e470d0a1a0a")):
        kind, mime, allowed_suffixes = "png", "image/png", {".png"}
        if len(data) < 12 or data[-8:-4] != b"IEND":
            fail(f"PNG IEND marker is missing: {path}")
    else:
        fail(f"image has an invalid JPEG/PNG signature: {path}")
    if suffix not in allowed_suffixes:
        fail(f"image suffix does not match MIME/signature ({mime}): {path}")
    size = len(data)
    if size < MIN_BYTES or size > MAX_BYTES:
        fail(f"image size outside allowed range ({size} bytes): {path}")
    width, height, decoder = decode_dimensions(path)
    if not (MIN_DIMENSION <= width <= MAX_DIMENSION and MIN_DIMENSION <= height <= MAX_DIMENSION):
        fail(f"image dimensions outside allowed range ({width}x{height}): {path}")
    return {
        "bytes": size,
        "kind": kind,
        "mime": mime,
        "width": width,
        "height": height,
        "decoder": decoder,
        "sha256": hashlib.sha256(data).hexdigest(),
    }


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

    expected_prefix = f"./assets/daily/{date}-"
    if not index_src.startswith(expected_prefix):
        fail(f"newest card image must use {expected_prefix}*.jpg|png: {index_src}")
    image_path = local_target(root, index, index_src)
    metadata = valid_image(image_path)

    article = local_target(root, index, index_href)
    if not article.is_file():
        fail(f"newest article does not exist: {article}")
    article_match = ARTICLE_IMAGE_RE.search(article.read_text(encoding="utf-8"))
    if not article_match:
        fail(f"cannot find daily artwork image in {article}")
    article_src = article_match.group("src")
    expected_article_prefix = f"../../assets/daily/{date}-"
    if not article_src.startswith(expected_article_prefix):
        fail(f"article image must use {expected_article_prefix}*.jpg|png: {article_src}")
    article_image_path = local_target(root, article, article_src)
    if article_image_path != image_path:
        fail(f"article and cards must resolve to the same local image: {article_image_path} != {image_path}")

    print(
        "DAILY_ART_IMAGE_GATE_PASS "
        f"date={date} article={article.relative_to(root)} image={image_path.relative_to(root)} "
        f"mime={metadata['mime']} bytes={metadata['bytes']} dimensions={metadata['width']}x{metadata['height']} "
        f"decoder={metadata['decoder']} sha256={metadata['sha256']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        print(f"DAILY_ART_IMAGE_GATE_FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
