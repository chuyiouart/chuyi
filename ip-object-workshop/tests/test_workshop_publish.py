import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, "/root/.hermes/lib")

from release_daily import git_with_retry, is_expected_remote  # noqa: E402
from workshop_publish import build_updates_js, publish_manifest, validate_public_tree  # noqa: E402
from web_image_delivery import derive_responsive_assets  # noqa: E402


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

    def test_git_retry_handles_openssh_connection_to_timed_out_wording(self):
        attempts = [
            subprocess.CompletedProcess(
                ["git", "pull"],
                1,
                "",
                "Connection to 20.205.243.160 port 443 timed out",
            ),
            subprocess.CompletedProcess(["git", "pull"], 0, "Already up to date.", ""),
        ]
        with patch("release_daily.git", side_effect=attempts) as mocked_git, patch(
            "release_daily.time.sleep"
        ) as mocked_sleep:
            result = git_with_retry(
                Path("/tmp"), "pull", "--ff-only", "origin", "main", delays=(0, 0)
            )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(mocked_git.call_count, 2)
        mocked_sleep.assert_called_once_with(0)

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
                {"heading": "具体问题", "paragraphs": ["二维角色只有单视图时，遮挡、背面和材质信息都不足以支持三维判断。"]},
                {"heading": "核心判断", "paragraphs": ["先补齐可验证输入，再决定结构转译与制作范围。"]},
                {"heading": "步骤或标准", "bullets": ["确认用途", "补齐视图", "标记材质", "检查结构"]},
                {"heading": "常见错误", "paragraphs": ["只追求画面好看，却忽略遮挡、悬空、薄片和重心。"]},
                {"heading": "与五天课程的关系", "paragraphs": ["这一步对应第一天的范围锁定，并为第二天三维初模准备输入。"]},
                {"heading": "事实 / 案例 / 完成度边界", "paragraphs": ["页面内容是课程方法示意，不是往期学员案例，也不承诺五天量产。"]},
                {"heading": "报名入口", "paragraphs": ["两类起点都可填写公开报名资料：https://wj.qq.com/s2/27296919/9499/"]},
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
        self.assertIn('<link rel="icon" href="../favicon.ico" sizes="any" />', article_text)
        self.assertIn("课程示范内容，不是往期学员案例。", article_text)
        self.assertNotIn("METRION", article_text)

        calendar = json.loads((self.tmp / "course-calendar.json").read_text(encoding="utf-8"))
        self.assertEqual(calendar[0]["status"], "published")
        self.assertTrue(calendar[0]["published"])
        self.assertEqual(calendar[0]["url"], "./updates/2026-07-15-structure-translation-demo.html")
        self.assertTrue((self.tmp / "assets" / "updates" / "2026-07-15" / "source.png").exists())
        self.assertEqual(result["url"], calendar[0]["url"])

    def test_publish_manifest_allows_missing_optional_gallery_roles(self):
        manifest = {
            "date": "2026-07-15",
            "type": "图文",
            "title": "只有主图也可安全发布",
            "summary": "非主图缺失时不生成占位符或破图引用。",
            "slug": "hero-only-degraded-release",
            "heroImage": str(self.tmp / "source.png"),
            "galleryImages": [],
            "missingRoles": ["02-core-explanation", "04-social-promotion"],
            "lead": "正文和主图完整，非主图角色按动态画廊降级。",
            "sections": [
                {"heading": heading, "paragraphs": [f"{heading}具有可见正文。"]}
                for heading in (
                    "具体问题",
                    "核心判断",
                    "步骤或标准",
                    "常见错误",
                    "与五天课程的关系",
                    "事实 / 案例 / 完成度边界",
                    "报名入口",
                )
            ],
        }
        manifest_path = self.tmp.parent / f"{self.tmp.name}-hero-only.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        self.addCleanup(lambda: manifest_path.unlink(missing_ok=True))

        result = publish_manifest(self.tmp, manifest_path)

        article = self.tmp / "updates" / "2026-07-15-hero-only-degraded-release.html"
        article_text = article.read_text(encoding="utf-8")
        self.assertEqual(result["status"], "partial_media_published")
        self.assertEqual(result["missingRoles"], ["02-core-explanation", "04-social-promotion"])
        self.assertNotIn("update-gallery", article_text)
        self.assertNotIn("04-social-promotion", article_text)

    def test_publish_manifest_allows_missing_hero_role_under_text_first_policy(self):
        manifest = {
            "date": "2026-07-15",
            "type": "图文",
            "title": "主图缺失不能降级发布",
            "summary": "主图属于网站硬门槛。",
            "slug": "missing-required-hero",
            "heroImage": str(self.tmp / "source.png"),
            "missingRoles": ["01-website-hero"],
            "lead": "即使文件路径存在，角色状态也不能自相矛盾。",
            "sections": [
                {"heading": heading, "paragraphs": [f"{heading}具有可见正文。"]}
                for heading in (
                    "具体问题",
                    "核心判断",
                    "步骤或标准",
                    "常见错误",
                    "与五天课程的关系",
                    "事实 / 案例 / 完成度边界",
                    "报名入口",
                )
            ],
        }
        manifest_path = self.tmp.parent / f"{self.tmp.name}-missing-hero.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        self.addCleanup(lambda: manifest_path.unlink(missing_ok=True))

        result = publish_manifest(self.tmp, manifest_path)
        self.assertEqual("partial_media_published", result["status"])

    def test_publish_manifest_rejects_sections_with_headings_but_no_visible_content(self):
        headings = [
            "具体问题",
            "核心判断",
            "步骤或标准",
            "常见错误",
            "与五天课程的关系",
            "事实 / 案例 / 完成度边界",
            "报名入口",
        ]
        manifest = {
            "date": "2026-07-15",
            "type": "图文",
            "title": "只有标题的空壳文章",
            "summary": "这个清单必须在发布前被拒绝。",
            "slug": "empty-section-shell",
            "heroImage": str(self.tmp / "source.png"),
            "lead": "引言存在，但七个正文区块为空。",
            "sections": [{"heading": heading} for heading in headings],
            "cta": {"label": "填写报名资料", "url": "https://wj.qq.com/s2/27296919/9499/"},
        }
        manifest_path = self.tmp.parent / f"{self.tmp.name}-empty-sections.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        self.addCleanup(lambda: manifest_path.unlink(missing_ok=True))

        with self.assertRaisesRegex(ValueError, "章节正文为空"):
            publish_manifest(self.tmp, manifest_path)

    def test_publish_manifest_rejects_missing_required_website_sections(self):
        manifest = {
            "date": "2026-07-15",
            "type": "图文",
            "title": "缺少完整章节的文章",
            "summary": "只有一个有内容的章节仍不符合网站合同。",
            "slug": "missing-required-sections",
            "heroImage": str(self.tmp / "source.png"),
            "lead": "引言存在。",
            "sections": [{"heading": "具体问题", "paragraphs": ["这里有实际问题说明。"]}],
            "cta": {"label": "填写报名资料", "url": "https://wj.qq.com/s2/27296919/9499/"},
        }
        manifest_path = self.tmp.parent / f"{self.tmp.name}-missing-sections.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        self.addCleanup(lambda: manifest_path.unlink(missing_ok=True))

        with self.assertRaisesRegex(ValueError, "缺少必需章节"):
            publish_manifest(self.tmp, manifest_path)

    def test_validate_public_tree_rejects_internal_questionnaire_url(self):
        (self.tmp / "leak.html").write_text(
            "https://wj.qq.com/stat/1/recycle?sid=27296919", encoding="utf-8"
        )
        errors = validate_public_tree(self.tmp)
        self.assertTrue(any("内部报名数据地址" in error for error in errors))


