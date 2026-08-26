#!/usr/bin/env python
"""Deterministic publisher for IP 实物化五天实战营 daily website updates."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import html
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

HERMES_LIB = Path("/root/.hermes/lib")
if str(HERMES_LIB) not in sys.path:
    sys.path.insert(0, str(HERMES_LIB))
from web_image_delivery import (  # noqa: E402
    EFFECTIVE_DATE as WEB_IMAGE_EFFECTIVE_DATE,
    build_picture_html,
    derive_responsive_assets,
    validate_web_image_manifest,
)

APPLICATION_URL = "https://wj.qq.com/s2/27296919/9499/"
INTERNAL_URL_MARKERS = (
    "wj.qq.com/stat/1/recycle",
    "wj.qq.com/stat/1/overview",
)
FORBIDDEN_PUBLIC_MARKERS = (
    "METRION",
    "元维构",
)
REQUIRED_SECTION_HEADINGS = (
    "具体问题",
    "核心判断",
    "步骤或标准",
    "常见错误",
    "与五天课程的关系",
    "事实 / 案例 / 完成度边界",
    "报名入口",
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_updates_js(calendar: list[dict[str, Any]]) -> str:
    payload = json.dumps(calendar, ensure_ascii=False, indent=2)
    return f"window.WORKSHOP_UPDATES = {payload};\n"


def slug_is_safe(value: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value))


def public_image_path(root: Path, date: str, source: Path) -> tuple[Path, str]:
    target_dir = root / "assets" / "updates" / date
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / source.name
    if source.resolve() != target.resolve():
        shutil.copy2(source, target)
    return target, f"../assets/updates/{date}/{source.name}"


def render_article(manifest: dict[str, Any], hero_href: str, gallery_hrefs: list[str], *, hero_picture: str | None = None, gallery_pictures: list[str] | None = None) -> str:
    title = html.escape(manifest["title"])
    summary = html.escape(manifest["summary"])
    lead = html.escape(manifest["lead"])
    date = html.escape(manifest["date"])
    content_type = html.escape(manifest["type"])
    disclaimer = html.escape(manifest.get("disclaimer", "课程公开示范内容，不代表往期学员成果。"))
    cta = manifest.get("cta") or {"label": "填写报名资料", "url": APPLICATION_URL}
    cta_label = html.escape(cta.get("label") or "填写报名资料")
    cta_url = html.escape(cta.get("url") or APPLICATION_URL, quote=True)

    section_markup = []
    for section in manifest.get("sections", []):
        heading = html.escape(section.get("heading", ""))
        paragraphs = "".join(f"<p>{html.escape(text)}</p>" for text in section.get("paragraphs", []))
        bullets = section.get("bullets", [])
        bullet_markup = ""
        if bullets:
            bullet_markup = "<ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in bullets) + "</ul>"
        section_markup.append(f'<section class="update-section"><h2>{heading}</h2>{paragraphs}{bullet_markup}</section>')

    gallery_markup = ""
    if gallery_pictures:
        gallery_markup = '<div class="update-gallery">' + "".join(gallery_pictures) + "</div>"
    elif gallery_hrefs:
        gallery_markup = '<div class="update-gallery">' + "".join(
            f'<img src="{html.escape(href, quote=True)}" alt="{title} 配图" />'
            for href in gallery_hrefs
        ) + "</div>"
    hero_markup = ""
    if hero_picture or hero_href:
        hero_markup = f'''<figure class="update-hero">
      {hero_picture or f'<img src="{html.escape(hero_href, quote=True)}" alt="{title}" />'}
      <figcaption>{disclaimer}</figcaption>
    </figure>'''

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="description" content="{summary}" />
  <title>{title} | IP 实物化五天实战营</title>
  <link rel="icon" href="../favicon.ico" sizes="any" />
  <link rel="stylesheet" href="../course.css" />
  <link rel="stylesheet" href="../update-article.css" />
</head>
<body class="update-page">
  <header class="update-header">
    <a href="../#updates">← 返回每日公开更新</a>
    <a class="update-brand" href="../#course-intro">IP 实物化五天实战营</a>
  </header>
  <main class="update-article">
    <header class="update-article-title">
      <p class="update-meta"><time datetime="{date}">{date}</time> · {content_type}</p>
      <h1>{title}</h1>
      <p class="update-lead">{lead}</p>
    </header>
    {hero_markup}
    {''.join(section_markup)}
    {gallery_markup}
    <aside class="update-boundary">
      <strong>课程边界</strong>
      <p>五天课程以完成第一版可继续发展的项目闭环为目标，不承诺商业级量产、人人进入正式展览或必然产生销售。</p>
    </aside>
    <section class="update-cta">
      <p>课程时间：2026 年 10 月 2 日至 10 月 6 日｜青岛｜每班限 10 人</p>
      <a href="{cta_url}" target="_blank" rel="noopener">{cta_label} →</a>
    </section>
  </main>
</body>
</html>
"""


