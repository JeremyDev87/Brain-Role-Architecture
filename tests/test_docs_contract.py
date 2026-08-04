from __future__ import annotations

import hashlib
import importlib.util
import struct
import tomllib
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]


def load_check_docs() -> ModuleType:
    spec = importlib.util.spec_from_file_location("brain_role_check_docs", ROOT / "scripts" / "check_docs.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check_docs = load_check_docs()
README_NAMES = (
    "README.md",
    "README.ko.md",
    "README.zh-CN.md",
    "README.es.md",
    "README.ja.md",
)
LOCALE_MARKER = "<!-- locales: " + " ".join(README_NAMES) + " -->"
LOCALE_LABELS = {
    "README.md": "English",
    "README.ko.md": "한국어",
    "README.zh-CN.md": "简体中文",
    "README.es.md": "Español",
    "README.ja.md": "日本語",
}
EXPECTED_JSON = '{"errors":[],"specVersion":"0.1.0","valid":true}'
MEME_PATH = ROOT / "docs" / "assets" / "brain-role-meme.png"


def test_all_localized_readmes_share_the_public_contract() -> None:
    for name in README_NAMES:
        text = (ROOT / name).read_text(encoding="utf-8")
        assert text.startswith(LOCALE_MARKER)
        assert f"**{LOCALE_LABELS[name]}**" in text
        for other in README_NAMES:
            if other != name:
                assert f"]({other})" in text
        assert "PRE_RELEASE" in text
        assert "0.1.0" in text
        assert "SPEC.md" in text
        assert "docs/assets/brain-role-meme.png" in text
        assert "uv run brain-role validate" in text
        assert EXPECTED_JSON in text
        assert "make verify" in text


def test_meme_is_a_real_landscape_png() -> None:
    payload = MEME_PATH.read_bytes()
    assert payload.startswith(b"\x89PNG\r\n\x1a\n")
    assert hashlib.sha256(payload).hexdigest() == "7759fe2bf370b9e13b56555f860e04520d8301f6d414c6b51b973cf7800cf1e7"
    width, height = struct.unpack(">II", payload[16:24])
    assert width >= 1200
    assert height >= 675
    assert width > height


def test_sdist_declares_all_readmes_and_readme_assets() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    includes = set(pyproject["tool"]["hatch"]["build"]["targets"]["sdist"]["include"])
    for name in README_NAMES:
        assert f"/{name}" in includes
    assert "/docs" in includes or "/docs/assets" in includes


def test_docs_checker_detects_broken_local_image(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("![missing local image](docs/assets/missing.png)\n", encoding="utf-8")
    failures = check_docs.local_path_failures(tmp_path, readme)
    assert failures == ["README.md: broken image docs/assets/missing.png"]
