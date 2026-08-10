#!/usr/bin/env python3
"""Create WebP derivatives for the public static sites without replacing originals."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageOps


def prepare(source: Path) -> Image.Image:
    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened)
        if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
            return image.convert("RGBA")
        return image.convert("RGB")


def write_variant(source: Path, destination: Path, width: int, quality: int, force: bool) -> tuple[int, int]:
    if not source.is_file():
        raise FileNotFoundError(source)
    if not force and destination.is_file() and destination.stat().st_mtime_ns >= source.stat().st_mtime_ns:
        return source.stat().st_size, destination.stat().st_size

    image = prepare(source)
    if image.width > width:
        height = max(1, round(image.height * width / image.width))
        image = image.resize((width, height), Image.Resampling.LANCZOS)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, "WEBP", quality=quality, method=6)
    return source.stat().st_size, destination.stat().st_size


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--file", action="append", dest="files", required=True, help="relative source path; repeatable")
    parser.add_argument("--width", action="append", type=int, dest="widths", default=[480, 960, 1600])
    parser.add_argument("--quality", type=int, default=78)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    # Keep the workspace-facing path intact. Some checked-out site folders are
    # junctions to another drive; resolving them would bypass the writable root.
    root = args.root.absolute()
    total_source = 0
    total_output = 0
    count = 0
    for relative in args.files:
        source = root / relative
        if source.absolute().relative_to(root) is None:
            raise SystemExit(f"source escapes root: {relative}")
        for width in args.widths:
            destination = source.with_name(f"{source.stem}-{width}.webp")
            source_bytes, output_bytes = write_variant(source, destination, width, args.quality, args.force)
            total_source += source_bytes
            total_output += output_bytes
            count += 1

    reduction = 100 * (1 - total_output / total_source) if total_source else 0
    print(f"Generated/verified {count} WebP files: {total_source / 1024 / 1024:.2f} MB -> {total_output / 1024 / 1024:.2f} MB ({reduction:.1f}% smaller).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