class FutureResponsiveWebsiteTests(unittest.TestCase):
    DATE = "2026-08-12"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ip-workshop-responsive-"))
        for directory in ("assets", "updates"):
            (self.tmp / directory).mkdir()
        for filename in ("course.css", "update-article.css"):
            (self.tmp / filename).write_text("body{}", encoding="utf-8")
        calendar = [{"date": self.DATE, "type": "图文", "title": "计划内容", "time": "11:30", "summary": "计划摘要", "cover": "./assets/old.png", "status": "planned", "published": False, "url": ""}]
        (self.tmp / "course-calendar.json").write_text(json.dumps(calendar, ensure_ascii=False), encoding="utf-8")
        self.sources = []
        for index, name in enumerate(("01-website-hero.png", "02-core-explanation.png", "03-real-application.png", "04-social-promotion.png"), 1):
            path = self.tmp / f"source-{name}"
            Image.new("RGB", (1400, 900), (30 * index, 60, 180)).save(path)
            self.sources.append(path)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def manifest(self):
        headings = ("具体问题", "核心判断", "步骤或标准", "常见错误", "与五天课程的关系", "事实 / 案例 / 完成度边界", "报名入口")
        roles = ("website_hero", "core_explanation", "real_application", "social_promotion")
        return {
            "date": self.DATE, "type": "图文", "title": "未来响应式图片测试", "summary": "四张图必须各自有完整响应式资产。",
            "slug": "future-responsive-images", "heroImage": str(self.sources[0]), "galleryImages": [str(path) for path in self.sources[1:]],
            "lead": "验证未来网站图片合同。", "sections": [{"heading": heading, "paragraphs": [f"{heading}正文。"]} for heading in headings],
            "imageRoles": [{"role": role, "path": str(path), "expected_text": [f"逐字文本{index}"]} for index, (role, path) in enumerate(zip(roles, self.sources), 1)],
        }

    def write_manifest(self, value):
        path = self.tmp / "future-manifest.json"
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return path

    def test_future_publish_fails_closed_without_derivative_sha_qa_receipts(self):
        with self.assertRaisesRegex(ValueError, "派生.*QA|QA.*派生"):
            publish_manifest(self.tmp, self.write_manifest(self.manifest()))

    def test_future_article_and_dynamic_cover_use_complete_responsive_assets(self):
        manifest = self.manifest()
        manifest["webImageQA"] = {}
        for index, row in enumerate(manifest["imageRoles"]):
            preview = derive_responsive_assets(
                row["path"], self.tmp / f"preview-{index}", Path(row["path"]).stem,
                widths=(480, 768, 1280), page_role="hero" if index == 0 else "gallery",
                expected_text=row["expected_text"], require_text_qa=True,
            )
            keyed = [(str(asset["width"]), asset) for asset in preview["derivatives"]] + [("fallback", preview["fallback"])]
            manifest["webImageQA"][row["role"]] = {
                key: {"image_sha256": asset["sha256"], "ocr_exact_match": True, "vision_mobile_readable": True, "artifacts": False}
                for key, asset in keyed
            }
        result = publish_manifest(self.tmp, self.write_manifest(manifest))
        article = Path(result["article"]).read_text(encoding="utf-8")
        self.assertEqual(4, article.count("<picture>"))
        for marker in ("480w", "768w", "1280w"):
            self.assertIn(marker, article)
        self.assertEqual(1, article.count('loading="eager"'))
        self.assertEqual(1, article.count('fetchpriority="high"'))
        self.assertEqual(3, article.count('loading="lazy"'))
        self.assertEqual(4, article.count('decoding="async"'))
        self.assertEqual(4, article.count('width="1280"'))
        self.assertEqual(4, len(result["webImageAssets"]))
        for asset in result["webImageAssets"]:
            self.assertEqual({480, 768, 1280}, {row["width"] for row in asset["derivatives"]})
            for key, receipt in asset["qa_receipts"].items():
                expected = asset["fallback"]["sha256"] if key == "fallback" else next(row["sha256"] for row in asset["derivatives"] if str(row["width"]) == key)
                self.assertEqual(receipt["image_sha256"], expected)
        calendar = json.loads((self.tmp / "course-calendar.json").read_text(encoding="utf-8"))
        self.assertTrue({"srcset", "sizes", "fallback", "width", "height"} <= set(calendar[0]["coverImage"]))
        self.assertIn('"coverImage"', (self.tmp / "course-updates.js").read_text(encoding="utf-8"))

    def test_dynamic_today_cover_applies_complete_responsive_contract(self):
        course_js = (PROJECT_ROOT / "course.js").read_text(encoding="utf-8")
        for marker in ("cover.srcset = item.coverImage.srcset", "cover.sizes = item.coverImage.sizes", "cover.width = item.coverImage.width", "cover.height = item.coverImage.height", "cover.dataset.imageFallback = item.coverImage.fallback"):
            self.assertIn(marker, course_js)


if __name__ == "__main__":
    unittest.main()
