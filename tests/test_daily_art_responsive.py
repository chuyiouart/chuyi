from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/validate_daily_art_images.py"
GENERATOR = ROOT / "tools/generate-responsive-images.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("daily_validator", VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DailyArtResponsiveTests(unittest.TestCase):
    def test_future_gate_requires_picture_and_sha_bound_vision_receipt(self):
        validator = load_validator()
        self.assertEqual(validator.EFFECTIVE_DATE, "2026-08-12")
        self.assertTrue(hasattr(validator, "validate_responsive_delivery"))
        with TemporaryDirectory() as directory:
            Path(directory, "index.html").write_text('<a class="daily-card" href="x"></a>')
            Path(directory, "daily-art.html").write_text('<a class="daily-card" href="x"></a>')
            with self.assertRaisesRegex(ValueError, "picture"):
                validator.validate_responsive_delivery(Path(directory), "2026-08-12")

    def test_generator_uses_shared_chain_and_fixed_widths(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "assets/daily/2026-08-12-test.jpg"
            source.parent.mkdir(parents=True)
            Image.new("RGB", (1600, 1200), (0, 0, 128)).save(source, quality=95)
            cp = subprocess.run(
                [sys.executable, str(GENERATOR), "--root", str(root), "--file", source.relative_to(root).as_posix(), "--date", "2026-08-12"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(cp.returncode, 0, cp.stderr)
            manifest_path = source.with_name(source.stem + "-responsive.json")
            manifest = json.loads(manifest_path.read_text())
            self.assertEqual([row["width"] for row in manifest["derivatives"]], [480, 768, 1280])
            self.assertEqual(manifest["original_sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
            self.assertTrue(source.is_file())
            self.assertTrue(manifest["qa_receipt_path"].endswith("-responsive-vision.json"))

    def test_pre_effective_date_keeps_legacy_behavior(self):
        validator = load_validator()
        self.assertFalse(validator.responsive_required("2026-08-11"))
        self.assertTrue(validator.responsive_required("2026-08-12"))

    def test_non_first_future_card_must_be_lazy(self):
        validator = load_validator()
        with TemporaryDirectory() as directory:
            page = Path(directory) / "listing.html"
            picture = '<picture><source type="image/webp" srcset="x.webp 480w" sizes="100vw"><img src="x.jpg" loading="eager" fetchpriority="high"></picture>'
            page.write_text(
                f'<a class="daily-card" href="2026-08-13-a.html">{picture}</a>'
                f'<a class="daily-card" href="2026-08-12-b.html">{picture}</a>'
            )
            with self.assertRaisesRegex(ValueError, "non-first responsive list card"):
                validator.validate_listing_priorities(page)

    def test_complete_future_fixture_passes_and_tampered_receipt_fails(self):
        validator = load_validator()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            assets = root / "assets/daily"
            article = root / "content/daily/2026-08-12-test.html"
            assets.mkdir(parents=True)
            article.parent.mkdir(parents=True)
            original = assets / "2026-08-12-test.jpg"
            Image.effect_noise((1600, 1200), 80).convert("RGB").save(original, quality=95)
            cp = subprocess.run(
                [sys.executable, str(GENERATOR), "--root", str(root), "--file", "assets/daily/2026-08-12-test.jpg", "--date", "2026-08-12"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(0, cp.returncode, cp.stderr)
            manifest = json.loads((assets / "2026-08-12-test-responsive.json").read_text())
            candidates = ", ".join(
                f"{{prefix}}{Path(row['path']).name}?v={row['sha256'][:12]} {row['width']}w"
                for row in manifest["derivatives"]
            )
            fallback = manifest["fallback"]
            def picture(prefix: str) -> str:
                srcset = candidates.format(prefix=prefix)
                return (
                    f'<picture><source type="image/webp" srcset="{srcset}" sizes="100vw" />'
                    f'<img src="{prefix}{Path(fallback["path"]).name}?v={fallback["sha256"][:12]}" '
                    f'srcset="{srcset}" sizes="100vw" alt="test artwork" width="1280" height="960" '
                    'loading="eager" decoding="async" fetchpriority="high" /></picture>'
                )
            card = f'<a class="daily-card" href="./content/daily/{article.name}">{picture("./assets/daily/")}</a>'
            (root / "index.html").write_text(card)
            (root / "daily-art.html").write_text(card)
            article.write_text(f'<figure class="daily-artwork">{picture("../../assets/daily/")}</figure>')
            prompt, output = "Inspect all four SHA-bound assets for mobile readability.", "All four assets are readable and artifact-free."
            receipt = {
                "schema_version": 1, "date": "2026-08-12", "agent_prompt": prompt,
                "agent_prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "agent_output": output, "agent_output_sha256": hashlib.sha256(output.encode()).hexdigest(),
                "results": {},
            }
            for row in manifest["derivatives"]:
                receipt["results"][str(row["width"])] = {"image_sha256": row["sha256"], "ocr_exact_match": "N/A", "vision_mobile_readable": True, "artifacts": False}
            receipt["results"]["fallback"] = {"image_sha256": fallback["sha256"], "ocr_exact_match": "N/A", "vision_mobile_readable": True, "artifacts": False}
            receipt_path = assets / "2026-08-12-test-responsive-vision.json"
            receipt_path.write_text(json.dumps(receipt))
            result = validator.validate_responsive_delivery(root, "2026-08-12")
            self.assertEqual(original, result["original"])
            receipt["agent_prompt_sha256"] = "0" * 64
            receipt_path.write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError, "prompt/output SHA-256 mismatch"):
                validator.validate_responsive_delivery(root, "2026-08-12")


if __name__ == "__main__":
    unittest.main()
