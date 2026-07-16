#!/usr/bin/env python
"""Deterministic publisher for IP 实物化五天实战营 daily website updates."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path
from typing import Any

APPLICATION_URL = "https://wj.qq.com/s2/27296919/9499/"
INTERNAL_URL_MARKERS = (
    "wj.qq.com/stat/1/recycle",
    "wj.qq.com/stat/1/overview",
)
FORBIDDEN_PUBLIC_MARKERS = (
    "METRION",
    "元维构",
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


def render_article(manifest: dict[str, Any], hero_href: str, gallery_hrefs: list[str]) -> str:
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
    if gallery_hrefs:
        gallery_markup = '<div class="update-gallery">' + "".join(
            f'<img src="{html.escape(href, quote=True)}" alt="{title} 配图" />'
            for href in gallery_hrefs
        ) + "</div>"

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="description" content="{summary}" />
  <title>{title} | IP 实物化五天实战营</title>
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
    <figure class="update-hero">
      <img src="{html.escape(hero_href, quote=True)}" alt="{title}" />
      <figcaption>{disclaimer}</figcaption>
    </figure>
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


def publish_manifest(root: Path | str, manifest_path: Path | str) -> dict[str, str]:
    root = Path(root)
    manifest_path = Path(manifest_path)
    manifest = read_json(manifest_path)

    required = ("date", "type", "title", "summary", "slug", "heroImage", "lead", "sections")
    missing = [key for key in required if not manifest.get(key)]
    if missing:
        raise ValueError(f"manifest 缺少字段: {', '.join(missing)}")
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

    hero_source = Path(manifest["heroImage"])
    if not hero_source.exists():
        raise FileNotFoundError(f"主图不存在: {hero_source}")
    _, hero_href = public_image_path(root, manifest["date"], hero_source)

    gallery_hrefs: list[str] = []
    for image in manifest.get("galleryImages", []):
        source = Path(image)
        if not source.exists():
            raise FileNotFoundError(f"配图不存在: {source}")
        _, href = public_image_path(root, manifest["date"], source)
        gallery_hrefs.append(href)

    filename = f"{manifest['date']}-{manifest['slug']}.html"
    article_path = root / "updates" / filename
    article_path.parent.mkdir(parents=True, exist_ok=True)
    article_path.write_text(render_article(manifest, hero_href, gallery_hrefs), encoding="utf-8")

    item.update(
        {
            "title": manifest["title"],
            "summary": manifest["summary"],
            "cover": f"./assets/updates/{manifest['date']}/{hero_source.name}",
            "status": "published",
            "published": True,
            "url": f"./updates/{filename}",
        }
    )
    write_json(calendar_path, calendar)
    (root / "course-updates.js").write_text(build_updates_js(calendar), encoding="utf-8")

    errors = validate_public_tree(root)
    if errors:
        raise ValueError("发布后检查失败:\n" + "\n".join(errors))

    return {"article": str(article_path), "url": item["url"], "cover": item["cover"]}


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
