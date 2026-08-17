from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from release_daily import build_release_allowlist, classify_checkpoint_dirty_paths


class ReleaseDailyEntrypointTests(unittest.TestCase):
    def setUp(self):
        self.tmp_obj = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp_obj.name)
        (self.repo / "ip-object-workshop/updates").mkdir(parents=True)
        for name in ("course-calendar.json", "course-updates.js", "index.html"):
            (self.repo / "ip-object-workshop" / name).write_text(name, encoding="utf-8")
        self.article = self.repo / "ip-object-workshop/updates/2026-08-17-day-3.html"
        self.article.write_text("Day 3", encoding="utf-8")
        self.manifest = {"date": "2026-08-17", "slug": "day-3", "media_status": "none", "webImageAssets": []}

    def tearDown(self):
        self.tmp_obj.cleanup()

    def asset(self, role: str, name: str):
        path = self.repo / "ip-object-workshop/assets/updates/2026-08-17" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"asset")
        return {"role": role, "fallback": {"path": str(path)}, "derivatives": []}

    def test_zero_image_allowlist_never_contains_missing_asset_directory(self):
        paths = build_release_allowlist(self.repo, self.manifest, {"article": str(self.article), "webImageAssets": []})
        self.assertEqual(4, len(paths))
        self.assertFalse(any("assets/updates/2026-08-17" in path for path in paths))

    def test_one_and_four_image_allowlists_add_only_real_files(self):
        for count in (1, 4):
            assets = [self.asset(f"role-{i}", f"0{i}-fallback.png") for i in range(1, count + 1)]
            paths = build_release_allowlist(self.repo, self.manifest, {"article": str(self.article), "webImageAssets": assets})
            self.assertEqual(4 + count, len(paths))
            self.assertTrue(all((self.repo / path).is_file() for path in paths))

    def test_resume_derives_exact_site_asset_names_from_manifest_qa(self):
        asset_root = self.repo / "ip-object-workshop/assets/updates/2026-08-17"
        asset_root.mkdir(parents=True)
        for name in ("01-website-hero-480.webp", "01-website-hero-fallback.png"):
            (asset_root / name).write_bytes(b"x")
        manifest = {"date": "2026-08-17", "slug": "day-3", "imageRoles": [{"role": "website_hero", "filename": "01-website-hero.png"}], "webImageQA": {"website_hero": {"480": {}, "fallback": {}}}}
        result = build_release_allowlist(self.repo, manifest, {"article": str(self.article)})
        self.assertIn("ip-object-workshop/assets/updates/2026-08-17/01-website-hero-480.webp", result)
        self.assertIn("ip-object-workshop/assets/updates/2026-08-17/01-website-hero-fallback.png", result)

    def test_checkpoint_accepts_exact_generated_paths_and_rejects_extra(self):
        allowlist = build_release_allowlist(self.repo, self.manifest, {"article": str(self.article), "webImageAssets": []})
        exact = [" M ip-object-workshop/course-calendar.json", " M ip-object-workshop/course-updates.js", " M ip-object-workshop/index.html", "?? ip-object-workshop/updates/2026-08-17-day-3.html"]
        self.assertEqual(set(allowlist), set(classify_checkpoint_dirty_paths(exact, allowlist)))
        with self.assertRaises(RuntimeError):
            classify_checkpoint_dirty_paths(exact + ["?? ip-object-workshop/other-project.txt"], allowlist)

    def test_duplicate_allowlist_is_stable_noop_input(self):
        published = {"article": str(self.article), "webImageAssets": []}
        self.assertEqual(build_release_allowlist(self.repo, self.manifest, published), build_release_allowlist(self.repo, self.manifest, published))


if __name__ == "__main__":
    unittest.main()
