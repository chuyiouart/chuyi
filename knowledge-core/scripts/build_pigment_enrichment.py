#!/usr/bin/env python3
"""Build a file://-compatible JS bundle for pigment enrichment and image credits."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    enrichment_path = root / "knowledge-core" / "data" / "pigment-enrichment.json"
    images_path = root / "knowledge-core" / "data" / "pigment-image-manifest.json"
    target = root / "data" / "pigment-enrichment-data.js"

    enrichment = json.loads(enrichment_path.read_text(encoding="utf-8"))
    images = json.loads(images_path.read_text(encoding="utf-8"))
    payload = {**enrichment, "images": images}
    target.write_text(
        "window.OUART_PIGMENT_ENRICHMENT = "
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )
    print(f"built {target} ({len(enrichment['pigments'])} pigment profiles, {len(images)} images)")


if __name__ == "__main__":
    main()
