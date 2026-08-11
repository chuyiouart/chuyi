#!/usr/bin/env python3
"""Fail-closed Daily Art local/original and responsive-delivery publication gate."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import date as iso_date
from pathlib import Path
from typing import NoReturn
from urllib.parse import urlparse

EFFECTIVE_DATE = "2026-08-12"
CARD_RE = re.compile(r'<a\b(?P<attrs>[^>]*\bclass="[^"]*\bdaily-card\b[^"]*"[^>]*)>(?P<body>.*?)</a>', re.S | re.I)
FIGURE_RE = re.compile(r'<figure\b[^>]*\bclass="[^"]*\bdaily-artwork\b[^"]*"[^>]*>(?P<body>.*?)</figure>', re.S | re.I)
PICTURE_RE = re.compile(r"<picture\b[^>]*>(?P<body>.*?)</picture>", re.S | re.I)
IMG_RE = re.compile(r"<img\b(?P<attrs>[^>]*)/?>", re.S | re.I)
SOURCE_RE = re.compile(r"<source\b(?P<attrs>[^>]*)/?>", re.S | re.I)
ATTR_RE = re.compile(r"([:\w-]+)\s*=\s*([\"'])(.*?)\2", re.S)
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
MIN_BYTES = 10_000
MAX_BYTES = 50 * 1024 * 1024
MIN_DIMENSION = 300
MAX_DIMENSION = 20_000
EXPECTED_WIDTHS = [480, 768, 1280]


def fail(message: str) -> NoReturn:
    raise ValueError(message)


def responsive_required(day: str) -> bool:
    return iso_date.fromisoformat(day) >= iso_date.fromisoformat(EFFECTIVE_DATE)


def attrs(text: str) -> dict[str, str]:
    return {match.group(1).lower(): match.group(3) for match in ATTR_RE.finditer(text)}


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
    ffprobe, ffmpeg = shutil.which("ffprobe"), shutil.which("ffmpeg")
    if ffprobe and ffmpeg:
        probe = subprocess.run([ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", str(path)], capture_output=True, text=True, timeout=30, check=False)
        if probe.returncode != 0:
            fail(f"image dimension probe failed: {path}: {probe.stderr.strip()}")
        try:
            stream = json.loads(probe.stdout)["streams"][0]
            width, height = int(stream["width"]), int(stream["height"])
        except (ValueError, KeyError, IndexError, TypeError, json.JSONDecodeError):
            fail(f"image dimensions missing from decoder output: {path}")
        decoded = subprocess.run([ffmpeg, "-v", "error", "-xerror", "-i", str(path), "-f", "null", "-"], capture_output=True, text=True, timeout=60, check=False)
        if decoded.returncode != 0:
            fail(f"full image decode failed: {path}: {decoded.stderr.strip()}")
        return width, height, "ffmpeg/ffprobe"
    try:
        from PIL import Image
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            image.load()
            width, height = image.size
    except Exception as exc:
        fail(f"Pillow image decode failed: {path}: {exc}")
    return int(width), int(height), "Pillow"


def valid_image(path: Path, *, allow_webp: bool = False, enforce_archive_limits: bool = True) -> dict[str, object]:
    if not path.is_file() or path.is_symlink():
        fail(f"image file does not exist or is not regular: {path}")
    data, suffix = path.read_bytes(), path.suffix.lower()
    if data.startswith(b"\xff\xd8\xff"):
        kind, mime, allowed = "jpeg", "image/jpeg", {".jpg", ".jpeg"}
        if not data.endswith(b"\xff\xd9"):
            fail(f"JPEG end-of-image marker is missing: {path}")
    elif data.startswith(bytes.fromhex("89504e470d0a1a0a")):
        kind, mime, allowed = "png", "image/png", {".png"}
        if len(data) < 12 or data[-8:-4] != b"IEND":
            fail(f"PNG IEND marker is missing: {path}")
    elif allow_webp and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        kind, mime, allowed = "webp", "image/webp", {".webp"}
    else:
        fail(f"image has an invalid JPEG/PNG/WebP signature: {path}")
    if suffix not in allowed:
        fail(f"image suffix does not match MIME/signature ({mime}): {path}")
    size = len(data)
    if enforce_archive_limits and not MIN_BYTES <= size <= MAX_BYTES:
        fail(f"image size outside allowed range ({size} bytes): {path}")
    width, height, decoder = decode_dimensions(path)
    if enforce_archive_limits and not (MIN_DIMENSION <= width <= MAX_DIMENSION and MIN_DIMENSION <= height <= MAX_DIMENSION):
        fail(f"image dimensions outside allowed range ({width}x{height}): {path}")
    return {"bytes": size, "kind": kind, "mime": mime, "width": width, "height": height, "decoder": decoder, "sha256": hashlib.sha256(data).hexdigest()}


def first_card(page: Path) -> tuple[str, str, str]:
    match = CARD_RE.search(page.read_text(encoding="utf-8"))
    if not match:
        fail(f"cannot find first daily card in {page}")
    anchor, body = attrs(match.group("attrs")), match.group("body")
    image = IMG_RE.search(body)
    if not image:
        fail(f"cannot find first daily card image in {page}")
    image_attrs = attrs(image.group("attrs"))
    return anchor.get("href", ""), image_attrs.get("src", ""), image_attrs.get("alt", "")


def picture_data(page: Path, *, article: bool) -> dict[str, object]:
    text = page.read_text(encoding="utf-8")
    container = FIGURE_RE.search(text) if article else CARD_RE.search(text)
    if not container:
        fail(f"cannot find {'daily artwork' if article else 'first daily card'} in {page}")
    body = container.group("body")
    picture = PICTURE_RE.search(body)
    if not picture:
        fail(f"responsive picture missing in {page}")
    image_match, source_match = IMG_RE.search(picture.group("body")), SOURCE_RE.search(picture.group("body"))
    if not image_match or not source_match:
        fail(f"picture img/source missing in {page}")
    image, source = attrs(image_match.group("attrs")), attrs(source_match.group("attrs"))
    if source.get("type") != "image/webp" or not source.get("srcset") or not source.get("sizes"):
        fail(f"picture WebP srcset/sizes invalid in {page}")
    if not image.get("src") or not image.get("srcset") or not image.get("sizes") or not image.get("alt", "").strip():
        fail(f"picture fallback/srcset/sizes/alt invalid in {page}")
    if article:
        if image.get("loading") != "eager" or image.get("fetchpriority") != "high":
            fail(f"article hero must be eager/high priority: {page}")
    return {"img": image, "source": source, "href": attrs(container.groupdict().get("attrs") or "").get("href", "")}


def validate_listing_priorities(page: Path) -> None:
    cards = list(CARD_RE.finditer(page.read_text(encoding="utf-8")))
    for index, card in enumerate(cards):
        href = attrs(card.group("attrs")).get("href", "")
        match = DATE_RE.search(href)
        if not match or not responsive_required(match.group(1)):
            continue
        picture = PICTURE_RE.search(card.group("body"))
        image = IMG_RE.search(picture.group("body")) if picture else None
        if not image:
            fail(f"responsive card picture missing in {page}: {href}")
        image_attrs = attrs(image.group("attrs"))
        if index > 0 and (image_attrs.get("loading") != "lazy" or image_attrs.get("fetchpriority") == "high"):
            fail(f"non-first responsive list card must be lazy and not high priority in {page}: {href}")


def srcset_rows(value: str) -> list[tuple[str, int]]:
    rows = []
    for item in value.split(","):
        parts = item.strip().rsplit(" ", 1)
        if len(parts) != 2 or not parts[1].endswith("w"):
            fail(f"invalid srcset candidate: {item}")
        rows.append((parts[0], int(parts[1][:-1])))
    return rows


def _load_manifest(root: Path, fallback: Path, day: str) -> tuple[Path, dict]:
    stem = re.sub(r"-fallback$", "", fallback.stem)
    path = fallback.with_name(f"{stem}-responsive.json")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"responsive manifest missing/invalid: {path}: {exc}")
    if manifest.get("effective_date") != EFFECTIVE_DATE or not str(Path(manifest.get("original_path", "")).name).startswith(f"{day}-"):
        fail("responsive manifest effective date/original identity invalid")
    return path, manifest


def _manifest_asset(root: Path, row: dict) -> tuple[Path, dict[str, object]]:
    path = (root / str(row.get("path", ""))).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        fail(f"manifest asset escapes root: {path}")
    metadata = valid_image(path, allow_webp=True, enforce_archive_limits=False)
    if metadata["sha256"] != row.get("sha256") or metadata["bytes"] != row.get("bytes") or metadata["width"] != row.get("width") or metadata["height"] != row.get("height"):
        fail(f"manifest asset identity mismatch: {path}")
    return path, metadata


def validate_responsive_delivery(root: Path, day: str) -> dict[str, object]:
    root = root.resolve()
    index, listing = root / "index.html", root / "daily-art.html"
    index_data, list_data = picture_data(index, article=False), picture_data(listing, article=False)
    validate_listing_priorities(index)
    validate_listing_priorities(listing)
    if index_data["href"] != list_data["href"]:
        fail("index/list newest responsive article mismatch")
    article = local_target(root, index, str(index_data["href"]))
    article_data = picture_data(article, article=True)
    fallbacks = [local_target(root, page, str(data["img"]["src"])) for page, data in ((index, index_data), (listing, list_data), (article, article_data))]
    if len(set(fallbacks)) != 1:
        fail("three page picture fallbacks do not resolve to one file")
    fallback = fallbacks[0]
    manifest_path, manifest = _load_manifest(root, fallback, day)
    original = (root / str(manifest.get("original_path", ""))).resolve()
    original_meta = valid_image(original)
    if original_meta["sha256"] != manifest.get("original_sha256") or manifest.get("source_preserved") is not True:
        fail("original museum image was not preserved by SHA-256")
    derivatives = manifest.get("derivatives")
    original_width = original_meta.get("width")
    if not isinstance(original_width, int) or original_width < 1:
        fail("decoded original width invalid")
    expected_widths = [width for width in EXPECTED_WIDTHS if width <= original_width] or [original_width]
    if not isinstance(derivatives, list) or [row.get("width") for row in derivatives] != expected_widths:
        fail(f"responsive widths must be no-upscale subset: {expected_widths}")
    asset_rows: dict[str, dict] = {}
    expected_urls: dict[int, Path] = {}
    for row in derivatives:
        path, _ = _manifest_asset(root, row)
        if row.get("format") != "webp" or int(row.get("bytes", 2**63)) > int(row.get("budget_bytes", -1)):
            fail(f"WebP derivative format/budget invalid: {path}")
        asset_rows[str(row["width"])] = row
        expected_urls[int(row["width"])] = path
    fallback_path, _ = _manifest_asset(root, manifest.get("fallback", {}))
    if fallback_path != fallback or manifest["fallback"].get("format") not in {"jpeg", "png"} or int(manifest["fallback"].get("bytes", 2**63)) > 1024 * 1024:
        fail("limited original-format fallback invalid")
    asset_rows["fallback"] = manifest["fallback"]
    for page, data in ((index, index_data), (listing, list_data), (article, article_data)):
        source_rows = srcset_rows(str(data["source"]["srcset"]))
        image_rows = srcset_rows(str(data["img"]["srcset"]))
        if [width for _, width in source_rows] != expected_widths or source_rows != image_rows:
            fail(f"responsive source/img srcset invalid in {page}")
        for url, width in source_rows:
            if local_target(root, page, url) != expected_urls[width]:
                fail(f"srcset identity mismatch in {page}: {url}")
    receipt_path = (root / str(manifest.get("qa_receipt_path", ""))).resolve()
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"SHA-bound Vision receipt missing/invalid: {receipt_path}: {exc}")
    prompt = receipt.get("agent_prompt")
    output = receipt.get("agent_output")
    if receipt.get("schema_version") != 1 or receipt.get("date") != day or not isinstance(prompt, str) or not prompt.strip() or not isinstance(output, str) or not output.strip():
        fail("Vision receipt agent prompt/output identity missing")
    if hashlib.sha256(prompt.encode()).hexdigest() != receipt.get("agent_prompt_sha256") or hashlib.sha256(output.encode()).hexdigest() != receipt.get("agent_output_sha256"):
        fail("Vision receipt prompt/output SHA-256 mismatch")
    results = receipt.get("results")
    if not isinstance(results, dict):
        fail("Vision receipt results missing")
    for key, row in asset_rows.items():
        qa = results.get(key)
        if not isinstance(qa, dict) or qa.get("image_sha256") != row.get("sha256") or qa.get("vision_mobile_readable") is not True or qa.get("artifacts") is not False or qa.get("ocr_exact_match") != "N/A":
            fail(f"Vision receipt fail closed for asset {key}")
    return {"manifest": manifest_path, "receipt": receipt_path, "original": original, "fallback": fallback, "sha256": original_meta["sha256"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--date", help="expected YYYY-MM-DD; defaults to newest card date")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    index, listing = root / "index.html", root / "daily-art.html"
    index_href, index_src, index_alt = first_card(index)
    list_href, list_src, list_alt = first_card(listing)
    if index_href != list_href or index_src != list_src:
        fail("index/list newest article or image mismatch")
    if not index_alt.strip() or not list_alt.strip():
        fail("newest card image alt text must not be empty")
    match = DATE_RE.search(index_href)
    if not match:
        fail(f"newest article href has no YYYY-MM-DD date: {index_href}")
    day = match.group(1)
    if args.date and day != args.date:
        fail(f"newest article date is {day}, expected {args.date}")
    if responsive_required(day):
        result = validate_responsive_delivery(root, day)
        print(f"DAILY_ART_IMAGE_GATE_PASS date={day} responsive=true manifest={result['manifest'].relative_to(root)} receipt={result['receipt'].relative_to(root)} original={result['original'].relative_to(root)} original_sha256={result['sha256']}")
        return 0
    expected_prefix = f"./assets/daily/{day}-"
    if not index_src.startswith(expected_prefix):
        fail(f"newest card image must use {expected_prefix}*.jpg|png: {index_src}")
    image_path = local_target(root, index, index_src)
    metadata = valid_image(image_path)
    article = local_target(root, index, index_href)
    figure = FIGURE_RE.search(article.read_text(encoding="utf-8"))
    image = IMG_RE.search(figure.group("body")) if figure else None
    if not image:
        fail(f"cannot find daily artwork image in {article}")
    article_src = attrs(image.group("attrs")).get("src", "")
    if local_target(root, article, article_src) != image_path:
        fail("article and cards must resolve to the same local image")
    print(f"DAILY_ART_IMAGE_GATE_PASS date={day} responsive=false article={article.relative_to(root)} image={image_path.relative_to(root)} mime={metadata['mime']} bytes={metadata['bytes']} dimensions={metadata['width']}x{metadata['height']} decoder={metadata['decoder']} sha256={metadata['sha256']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        print(f"DAILY_ART_IMAGE_GATE_FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
