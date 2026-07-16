#!/usr/bin/env python3
"""Build a bilingual, rights-aware pigment index from Art is Creation pages.

The source pages are used as a discovery index. The generated public dataset
keeps identifiers and concise factual fields, but deliberately excludes the
source site's long notes, marketing lists, and copied editorial prose.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable


BASE_URL = "https://www.artiscreation.com/"
PAGES = {
    "yellow": "yellow.html",
    "orange": "orange.html",
    "red": "red.html",
    "violet": "violet.html",
    "blue": "blue.html",
    "green": "green.html",
    "brown": "brown.html",
    "black": "black.html",
    "white": "white.html",
    "misc": "other.html",
}

FAMILY_ZH = {
    "yellow": "黄色",
    "orange": "橙色",
    "red": "红色",
    "violet": "紫色",
    "blue": "蓝色",
    "green": "绿色",
    "brown": "棕色",
    "black": "黑色",
    "white": "白色",
    "misc": "金属、填料与其他",
}

FAMILY_SWATCH = {
    "yellow": "#d5ad25",
    "orange": "#d77724",
    "red": "#a83b32",
    "violet": "#6d4f82",
    "blue": "#315f88",
    "green": "#4f7056",
    "brown": "#765440",
    "black": "#292826",
    "white": "#e8e3d9",
    "misc": "#77736c",
}

CI_PREFIX_ZH = {
    "NY": "天然黄",
    "PY": "颜料黄",
    "NO": "天然橙",
    "PO": "颜料橙",
    "NR": "天然红",
    "PR": "颜料红",
    "NV": "天然紫",
    "PV": "颜料紫",
    "NB": "天然蓝",
    "PB": "颜料蓝",
    "NG": "天然绿",
    "PG": "颜料绿",
    "NBR": "天然棕",
    "PBR": "颜料棕",
    "NBK": "天然黑",
    "PBK": "颜料黑",
    "NW": "天然白",
    "PW": "颜料白",
    "PM": "金属颜料",
}

# Curated artist-facing translations. Unknown industrial entries still receive
# a correct Chinese CI generic label, instead of an invented common name.
COMMON_NAME_ZH = {
    "aerinite": "蓝黏土矿（气蓝石）",
    "apatite": "磷灰石",
    "azurite": "蓝铜矿",
    "lapis lazuli": "青金石",
    "ultramarine": "群青",
    "phthalocyanine blue": "酞菁蓝",
    "phthalo blue": "酞菁蓝",
    "cobalt blue": "钴蓝",
    "cerulean blue": "天蓝（钴锡蓝）",
    "prussian blue": "普鲁士蓝",
    "egyptian blue": "埃及蓝",
    "smalt": "花绀青（斯马尔特蓝）",
    "indigo": "靛蓝",
    "vivianite": "蓝铁矿",
    "mayan blue": "玛雅蓝",
    "han blue": "汉蓝",
    "yinmn": "YInMn 蓝",
    "cadmium yellow": "镉黄",
    "chrome yellow": "铬黄",
    "naples yellow": "那不勒斯黄",
    "yellow ochre": "黄赭石",
    "indian yellow": "印度黄",
    "aureolin": "钴黄",
    "hansa yellow": "汉莎黄",
    "nickel azo yellow": "镍偶氮黄",
    "bismuth vanadate": "钒酸铋黄",
    "lead-tin yellow": "铅锡黄",
    "orpiment": "雌黄",
    "gamboge": "藤黄",
    "cadmium orange": "镉橙",
    "mars orange": "马斯橙",
    "realgar": "雄黄",
    "pyrrole orange": "吡咯橙",
    "cadmium red": "镉红",
    "vermilion": "银朱（朱红）",
    "cinnabar": "朱砂",
    "alizarin crimson": "茜素深红",
    "madder lake": "茜草色淀",
    "carmine": "胭脂红",
    "quinacridone red": "喹吖啶酮红",
    "pyrrole red": "吡咯红",
    "venetian red": "威尼斯红",
    "indian red": "印度红",
    "red ochre": "红赭石",
    "mars red": "马斯红",
    "red lead": "铅丹",
    "minium": "铅丹",
    "hematite": "赤铁矿",
    "cobalt violet": "钴紫",
    "manganese violet": "锰紫",
    "dioxazine": "二噁嗪紫",
    "quinacridone magenta": "喹吖啶酮品红",
    "tyrian purple": "骨螺紫",
    "han purple": "汉紫",
    "phthalocyanine green": "酞菁绿",
    "phthalo green": "酞菁绿",
    "viridian": "翠绿",
    "chromium oxide green": "氧化铬绿",
    "terre verte": "绿土",
    "green earth": "绿土",
    "malachite": "孔雀石",
    "verdigris": "铜绿",
    "emerald green": "翡翠绿",
    "scheele's green": "舍勒绿",
    "cobalt green": "钴绿",
    "sap green": "树汁绿",
    "burnt umber": "熟褐",
    "raw umber": "生褐",
    "burnt sienna": "熟赭",
    "raw sienna": "生赭",
    "van dyke brown": "凡戴克棕",
    "sepia": "乌贼墨",
    "mummy": "木乃伊棕",
    "ivory black": "象牙黑",
    "bone black": "骨黑",
    "carbon black": "炭黑",
    "lamp black": "灯黑",
    "mars black": "马斯黑",
    "vine black": "藤黑",
    "graphite": "石墨",
    "magnetite": "磁铁矿",
    "titanium white": "钛白",
    "zinc white": "锌白",
    "zinc oxide white": "锌白",
    "lead white": "铅白",
    "flake white": "铅白",
    "cremnitz white": "克雷姆尼茨白",
    "lithopone": "锌钡白",
    "chalk": "白垩",
    "gypsum": "石膏",
    "barium sulfate": "硫酸钡",
    "calcium carbonate": "碳酸钙",
    "synthetic iron oxide red": "合成氧化铁红",
    "red iron oxide": "氧化铁红",
    "yellow iron oxide": "氧化铁黄",
    "iron oxide yellow": "氧化铁黄",
    "silver": "银粉",
    "gold": "金粉",
    "bronze powder": "铜合金粉",
    "aluminum powder": "铝粉",
}

CHEMISTRY_ZH = [
    ("titanium dioxide", "二氧化钛"),
    ("zinc oxide", "氧化锌"),
    ("cadmium sulfide", "硫化镉"),
    ("cadmium sulphide", "硫化镉"),
    ("cobalt aluminate", "铝酸钴"),
    ("copper phthalocyanine", "铜酞菁"),
    ("phthalocyanine", "酞菁"),
    ("quinacridone", "喹吖啶酮"),
    ("dioxazine", "二噁嗪"),
    ("synthetic iron oxide", "合成氧化铁"),
    ("iron oxide", "氧化铁"),
    ("carbon black", "炭黑"),
    ("lead carbonate", "碳酸铅"),
    ("calcium carbonate", "碳酸钙"),
    ("barium sulfate", "硫酸钡"),
    ("barium sulphate", "硫酸钡"),
    ("chromium oxide", "氧化铬"),
    ("cobalt oxide", "氧化钴"),
    ("manganese oxide", "氧化锰"),
    ("copper carbonate", "碳酸铜"),
    ("aluminum", "铝"),
    ("aluminium", "铝"),
    ("titanium", "钛"),
    ("cadmium", "镉"),
    ("mercury", "汞"),
    ("arsenic", "砷"),
    ("chromium", "铬"),
    ("cobalt", "钴"),
    ("copper", "铜"),
    ("manganese", "锰"),
    ("nickel", "镍"),
    ("zinc", "锌"),
    ("lead", "铅"),
    ("sulfate", "硫酸盐"),
    ("sulphate", "硫酸盐"),
    ("sulfide", "硫化物"),
    ("sulphide", "硫化物"),
    ("carbonate", "碳酸盐"),
    ("hydroxide", "氢氧化物"),
    ("phosphate", "磷酸盐"),
    ("silicate", "硅酸盐"),
    ("oxide", "氧化物"),
    ("chloride", "氯化物"),
    ("organic pigment", "有机颜料"),
    ("inorganic pigment", "无机颜料"),
    ("natural", "天然"),
    ("synthetic", "合成"),
]

COLOR_WORDS_ZH = [
    ("greenish blue", "偏绿蓝色"),
    ("reddish blue", "偏红蓝色"),
    ("bluish green", "偏蓝绿色"),
    ("yellowish green", "偏黄绿色"),
    ("orange red", "橙红色"),
    ("violet blue", "紫蓝色"),
    ("yellow", "黄色"),
    ("orange", "橙色"),
    ("red", "红色"),
    ("violet", "紫色"),
    ("purple", "紫色"),
    ("blue", "蓝色"),
    ("green", "绿色"),
    ("brown", "棕色"),
    ("black", "黑色"),
    ("white", "白色"),
    ("bright", "明亮"),
    ("deep", "深"),
    ("dark", "暗"),
    ("light", "浅"),
    ("pale", "淡"),
    ("warm", "暖"),
    ("cool", "冷"),
    ("neutral", "中性"),
    ("transparent", "透明"),
    ("opaque", "不透明"),
]


def normalize_space(value: str) -> str:
    value = html.unescape(value).replace("\xa0", " ")
    return re.sub(r"\s+", " ", value).strip(" ;,\t\r\n")


@dataclass
class Cell:
    text: str = ""
    links: list[str] = field(default_factory=list)


class PigmentTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[tuple[list[Cell], str]] = []
        self.in_row = False
        self.cell_depth = 0
        self.row_cells: list[Cell] = []
        self.cell_text: list[str] = []
        self.cell_links: list[str] = []
        self.row_anchor = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key.lower(): value or "" for key, value in attrs}
        if tag == "tr":
            self.in_row = True
            self.row_cells = []
            self.row_anchor = ""
        elif tag in {"td", "th"} and self.in_row:
            self.cell_depth += 1
            if self.cell_depth == 1:
                self.cell_text = []
                self.cell_links = []
        elif tag == "a" and self.in_row:
            anchor = attrs_dict.get("id") or attrs_dict.get("name")
            if anchor and not self.row_anchor:
                self.row_anchor = anchor
            href = attrs_dict.get("href")
            if href and self.cell_depth:
                self.cell_links.append(href)
        elif tag == "br" and self.cell_depth:
            self.cell_text.append("; ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self.in_row and self.cell_depth:
            self.cell_depth -= 1
            if self.cell_depth == 0:
                self.row_cells.append(
                    Cell(normalize_space("".join(self.cell_text)), list(dict.fromkeys(self.cell_links)))
                )
        elif tag == "tr" and self.in_row:
            if self.row_cells:
                self.rows.append((self.row_cells, self.row_anchor))
            self.in_row = False
            self.cell_depth = 0

    def handle_data(self, data: str) -> None:
        if self.cell_depth:
            self.cell_text.append(data)


def download(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "OUART-Knowledge-Index/1.0 (+https://chuyiouart.com/)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")


def ci_label_zh(code: str, family: str) -> str:
    compact = re.sub(r"\s+", "", code.upper())
    match = re.match(r"([A-Z]+)(.*)", compact)
    if not match or compact in {"N/A", "NA"}:
        return f"{FAMILY_ZH[family]}历史或天然颜料"
    prefix, number = match.groups()
    label = CI_PREFIX_ZH.get(prefix)
    return f"{label} {number}" if label else f"{FAMILY_ZH[family]}颜料 {compact}"


def clean_ci_code(value: str) -> str:
    raw = normalize_space(value)
    if raw.upper().startswith("N/A"):
        return "N/A"
    match = re.match(
        r"^(NY|PY|NO|PO|NR|PR|NV|PV|NB|PB|NG|PG|NBr|PBr|NBk|PBk|NW|PW|PM)\s*(\d+(?::\d+)?)(?:\s*(Blk))?",
        raw,
        flags=re.I,
    )
    if not match:
        return raw
    prefix_raw, number, black = match.groups()
    canonical = {
        "nbr": "NBr",
        "pbr": "PBr",
        "nbk": "NBk",
        "pbk": "PBk",
    }.get(prefix_raw.lower(), prefix_raw.upper())
    return f"{canonical}{number}{' Blk' if black else ''}"


def common_name_zh(name: str, code: str, family: str) -> tuple[str, str]:
    lower = name.lower()
    for term, translation in sorted(COMMON_NAME_ZH.items(), key=lambda item: len(item[0]), reverse=True):
        if term in lower:
            return translation, "curated"
    return ci_label_zh(code, family), "ci-generic"


def replace_terms(value: str, terms: Iterable[tuple[str, str]], limit: int = 240) -> str:
    concise = normalize_space(value)
    concise = re.sub(r"\((?:ref|reference)[^)]*\)", "", concise, flags=re.I)
    concise = re.sub(r"https?://\S+", "", concise)
    concise = normalize_space(concise)[:limit]
    translated = concise
    for source, target in terms:
        translated = re.sub(re.escape(source), target, translated, flags=re.I)
    return normalize_space(translated)


def normalize_opacity(value: str) -> dict[str, str]:
    raw = normalize_space(value)
    first = re.search(r"[1-4]", raw)
    mapping = {
        "1": ("opaque", "不透明"),
        "2": ("semi-opaque", "半不透明"),
        "3": ("semi-transparent", "半透明"),
        "4": ("transparent", "透明"),
    }
    if first and first.group(0) in mapping:
        en, zh = mapping[first.group(0)]
        return {"raw": raw, "level": first.group(0), "en": en, "zh": zh}
    lower = raw.lower()
    if "opaque" in lower:
        return {"raw": raw, "level": "1", "en": "opaque", "zh": "不透明"}
    if "trans" in lower:
        return {"raw": raw, "level": "4", "en": "transparent", "zh": "透明"}
    return {"raw": raw, "level": "", "en": "unknown", "zh": "待核验"}


def normalize_lightfastness(value: str) -> dict[str, str]:
    raw = normalize_space(value)
    roman = re.search(r"\b(I{1,3}|IV|V)\b", raw.upper())
    mapping = {
        "I": ("excellent", "优秀"),
        "II": ("very good", "很好"),
        "III": ("fair", "一般"),
        "IV": ("poor", "较差"),
        "V": ("fugitive", "易褪色"),
    }
    if roman:
        level = roman.group(1)
        en, zh = mapping[level]
        return {"raw": raw, "level": level, "en": en, "zh": zh}
    bws = re.search(r"(?:BWS\s*)?([1-8])(?:\s*[;/,-]\s*[1-8])?", raw, flags=re.I)
    if bws:
        n = int(bws.group(1))
        if n >= 7:
            zh = "优秀"
        elif n == 6:
            zh = "很好"
        elif n >= 4:
            zh = "一般"
        else:
            zh = "较差或易褪色"
        return {"raw": raw, "level": f"BWS {n}", "en": "blue wool scale", "zh": zh}
    return {"raw": raw, "level": "", "en": "unknown", "zh": "待核验"}


def normalize_hazard(value: str, composition: str) -> dict[str, object]:
    raw = normalize_space(value)
    rating_match = re.search(r"\b([A-D])\b", raw.upper())
    rating = rating_match.group(1) if rating_match else ""
    labels = {
        "A": ("low hazard", "低风险，但仍需规范操作"),
        "B": ("possible hazard", "不当操作可能有害"),
        "C": ("hazardous", "有害，需采取专业防护"),
        "D": ("extremely toxic", "高毒，仅限专业实验条件"),
    }
    en, zh = labels.get(rating, ("unverified", "待核验"))
    combined = f"{raw} {composition}".lower()
    triggers = []
    for term, label in {
        "lead": "铅",
        "cadmium": "镉",
        "mercury": "汞",
        "arsenic": "砷",
        "chromate": "铬酸盐",
        "cobalt": "钴",
        "nickel": "镍",
        "manganese": "锰",
    }.items():
        if term in combined:
            triggers.append(label)
    if triggers and rating in {"", "A"}:
        zh += "；含需复核成分：" + "、".join(triggers)
    return {"raw": raw, "rating": rating, "en": en, "zh": zh, "triggers": triggers}


def course_tags(record: dict[str, object]) -> list[str]:
    tags = ["色相与颜料身份"]
    family = str(record["family"])
    if family in {"white", "black"}:
        tags.append("明度与黑白极")
    if record["opacity"]["level"]:  # type: ignore[index]
        tags.append("透明度与覆盖力")
    if record["lightfastness"]["level"]:  # type: ignore[index]
        tags.append("耐光性与作品保存")
    if normalize_space(str(record["oil_absorption_raw"])) not in {"", "-", "N/A"}:
        tags.append("油画颜料体质")
    if record["hazard"]["rating"] or record["hazard"]["triggers"]:  # type: ignore[index]
        tags.append("材料安全")
    return tags


def row_to_record(cells: list[Cell], anchor: str, family: str, page: str, ordinal: int) -> dict[str, object] | None:
    if len(cells) != 11:
        return None
    values = [normalize_space(cell.text) for cell in cells]
    code, name = clean_ci_code(values[0]), values[1]
    if not name or "Common or Historical Name" in name or "Color Index Generic Name" in code:
        return None
    if len(name) > 220 or len(code) > 60:
        return None
    if not (code.upper() in {"N/A", "NA", "-"} or re.match(r"^[A-Za-z]{1,4}\s*\d", code)):
        return None

    name_zh, translation_status = common_name_zh(name, code, family)
    composition_en = replace_terms(values[4], [], 260)
    record: dict[str, object] = {
        "id": f"PIG-{family.upper()}-{ordinal:04d}",
        "family": family,
        "family_zh": FAMILY_ZH[family],
        "swatch": FAMILY_SWATCH[family],
        "ci_code": code,
        "ci_name_zh": ci_label_zh(code, family),
        "name_en": name,
        "name_zh": name_zh,
        "translation_status": translation_status,
        "constitution_number": values[3],
        "composition_en": composition_en,
        "composition_zh": replace_terms(composition_en, CHEMISTRY_ZH, 260),
        "color_description_en": values[5][:180],
        "color_description_zh": replace_terms(values[5], COLOR_WORDS_ZH, 180),
        "opacity": normalize_opacity(values[6]),
        "lightfastness": normalize_lightfastness(values[7]),
        "oil_absorption_raw": values[8],
        "hazard": normalize_hazard(values[9], values[4]),
        "source": {
            "name": "The Color of Art Pigment Database",
            "url": f"{BASE_URL}{page}{('#' + anchor) if anchor else ''}",
            "page": page,
            "retrieved": str(date.today()),
        },
        "review_status": "structured-unverified",
        "source_links": list(
            dict.fromkeys(
                link
                for cell in cells[3:11]
                for link in cell.links
                if link.startswith(("http://", "https://")) and "bit.ly" not in link
            )
        )[:6],
    }
    record["course_tags"] = course_tags(record)
    return record


def build_dataset() -> dict[str, object]:
    records: list[dict[str, object]] = []
    page_stats: dict[str, dict[str, int]] = {}
    seen: set[tuple[str, str, str]] = set()

    for family, page in PAGES.items():
        source = download(BASE_URL + page)
        parser = PigmentTableParser()
        parser.feed(source)
        accepted = 0
        for cells, anchor in parser.rows:
            record = row_to_record(cells, anchor, family, page, accepted + 1)
            if not record:
                continue
            key = (family, str(record["ci_code"]).lower(), str(record["name_en"]).lower())
            if key in seen:
                continue
            seen.add(key)
            accepted += 1
            record["id"] = f"PIG-{family.upper()}-{accepted:04d}"
            records.append(record)
        page_stats[family] = {"table_rows_seen": len(parser.rows), "records": accepted}

    status_counts = Counter(str(record["translation_status"]) for record in records)
    hazard_counts = Counter(str(record["hazard"]["rating"] or "unrated") for record in records)  # type: ignore[index]
    return {
        "meta": {
            "title_zh": "初艺颜料数据库",
            "title_en": "OUART Pigment Index",
            "version": "0.1.0",
            "generated": str(date.today()),
            "record_count": len(records),
            "families": {key: FAMILY_ZH[key] for key in PAGES},
            "source": "https://www.artiscreation.com/Color_index_names.html",
            "source_role": "discovery-index",
            "rights_note_zh": "仅整理颜料标识与简明事实字段；未转载原站长篇说明、营销名称清单和编辑性旁注。",
            "review_note_zh": "当前为结构化初稿。CI 通用中文名可直接检索；常用颜料译名已人工整理，化学组成中文为辅助初译，发布教学材料前须逐条复核。",
            "rating_key": {
                "opacity": {"1": "不透明", "2": "半不透明", "3": "半透明", "4": "透明"},
                "lightfastness": {"I": "优秀", "II": "很好", "III": "一般", "IV": "较差", "V": "易褪色"},
                "hazard": {"A": "低风险", "B": "不当操作可能有害", "C": "有害", "D": "高毒"},
            },
            "page_stats": page_stats,
            "translation_status_counts": dict(status_counts),
            "hazard_counts": dict(hazard_counts),
        },
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="data/pigments.json",
        help="Destination JSON path relative to the repository root.",
    )
    parser.add_argument(
        "--js-output",
        default="data/pigments-data.js",
        help="Browser-ready data path so the page also works when opened directly.",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    output = root / args.output
    js_output = root / args.js_output
    output.parent.mkdir(parents=True, exist_ok=True)
    js_output.parent.mkdir(parents=True, exist_ok=True)
    dataset = build_dataset()
    serialized = json.dumps(dataset, ensure_ascii=False, indent=2)
    output.write_text(serialized + "\n", encoding="utf-8")
    js_output.write_text(f"window.OUART_PIGMENTS = {serialized};\n", encoding="utf-8")
    print(json.dumps(dataset["meta"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
