from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, "/root/.hermes/lib")
from workshop_publish import publish_manifest, render_article  # noqa: E402
from web_image_delivery import derive_responsive_assets  # noqa: E402


class TextFirstPartialMediaPublisherTests(unittest.TestCase):
    DATE = "2099-01-02"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ip-text-first-site-"))
        for directory in ("assets", "updates"):
            (self.tmp / directory).mkdir()
        (self.tmp / "course.css").write_text("body{}", encoding="utf-8")
        (self.tmp / "update-article.css").write_text("body{}", encoding="utf-8")
        calendar = [{"date": self.DATE, "status": "planned", "published": False, "url": ""}]
        (self.tmp / "course-calendar.json").write_text(json.dumps(calendar), encoding="utf-8")
        self.source = self.tmp / "03-real-application.png"
        Image.new("RGB", (1400, 900), (50, 100, 180)).save(self.source)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def manifest(self):
        headings = ("具体问题", "核心判断", "步骤或标准", "常见错误", "与五天课程的关系", "事实 / 案例 / 完成度边界", "报名入口")
        return {"date": self.DATE, "type": "图文", "title": "正文优先", "summary": "无图也发布", "slug": "text-first", "heroImage": "", "galleryImages": [], "lead": "正文有效。", "sections": [{"heading": heading, "paragraphs": ["有效正文。"]} for heading in headings], "imageRoles": [], "passedRoles": [], "missingRoles": ["website_hero", "core_explanation", "real_application", "social_promotion"], "media_status": "none", "content_validated": True}

    def write_manifest(self, manifest):
        path = self.tmp / "manifest.json"
        path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        return path

    def test_zero_image_render_has_no_empty_figure_or_broken_image(self):
        article = render_article(self.manifest(), "", [])
        self.assertNotIn("<figure", article)
        self.assertNotIn("<picture", article)
        self.assertNotIn('<img src=""', article)

    def test_zero_image_publish_records_none_media(self):
        result = publish_manifest(self.tmp, self.write_manifest(self.manifest()))
        article = Path(result["article"]).read_text(encoding="utf-8")
        self.assertNotIn("<figure", article)
        calendar = json.loads((self.tmp / "course-calendar.json").read_text(encoding="utf-8"))[0]
        self.assertEqual("none", calendar["media_status"])
        self.assertEqual([], calendar["passedRoles"])
        self.assertEqual(self.manifest()["missingRoles"], calendar["pendingRoles"])

    def test_v4_partial_derives_only_passed_role_with_strict_receipts(self):
        manifest = self.manifest()
        manifest.update(media_status="partial", passedRoles=["real_application"], missingRoles=["website_hero", "core_explanation", "social_promotion"], galleryImages=[str(self.source)], imageRoles=[{"role": "real_application", "path": str(self.source), "expected_text": ["逐字文本"]}])
        preview = derive_responsive_assets(self.source, self.tmp / "preview", self.source.stem, widths=(480, 768, 1280), page_role="gallery", expected_text=["逐字文本"], require_text_qa=True)
        keyed = [(str(row["width"]), row) for row in preview["derivatives"]] + [("fallback", preview["fallback"])]
        manifest["webImageQA"] = {"real_application": {key: {"image_sha256": row["sha256"], "ocr_exact_match": True, "vision_mobile_readable": True, "artifacts": False} for key, row in keyed}}
        result = publish_manifest(self.tmp, self.write_manifest(manifest))
        article = Path(result["article"]).read_text(encoding="utf-8")
        self.assertEqual(1, article.count("<picture>"))
        self.assertNotIn("update-hero", article)
        calendar = json.loads((self.tmp / "course-calendar.json").read_text(encoding="utf-8"))[0]
        self.assertEqual("partial", calendar["media_status"])
        self.assertEqual(["real_application"], calendar["passedRoles"])
        self.assertEqual(manifest["missingRoles"], calendar["pendingRoles"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
