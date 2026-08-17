from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_public_content_policy.py"
CANARY_ROUTE = Path("ouart-model-site/canary-releases/ouart-daily-six-exact-one-canary-20260816-r1")
FORBIDDEN_LITERALS = (
    "ouart-exact-one-canary",
    "data-daily-six-complete=\"false\"",
    "internal_fixture_only",
    "run_kind=public_test",
    '"run_kind":"public_test"',
    '"run_kind": "public_test"',
    "Daily Six未完成",
    "Exact-one canary",
    "canary-releases/",
)


def production_text_files(root: Path):
    ignored = {".git", "tests", "scripts", "__pycache__", "node_modules"}
    for path in root.rglob("*"):
        if not path.is_file() or ignored.intersection(path.relative_to(root).parts):
            continue
        if path.suffix.lower() in {".html", ".js", ".json", ".xml", ".txt", ".webmanifest"}:
            yield path


def load_validator():
    assert VALIDATOR.is_file(), "canonical public content validator is missing"
    spec = importlib.util.spec_from_file_location("public_content_policy", VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_00_current_production_tree_has_no_internal_canary_surface():
    hits = []
    for path in production_text_files(ROOT):
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in FORBIDDEN_LITERALS:
            if marker.lower() in text.lower():
                hits.append(f"{path.relative_to(ROOT)}:{marker}")
    assert not CANARY_ROUTE.exists(), f"public canary route still exists: {CANARY_ROUTE}"
    assert hits == [], "internal/test canary markers leaked into production tree:\n" + "\n".join(hits)


def test_formal_complete_daily_six_metadata_is_eligible_and_unchanged():
    validator = load_validator()
    metadata = {
        "run_kind": "production",
        "content_kind": "daily_six",
        "target_count": 6,
        "daily_six_complete": True,
        "internal_fixture_only": False,
        "inject_main_homepage": True,
    }
    assert validator.validate_release_metadata(
        metadata,
        publication_root=ROOT,
        production_root=ROOT,
        now=datetime.now(timezone.utc),
    ) == []


def test_internal_fixture_is_never_eligible_for_public_test_or_telegram():
    validator = load_validator()
    metadata = {
        "run_kind": "public_test",
        "content_kind": "model_test",
        "target_count": 1,
        "daily_six_complete": False,
        "internal_fixture_only": True,
        "authorized_test_root": True,
        "fresh_until": "2099-01-01T00:00:00+00:00",
        "inject_main_homepage": False,
        "telegram_enabled": True,
    }
    errors = validator.validate_release_metadata(
        metadata,
        publication_root=Path("/tmp/ouart-authorized-test-root"),
        production_root=ROOT,
        now=datetime.now(timezone.utc),
    )
    assert any("internal_fixture_only" in error for error in errors)
    assert any("telegram" in error for error in errors)


def test_public_test_requires_fresh_authorized_separate_root_and_never_main_homepage():
    validator = load_validator()
    base = {
        "run_kind": "public_test",
        "content_kind": "model_test",
        "target_count": 1,
        "daily_six_complete": False,
        "internal_fixture_only": False,
        "authorized_test_root": True,
        "fresh_until": "2099-01-01T00:00:00+00:00",
        "inject_main_homepage": False,
        "telegram_enabled": False,
    }
    test_root = Path("/tmp/ouart-authorized-test-root")
    assert validator.validate_release_metadata(base, publication_root=test_root, production_root=ROOT, now=datetime.now(timezone.utc)) == []
    for changed in (
        {"authorized_test_root": False},
        {"fresh_until": "2000-01-01T00:00:00+00:00"},
        {"inject_main_homepage": True},
    ):
        candidate = {**base, **changed}
        assert validator.validate_release_metadata(candidate, publication_root=test_root, production_root=ROOT, now=datetime.now(timezone.utc))
    assert validator.validate_release_metadata(base, publication_root=ROOT, production_root=ROOT, now=datetime.now(timezone.utc))


def test_incomplete_or_non_six_daily_six_is_rejected_before_render():
    validator = load_validator()
    for target_count, complete in ((1, False), (1, True), (6, False)):
        errors = validator.validate_release_metadata(
            {
                "run_kind": "production",
                "content_kind": "daily_six",
                "target_count": target_count,
                "daily_six_complete": complete,
                "internal_fixture_only": False,
                "inject_main_homepage": True,
            },
            publication_root=ROOT,
            production_root=ROOT,
            now=datetime.now(timezone.utc),
        )
        assert errors


def test_public_text_scanner_rejects_internal_markers_and_preserves_formal_six():
    validator = load_validator()
    bad = '<section class="ouart-exact-one-canary" data-target-count="1" data-daily-six-complete="false">Daily Six未完成 <a href="canary-releases/x">Exact-one canary</a></section>'
    assert validator.scan_public_text(Path("index.html"), bad)
    good = '<section class="daily-six" data-target-count="6" data-daily-six-complete="true"><h2>今日模型</h2></section>'
    assert validator.scan_public_text(Path("index.html"), good) == []


def test_tree_validator_scans_html_js_json_and_service_worker_manifests():
    validator = load_validator()
    with TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "index.html").write_text("<main>正式内容</main>", encoding="utf-8")
        (root / "data.json").write_text(json.dumps({"run_kind": "public_test"}), encoding="utf-8")
        (root / "sw.js").write_text("const CACHE=['canary-releases/x'];", encoding="utf-8")
        errors = validator.validate_public_tree(root)
        assert any("data.json" in error for error in errors)
        assert any("sw.js" in error for error in errors)
