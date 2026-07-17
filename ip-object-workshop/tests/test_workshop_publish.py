import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from release_daily import is_expected_remote  # noqa: E402
from workshop_publish import build_updates_js, publish_manifest, validate_public_tree  # noqa: E402


class WorkshopPublishTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "assets").mkdir()
        (self.tmp / "updates").mkdir()
        (self.tmp / "course.css").write_text("body{}", encoding="utf-8")
        (self.tmp / "course-config.js").write_text(
            'window.WORKSHOP_CONFIG={applicationFormUrl:"https://wj.qq.com/s2/27296919/9499/"};',
            encoding="utf-8",
        )
        self.calendar = [
            {
                "date": "2026-07-15",
                "type": "图文",
                "title": "课程示范：一张角色图怎样完成结构转译",
                "time": "11:30",
                "summary": "用具体判断说明二维作品进入三维前需要补齐什么。",
                "cover": "./assets/workshop-modeling.png",
                "status": "planned",
                "published": False,
                "url": "",
            }
        ]
        (self.tmp / "course-calendar.json").write_text(
            json.dumps(self.calendar, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (self.tmp / "source.png").write_bytes(b"fake-png")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_expected_remote_accepts_ssh_alias_used_on_nas(self):
        self.assertTrue(is_expected_remote("git@github-ouart:chuyiouart/chuyi.git"))
        self.assertTrue(is_expected_remote("git@github.com:chuyiouart/chuyi.git"))
        self.assertTrue(is_expected_remote("https://github.com/chuyiouart/chuyi.git"))
        self.assertFalse(is_expected_remote("git@github.com:someone-else/chuyi.git"))

    def test_build_updates_js_preserves_explicit_status(self):
        output = build_updates_js(self.calendar)
        self.assertIn("window.WORKSHOP_UPDATES", output)
        self.assertIn('"status": "planned"', output)
        self.assertIn('"published": false', output)

    def test_publish_manifest_creates_article_and_updates_calendar(self):
        manifest = {
            "date": "2026-07-15",
            "type": "图文",
            "title": "课程示范：一张角色图怎样完成结构转译",
            "summary": "从输入图、遮挡、重心和结构厚度开始判断。",
            "slug": "structure-translation-demo",
            "heroImage": str(self.tmp / "source.png"),
            "lead": "一张角色图进入三维前，需要先把看不见的结构补清楚。",
            "sections": [
                {"heading": "先补齐输入", "paragraphs": ["准备正面、侧面、背面和材质参考。"]},
                {"heading": "再判断结构", "paragraphs": ["检查遮挡、悬空、薄片和重心。"]},
            ],
            "cta": {"label": "填写报名资料", "url": "https://wj.qq.com/s2/27296919/9499/"},
            "disclaimer": "课程示范内容，不是往期学员案例。",
        }
        manifest_path = self.tmp.parent / f"{self.tmp.name}-manifest.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        self.addCleanup(lambda: manifest_path.unlink(missing_ok=True))

        result = publish_manifest(self.tmp, manifest_path)

        article = self.tmp / "updates" / "2026-07-15-structure-translation-demo.html"
        self.assertTrue(article.exists())
        article_text = article.read_text(encoding="utf-8")
        self.assertIn("课程示范：一张角色图怎样完成结构转译", article_text)
        self.assertIn("课程示范内容，不是往期学员案例。", article_text)
        self.assertNotIn("METRION", article_text)

        calendar = json.loads((self.tmp / "course-calendar.json").read_text(encoding="utf-8"))
        self.assertEqual(calendar[0]["status"], "published")
        self.assertTrue(calendar[0]["published"])
        self.assertEqual(calendar[0]["url"], "./updates/2026-07-15-structure-translation-demo.html")
        self.assertTrue((self.tmp / "assets" / "updates" / "2026-07-15" / "source.png").exists())
        self.assertEqual(result["url"], calendar[0]["url"])

    def test_validate_public_tree_rejects_internal_questionnaire_url(self):
        (self.tmp / "leak.html").write_text(
            "https://wj.qq.com/stat/1/recycle?sid=27296919", encoding="utf-8"
        )
        errors = validate_public_tree(self.tmp)
        self.assertTrue(any("内部报名数据地址" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