def prepare_responsive_images(root: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Derive and gate exactly the QA-passed roles supplied by the manifest."""
    roles = manifest.get("imageRoles")
    expected_roles = ("website_hero", "core_explanation", "real_application", "social_promotion")
    role_names = [row.get("role") for row in roles if isinstance(row, dict)] if isinstance(roles, list) else []
    if not isinstance(roles, list) or len(role_names) != len(set(role_names)) or any(role not in expected_roles for role in role_names):
        raise ValueError("imageRoles 必须是唯一、已知且 QA PASS 的角色")
    if role_names != [role for role in expected_roles if role in role_names]:
        raise ValueError("imageRoles 顺序无效")
    if not roles:
        return []
    supplied_qa = manifest.get("webImageQA")
    if not isinstance(supplied_qa, dict):
        raise ValueError("2026-08-12 起缺少派生图片 SHA 绑定 OCR/Vision QA 回执")
    target_dir = root / "assets" / "updates" / manifest["date"]
    assets: list[dict[str, Any]] = []
    for index, row in enumerate(roles):
        role = row["role"]
        source = Path(str(row.get("path") or ""))
        expected_text = row.get("expected_text")
        if not source.is_file() or not isinstance(expected_text, list) or not expected_text:
            raise ValueError(f"{role} 缺少源图或 OCR exact expected_text")
        stem = Path(source.name).stem
        asset = derive_responsive_assets(
            source, target_dir, stem, widths=(480, 768, 1280),
            page_role="hero" if role == "website_hero" else "gallery",
            sizes="(max-width: 680px) 100vw, 760px" if role == "website_hero" else "(max-width: 680px) 100vw, 50vw",
            expected_text=[str(value) for value in expected_text], require_text_qa=True,
        )
        role_qa = supplied_qa.get(role)
        if not isinstance(role_qa, dict):
            raise ValueError(f"{role} 缺少派生图片 QA 回执")
        bound: dict[str, Any] = {}
        keyed = [(str(item["width"]), item) for item in asset["derivatives"]] + [("fallback", asset["fallback"])]
        for key, derivative in keyed:
            receipt = role_qa.get(key)
            if not isinstance(receipt, dict) or receipt.get("image_sha256") != derivative["sha256"]:
                raise ValueError(f"{role}:{key} 派生图片 QA 未绑定实际 SHA")
            bound[key] = dict(receipt)
        asset["qa_receipts"] = bound
        asset["role"] = role
        validate_web_image_manifest(asset, require_qa=True)
        assets.append(asset)
    return assets


def _publish_manifest_locked(root: Path | str, manifest_path: Path | str) -> dict[str, Any]:
    root = Path(root)
    manifest_path = Path(manifest_path)
    manifest = read_json(manifest_path)

    required = ("date", "type", "title", "summary", "slug", "lead", "sections")
    missing = [key for key in required if not manifest.get(key)]
    if missing:
        raise ValueError(f"manifest 缺少字段: {', '.join(missing)}")
    section_headings = {str(section.get("heading") or "").strip() for section in manifest["sections"]}
    missing_sections = [heading for heading in REQUIRED_SECTION_HEADINGS if heading not in section_headings]
    if missing_sections:
        raise ValueError(f"缺少必需章节: {', '.join(missing_sections)}")
    for section in manifest["sections"]:
        heading = str(section.get("heading") or "").strip()
        paragraphs = [str(item).strip() for item in section.get("paragraphs", []) if str(item).strip()]
        bullets = [str(item).strip() for item in section.get("bullets", []) if str(item).strip()]
        if not paragraphs and not bullets:
            raise ValueError(f"章节正文为空: {heading or '未命名章节'}")
    if not slug_is_safe(manifest["slug"]):
        raise ValueError("slug 只能使用小写英文、数字和短横线")
    if any(marker in json.dumps(manifest, ensure_ascii=False) for marker in INTERNAL_URL_MARKERS):
        raise ValueError("manifest 包含内部报名数据地址")
    if any(marker in json.dumps(manifest, ensure_ascii=False) for marker in FORBIDDEN_PUBLIC_MARKERS):
        raise ValueError("公开内容不得包含 METRION / 元维构品牌")

    calendar_path = root / "course-calendar.json"
    calendar = read_json(calendar_path)
    item = next((entry for entry in calendar if entry.get("date") == manifest["date"]), None)
    if item is None:
        raise ValueError(f"公开日历中没有日期 {manifest['date']}")

    hero_source = Path(manifest["heroImage"]) if manifest.get("heroImage") else None
    if hero_source is not None and not hero_source.exists():
        raise FileNotFoundError(f"主图不存在: {hero_source}")
    web_assets: list[dict[str, Any]] = []
    hero_picture: str | None = None
    gallery_pictures: list[str] | None = None
    if manifest["date"] >= WEB_IMAGE_EFFECTIVE_DATE:
        web_assets = prepare_responsive_images(root, manifest)
        manifest["webImageAssets"] = web_assets
        write_json(manifest_path, manifest)
        prefix = f"../assets/updates/{manifest['date']}/"
        hero_asset = next((asset for asset in web_assets if asset.get("role") == "website_hero"), None)
        hero_picture = build_picture_html(hero_asset, alt=manifest["title"], lcp=True, relative_prefix=prefix) if hero_asset else None
        gallery_pictures = [
            build_picture_html(asset, alt=f"{manifest['title']} 配图", lcp=False, relative_prefix=prefix)
            for asset in web_assets if asset.get("role") != "website_hero"
        ]
        hero_href = prefix + Path(hero_asset["fallback"]["path"]).name if hero_asset else ""
        gallery_hrefs = [prefix + Path(asset["fallback"]["path"]).name for asset in web_assets if asset.get("role") != "website_hero"]
    else:
        hero_href = ""
        if hero_source is not None:
            _, hero_href = public_image_path(root, manifest["date"], hero_source)
        gallery_hrefs = []
        for image in manifest.get("galleryImages", []):
            source = Path(image)
            if not source.exists():
                raise FileNotFoundError(f"配图不存在: {source}")
            _, href = public_image_path(root, manifest["date"], source)
            gallery_hrefs.append(href)
    missing_roles = list(dict.fromkeys(
        str(role).strip()
        for role in manifest.get("missingRoles", [])
        if str(role).strip()
    ))

    filename = f"{manifest['date']}-{manifest['slug']}.html"
    article_path = root / "updates" / filename
    article_path.parent.mkdir(parents=True, exist_ok=True)
    article_path.write_text(
        render_article(manifest, hero_href, gallery_hrefs, hero_picture=hero_picture, gallery_pictures=gallery_pictures),
        encoding="utf-8",
    )

    calendar_update: dict[str, Any] = {
            "source_id": f"workshop:{manifest['date']}",
            "title": manifest["title"],
            "summary": manifest["summary"],
            "cover": f"./assets/updates/{manifest['date']}/{hero_source.name}" if hero_source else "",
            "status": "published",
            "published": True,
            "url": f"./updates/{filename}",
            "media_status": manifest.get("media_status", "complete" if not missing_roles else ("none" if not web_assets else "partial")),
            "passedRoles": list(manifest.get("passedRoles") or []),
            "pendingRoles": list(manifest.get("pendingRoles") or manifest.get("missingRoles") or []),
    }
    hero_asset = next((asset for asset in web_assets if asset.get("role") == "website_hero"), None)
    # A missing website_hero remains pending media, but it must not leave an
    # otherwise published list/calendar item without a usable image. Reuse the
    # first strictly verified gallery derivative only as the card cover; do not
    # promote it to hero in the article or alter role/pending-role evidence.
    cover_asset = hero_asset or next(iter(web_assets), None)
    if cover_asset:
        public_prefix = f"./assets/updates/{manifest['date']}/"
        fallback = cover_asset["fallback"]
        calendar_update["cover"] = public_prefix + Path(fallback["path"]).name + f"?v={fallback['sha256'][:12]}"
        calendar_update["coverImage"] = {
            "srcset": ", ".join(
                f"{public_prefix}{Path(row['path']).name}?v={row['sha256'][:12]} {row['width']}w"
                for row in cover_asset["derivatives"]
            ),
            "sizes": cover_asset["sizes"],
            "fallback": calendar_update["cover"],
            "width": fallback["width"],
            "height": fallback["height"],
        }
    else:
        item.pop("coverImage", None)
    item.update(calendar_update)
    write_json(calendar_path, calendar)
    updates_payload = build_updates_js(calendar)
    (root / "course-updates.js").write_text(updates_payload, encoding="utf-8")
    index_path = root / "index.html"
    if index_path.is_file():
        index = index_path.read_text(encoding="utf-8")
        version = hashlib.sha256(updates_payload.encode("utf-8")).hexdigest()[:16]
        updated_index, count = re.subn(
            r'course-updates\.js\?v=[^"\']+',
            f'course-updates.js?v={version}',
            index,
            count=1,
        )
        if count != 1:
            raise ValueError("首页course-updates脚本标签缺失或不唯一")
        index_path.write_text(updated_index, encoding="utf-8")

    errors = validate_public_tree(root)
    if errors:
        raise ValueError("发布后检查失败:\n" + "\n".join(errors))

    return {
        "status": "partial_media_published" if missing_roles else "published",
        "missingRoles": missing_roles,
        "media_status": calendar_update["media_status"],
        "passedRoles": calendar_update["passedRoles"],
        "pendingRoles": calendar_update["pendingRoles"],
        "article": str(article_path),
        "url": item["url"],
        "cover": item["cover"],
        "webImageAssets": web_assets,
    }


def publish_manifest(root: Path | str, manifest_path: Path | str) -> dict[str, Any]:
    """Hold one date lock across derivation, QA binding, HTML and card updates."""
    manifest_path = Path(manifest_path)
    date = str(read_json(manifest_path).get("date") or "unknown")
    lock_path = Path("/tmp") / f"ip-object-workshop-publish-{date}.lock"
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            return _publish_manifest_locked(root, manifest_path)
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def validate_public_tree(root: Path | str) -> list[str]:
    root = Path(root)
    errors: list[str] = []
    ignored_parts = {".git", "scripts", "tests", "node_modules", "tmp"}
    public_suffixes = {".html", ".js", ".json", ".css"}

    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in public_suffixes:
            continue
        relative_parts = path.relative_to(root).parts
        if any(part in ignored_parts for part in relative_parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "�" in text:
            errors.append(f"{path}: 包含 UTF-8 替换字符")
        for marker in INTERNAL_URL_MARKERS:
            if marker in text:
                errors.append(f"{path}: 包含内部报名数据地址 {marker}")
        if re.search(r"(?:[A-Za-z]:\\|/root/\.hermes/)", text):
            errors.append(f"{path}: 包含本地或 NAS 绝对路径")

    calendar_path = root / "course-calendar.json"
    if calendar_path.exists():
        calendar = read_json(calendar_path)
        dates = [item.get("date") for item in calendar]
        if len(dates) != len(set(dates)):
            errors.append("course-calendar.json: 日期重复")
        for item in calendar:
            if item.get("status") == "published" and not item.get("url"):
                errors.append(f"{item.get('date')}: published 状态缺少 url")
            if item.get("published") and not item.get("url"):
                errors.append(f"{item.get('date')}: published=true 但缺少 url")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    publish = sub.add_parser("publish", help="根据 manifest 创建文章并更新公开日历")
    publish.add_argument("--root", type=Path, required=True)
    publish.add_argument("--manifest", type=Path, required=True)

    validate = sub.add_parser("validate", help="检查公开网站文件")
    validate.add_argument("--root", type=Path, required=True)

    build = sub.add_parser("build-js", help="从 JSON 日历生成浏览器 JS")
    build.add_argument("--root", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "publish":
        result = publish_manifest(args.root, args.manifest)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.command == "validate":
        errors = validate_public_tree(args.root)
        if errors:
            print("\n".join(errors))
            return 1
        print("OK: public workshop files validated")
        return 0
    if args.command == "build-js":
        calendar = read_json(args.root / "course-calendar.json")
        (args.root / "course-updates.js").write_text(build_updates_js(calendar), encoding="utf-8")
        print(f"Built {len(calendar)} updates")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
