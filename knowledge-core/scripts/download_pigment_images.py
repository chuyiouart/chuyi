#!/usr/bin/env python3
"""Download and normalize open-license pigment images from Wikimedia Commons."""

from __future__ import annotations

import io
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps


FILES = [
    {
        "commons_file": "Titanium(IV)_oxide.jpg",
        "local_name": "pw6-titanium-white.jpg",
        "ci_codes": ["PW6"],
        "caption_zh": "二氧化钛粉末（材料示意）",
        "caption_en": "Titanium dioxide powder",
        "creator": "Walkerma",
        "license": "Public domain",
    },
    {
        "commons_file": "Zinc_oxide.jpg",
        "local_name": "pw4-zinc-white.jpg",
        "ci_codes": ["PW4"],
        "caption_zh": "氧化锌粉末（材料示意）",
        "caption_en": "Zinc oxide powder",
        "creator": "Walkerma",
        "license": "Public domain",
    },
    {
        "commons_file": "Ultramarinepigment.jpg",
        "local_name": "pb29-ultramarine-synthetic.jpg",
        "ci_codes": ["PB29"],
        "caption_zh": "合成群青颜料粉",
        "caption_en": "Synthetic ultramarine pigment",
        "creator": "Palladian",
        "license": "Public domain",
    },
    {
        "commons_file": "Natural_ultramarine_pigment.jpg",
        "local_name": "pb29-ultramarine-natural.jpg",
        "ci_codes": ["PB29"],
        "caption_zh": "天然群青颜料粉",
        "caption_en": "Natural ultramarine pigment",
        "creator": "Palladian",
        "license": "Public domain",
    },
    {
        "commons_file": "Pigment_Blue_28.jpg",
        "local_name": "pb28-cobalt-blue.jpg",
        "ci_codes": ["PB28"],
        "caption_zh": "PB28 钴蓝颜料粉",
        "caption_en": "Pigment Blue 28 powder",
        "creator": "FK1954",
        "license": "Public domain",
    },
    {
        "commons_file": "PB35_Bleu_Céruléum.JPG",
        "local_name": "pb35-cerulean-blue.jpg",
        "ci_codes": ["PB35"],
        "caption_zh": "PB35 天蓝颜料粉",
        "caption_en": "Pigment Blue 35 cerulean powder",
        "creator": "Stephhzz",
        "license": "CC BY-SA 3.0",
    },
    {
        "commons_file": "Pigment_Berliner_Blau.JPG",
        "local_name": "pb27-prussian-blue.jpg",
        "ci_codes": ["PB27"],
        "caption_zh": "普鲁士蓝颜料粉",
        "caption_en": "Prussian blue pigment",
        "creator": "Saalebaer",
        "license": "CC0 1.0",
    },
    {
        "commons_file": "Cadmiumgelb-_Pigment.JPG",
        "local_name": "py35-py37-cadmium-yellow.jpg",
        "ci_codes": ["PY35", "PY37"],
        "caption_zh": "镉黄颜料粉",
        "caption_en": "Cadmium sulfide yellow pigment",
        "creator": "Marco Almbauer",
        "license": "Public domain",
    },
    {
        "commons_file": "Kadmiumrot.JPG",
        "local_name": "pr108-cadmium-red.jpg",
        "ci_codes": ["PR108"],
        "caption_zh": "镉红颜料粉",
        "caption_en": "Cadmium red pigment",
        "creator": "Marco Almbauer",
        "license": "Public domain",
    },
    {
        "commons_file": "Iron_oxide_red_b.jpg",
        "local_name": "pr101-iron-oxide-red.jpg",
        "ci_codes": ["PR101"],
        "caption_zh": "偏蓝相氧化铁红颜料粉",
        "caption_en": "Bluish iron oxide red pigment",
        "creator": "FK1954",
        "license": "Public domain",
    },
    {
        "commons_file": "Fragment_of_ochre_pigment,_ocher_-_Museo_Egizio_(Turin)_P_6162_p01.jpg",
        "local_name": "py42-py43-ochre-fragment.jpg",
        "ci_codes": ["PY42", "PY43"],
        "caption_zh": "古埃及赭石颜料块",
        "caption_en": "Ancient Egyptian ochre pigment fragment",
        "creator": "Museo Egizio",
        "license": "CC0 1.0",
    },
    {
        "commons_file": "Chromium(III)-oxide_pigment.jpg",
        "local_name": "pg17-chromium-oxide-green.jpg",
        "ci_codes": ["PG17"],
        "caption_zh": "三氧化二铬绿色颜料粉",
        "caption_en": "Chromium(III) oxide green pigment",
        "creator": "FK1954",
        "license": "Public domain",
    },
    {
        "commons_file": "Links_gebrannte_Siena,_rechts_natürliche.JPG",
        "local_name": "pbr7-sienna-raw-burnt.jpg",
        "ci_codes": ["PBr7"],
        "caption_zh": "熟赭（左）与生赭（右）颜料粉",
        "caption_en": "Burnt sienna (left) and raw sienna (right)",
        "creator": "Marco Almbauer",
        "license": "CC0 1.0",
    },
]


def api_image_url(filename: str) -> str:
    query = urllib.parse.urlencode(
        {
            "action": "query",
            "format": "json",
            "prop": "imageinfo",
            "iiprop": "url|mime|size",
            "titles": f"File:{filename}",
        }
    )
    request = urllib.request.Request(
        f"https://commons.wikimedia.org/w/api.php?{query}",
        headers={"User-Agent": "OUART-Knowledge-Index/1.0 (+https://chuyiouart.com/)"},
    )
    payload = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                payload = json.load(response)
            break
        except Exception:
            if attempt == 3:
                raise
            time.sleep(1.5 * (attempt + 1))
    assert payload is not None
    page = next(iter(payload["query"]["pages"].values()))
    return page["imageinfo"][0]["url"]


def download_bytes(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "OUART-Knowledge-Index/1.0 (+https://chuyiouart.com/)"},
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read()
        except Exception:
            if attempt == 3:
                raise
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError("unreachable")


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    image_dir = root / "assets" / "pigments"
    manifest_path = root / "knowledge-core" / "data" / "pigment-image-manifest.json"
    image_dir.mkdir(parents=True, exist_ok=True)
    manifest = []

    for item in FILES:
        original_url = api_image_url(item["commons_file"])
        content = download_bytes(original_url)
        with Image.open(io.BytesIO(content)) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            image.thumbnail((1400, 1000), Image.Resampling.LANCZOS)
            target = image_dir / item["local_name"]
            image.save(target, "JPEG", quality=86, optimize=True, progressive=True)
        commons_page = "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(item["commons_file"], safe="()_,:-")
        manifest.append(
            {
                **item,
                "local_path": f"assets/pigments/{item['local_name']}",
                "source_page": commons_page,
                "original_url": original_url,
                "modified": "Resized and converted to optimized JPEG; no color correction applied.",
                "retrieved": "2026-07-16",
            }
        )
        print(f"{item['local_name']}: {target.stat().st_size} bytes")

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"manifest: {manifest_path} ({len(manifest)} images)")


if __name__ == "__main__":
    main()
