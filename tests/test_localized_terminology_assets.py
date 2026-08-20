from __future__ import annotations

import copy
import importlib.util
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ("ko", "ja", "zh-CN", "es")
README_BY_LOCALE = {
    "ko": "README.ko.md",
    "ja": "README.ja.md",
    "zh-CN": "README.zh-CN.md",
    "es": "README.es.md",
}
ASSETS = ("brain-role-meme.svg", "brain-role-overview.svg", "brain-role-flow.svg")
EXPECTED_HOMEOSTAT_LOCALIZATIONS = {
    "ko": "항상성 조절기",
    "ja": "恒常性調節器",
    "zh-CN": "稳态调节器",
    "es": "homeostato",
}


def load_terminology() -> dict[str, Any]:
    return json.loads((ROOT / "docs/reference/localized-terminology.json").read_text(encoding="utf-8"))


def load_generator_module() -> Any:
    path = ROOT / "scripts/build_localized_assets.py"
    spec = importlib.util.spec_from_file_location("brain_role_localized_assets", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_homeostat_controller_translations_are_pinned() -> None:
    glossary = load_terminology()
    homeostat = next(term for term in glossary["terms"] if term["key"] == "homeostat")
    assert homeostat["locales"] == EXPECTED_HOMEOSTAT_LOCALIZATIONS


def test_glossary_validator_rejects_duplicate_keys_and_missing_locales() -> None:
    glossary = load_terminology()
    generator = load_generator_module()

    duplicate = copy.deepcopy(glossary)
    duplicate["terms"].append(copy.deepcopy(duplicate["terms"][0]))
    try:
        generator.validate_glossary(duplicate)
    except ValueError as error:
        assert "unique" in str(error)
    else:
        raise AssertionError("duplicate term key was accepted")

    missing_locale = copy.deepcopy(glossary)
    del missing_locale["terms"][0]["locales"]["ja"]
    try:
        generator.validate_glossary(missing_locale)
    except ValueError as error:
        assert "exactly the configured locales" in str(error)
    else:
        raise AssertionError("missing locale value was accepted")


def test_localized_readmes_use_canonical_plus_locale_terms_and_assets() -> None:
    glossary = load_terminology()
    terms = glossary["terms"]
    assert isinstance(terms, list)
    for locale in LOCALES:
        text = (ROOT / README_BY_LOCALE[locale]).read_text(encoding="utf-8")
        for term in terms:
            assert isinstance(term, dict)
            display = f'{term["canonical"]}({term["locales"][locale]})'
            assert display in text
        for asset in ASSETS:
            assert f"docs/assets/localized/{locale}/{asset}" in text


def test_localized_assets_are_self_contained_accessible_and_complete() -> None:
    glossary = load_terminology()
    terms_by_asset = glossary["assets"]
    for locale in LOCALES:
        for asset in ASSETS:
            path = ROOT / "docs/assets/localized" / locale / asset
            payload = path.read_text(encoding="utf-8")
            root = ET.fromstring(payload)
            assert root.tag.endswith("svg")
            assert "viewBox" in root.attrib
            assert "<title" in payload and "<desc" in payload
            assert "<script" not in payload
            assert "foreignObject" not in payload
            assert 'href="http://' not in payload and 'href="https://' not in payload
            assert "data:image/png;base64," in payload
            for key in terms_by_asset[asset]:
                term = next(item for item in glossary["terms"] if item["key"] == key)
                assert f'{term["canonical"]}({term["locales"][locale]})' in payload


def test_localized_asset_generator_is_deterministic(tmp_path: Path) -> None:
    import subprocess
    import sys

    subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_localized_assets.py"), "--output-root", str(tmp_path)],
        cwd=ROOT,
        check=True,
    )
    for locale in LOCALES:
        for asset in ASSETS:
            expected = ROOT / "docs/assets/localized" / locale / asset
            generated = tmp_path / locale / asset
            assert generated.read_bytes() == expected.read_bytes()
    assert (tmp_path / "manifest.json").read_bytes() == (
        ROOT / "docs/assets/localized/manifest.json"
    ).read_bytes()


def test_localized_asset_manifest_matches_bytes() -> None:
    import hashlib

    manifest = json.loads((ROOT / "docs/assets/localized/manifest.json").read_text(encoding="utf-8"))
    assert manifest["schemaVersion"] == 1
    assert len(manifest["entries"]) == len(LOCALES) * len(ASSETS)
    for entry in manifest["entries"]:
        payload = (ROOT / "docs/assets/localized" / entry["path"]).read_bytes()
        source = (ROOT / entry["source"]).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == entry["sha256"]
        assert hashlib.sha256(source).hexdigest() == entry["sourceSha256"]
        assert entry["width"] == 1536
        assert entry["height"] > 1024


def test_existing_english_readme_and_assets_are_frozen() -> None:
    expected = {
        "README.md": "41fbb6d7568dfbd1c6ebcc11754237980618e7a722044fc317e01d627320172a",
        "docs/assets/brain-role-meme.png": "4fcc65d3d27bfaf6840a4b49533b606c12009a013ef031f20a3e96c686cb2322",
        "docs/assets/brain-role-overview.svg": "e9ea05e98ce11319f237ad820f85056d3957a084cd73d6701b8fa3e7ce5d9304",
        "docs/assets/brain-role-flow.svg": "ad481e9cd5e0c9c8de912b6240b5f359bdc87236ca7675aedd83e5e852c12899",
    }
    import hashlib

    for relative, digest in expected.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest
