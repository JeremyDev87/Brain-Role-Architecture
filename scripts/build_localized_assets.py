#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import math
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GLOSSARY_PATH = ROOT / "docs/reference/localized-terminology.json"
SOURCE_BY_OUTPUT = {
    "brain-role-meme.svg": ROOT / "docs/assets/brain-role-meme.png",
    "brain-role-overview.svg": ROOT / "docs/assets/brain-role-overview.svg",
    "brain-role-flow.svg": ROOT / "docs/assets/brain-role-flow.svg",
}
PANEL_TITLES = {
    "ko": "용어 표기 — 영문 식별자(한국어)",
    "ja": "用語表記 — 英語識別子(日本語)",
    "zh-CN": "术语标注 — 英文标识符(简体中文)",
    "es": "Terminología — identificador inglés(español)",
}
EMBEDDED_PNG = re.compile(r'data:image/png;base64,([^"\s]+)')


def png_base64(source: Path) -> str:
    if source.suffix == ".png":
        return base64.b64encode(source.read_bytes()).decode("ascii")
    match = EMBEDDED_PNG.search(source.read_text(encoding="utf-8"))
    if match is None:
        raise ValueError(f"embedded PNG not found: {source}")
    base64.b64decode(match.group(1), validate=True)
    return match.group(1)


def load_glossary() -> dict[str, Any]:
    glossary = json.loads(GLOSSARY_PATH.read_text(encoding="utf-8"))
    validate_glossary(glossary)
    return glossary


def validate_glossary(glossary: dict[str, Any]) -> None:
    locales = glossary.get("locales")
    terms = glossary.get("terms")
    assets = glossary.get("assets")
    if not isinstance(locales, list) or not locales or len(locales) != len(set(locales)):
        raise ValueError("locales must be a non-empty unique list")
    if not isinstance(terms, list) or not terms:
        raise ValueError("terms must be a non-empty list")
    if not isinstance(assets, dict) or not assets:
        raise ValueError("assets must be a non-empty object")

    keys: list[str] = []
    for term in terms:
        if not isinstance(term, dict):
            raise ValueError("each term must be an object")
        key = term.get("key")
        canonical = term.get("canonical")
        localized = term.get("locales")
        if not isinstance(key, str) or not key or not isinstance(canonical, str) or not canonical:
            raise ValueError("each term requires non-empty key and canonical values")
        if not isinstance(localized, dict) or set(localized) != set(locales):
            raise ValueError(f"term {key} must define exactly the configured locales")
        if any(not isinstance(value, str) or not value.strip() for value in localized.values()):
            raise ValueError(f"term {key} contains an empty locale value")
        keys.append(key)
    if len(keys) != len(set(keys)):
        raise ValueError("term keys must be unique")

    known_keys = set(keys)
    for asset_name, asset_keys in assets.items():
        if not isinstance(asset_name, str) or not isinstance(asset_keys, list):
            raise ValueError("asset mappings must use string names and key lists")
        if len(asset_keys) != len(set(asset_keys)):
            raise ValueError(f"asset {asset_name} contains duplicate term keys")
        unknown = set(asset_keys) - known_keys
        if unknown:
            raise ValueError(f"asset {asset_name} references unknown keys: {sorted(unknown)}")


def render_svg(locale: str, output_name: str, glossary: dict[str, Any]) -> str:
    term_by_key = {term["key"]: term for term in glossary["terms"]}
    displays = [
        f'{term_by_key[key]["canonical"]}({term_by_key[key]["locales"][locale]})'
        for key in glossary["assets"][output_name]
    ]
    columns = 2
    rows = math.ceil(len(displays) / columns)
    panel_top = 1024
    row_height = 44
    canvas_height = panel_top + 106 + rows * row_height + 28
    x_positions = (48, 786)
    term_lines: list[str] = []
    for index, display in enumerate(displays):
        column = index // rows
        row = index % rows
        x = x_positions[column]
        y = panel_top + 105 + row * row_height
        safe = html.escape(display)
        term_lines.append(
            f'  <text class="term" x="{x}" y="{y}" data-term-index="{index}">{safe}</text>'
        )
    title = html.escape(PANEL_TITLES[locale])
    desc = html.escape(
        f"Brain-Role Architecture {output_name} with canonical English identifiers and {locale} terminology."
    )
    payload = png_base64(SOURCE_BY_OUTPUT[output_name])
    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="1536" height="{canvas_height}" '
            f'viewBox="0 0 1536 {canvas_height}" role="img" aria-labelledby="title desc">',
            f"  <title id=\"title\">{title}</title>",
            f"  <desc id=\"desc\">{desc}</desc>",
            "  <style>",
            "    .panel-title { font: 700 28px system-ui, -apple-system, BlinkMacSystemFont,",
            "      'Segoe UI', sans-serif; fill: #f8fafc; }",
            "    .term { font: 600 21px system-ui, -apple-system, BlinkMacSystemFont,",
            "      'Segoe UI', sans-serif; fill: #e2e8f0; }",
            "  </style>",
            f'  <image width="1536" height="1024" preserveAspectRatio="xMidYMid meet" '
            f'href="data:image/png;base64,{payload}"/>',
            f'  <rect x="0" y="{panel_top}" width="1536" height="{canvas_height - panel_top}" fill="#0f172a"/>',
            f'  <line x1="48" y1="{panel_top + 72}" x2="1488" y2="{panel_top + 72}" '
            'stroke="#38bdf8" stroke-width="2"/>',
            f'  <text class="panel-title" x="48" y="{panel_top + 48}">{title}</text>',
            *term_lines,
            "</svg>",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build deterministic localized Brain-Role SVG assets")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "docs/assets/localized",
        help="directory that receives <locale>/<asset>.svg",
    )
    args = parser.parse_args()
    glossary = load_glossary()
    manifest_entries: list[dict[str, object]] = []
    for locale in glossary["locales"]:
        locale_root = args.output_root / locale
        locale_root.mkdir(parents=True, exist_ok=True)
        for output_name in glossary["assets"]:
            output = locale_root / output_name
            rendered = render_svg(locale, output_name, glossary)
            with output.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(rendered)
            height_match = re.search(r'<svg[^>]+height="(\d+)"', rendered)
            if height_match is None:
                raise ValueError(f"generated SVG height missing: {output}")
            manifest_entries.append(
                {
                    "path": output.relative_to(args.output_root).as_posix(),
                    "locale": locale,
                    "source": SOURCE_BY_OUTPUT[output_name].relative_to(ROOT).as_posix(),
                    "sourceSha256": hashlib.sha256(SOURCE_BY_OUTPUT[output_name].read_bytes()).hexdigest(),
                    "sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
                    "width": 1536,
                    "height": int(height_match.group(1)),
                }
            )
            print(output.relative_to(args.output_root))
    manifest = {
        "schemaVersion": 1,
        "generator": "scripts/build_localized_assets.py",
        "entries": manifest_entries,
    }
    manifest_path = args.output_root / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(manifest_path.relative_to(args.output_root))


if __name__ == "__main__":
    main()
