from __future__ import annotations

import runpy
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = runpy.run_path(
    str(ROOT / "scripts" / "check_spec_schema_sync.py"),
    run_name="verification_script",
)
extract_requirement_ids = cast(
    Callable[[str], list[str]],
    SCRIPT["extract_requirement_ids"],
)
top_level_test_functions = cast(
    Callable[[Path], set[str]],
    SCRIPT["top_level_test_functions"],
)
collect_pytest_nodeids = cast(
    Callable[[Path], set[str]],
    SCRIPT["collect_pytest_nodeids"],
)
validate_test_reference = cast(
    Callable[[Path, str, str, set[str], dict[Path, set[str]]], None],
    SCRIPT["validate_test_reference"],
)


def test_requirement_parser_accepts_current_and_external_colon_styles() -> None:
    text = "\n".join(
        [
            "- **REQ-P0-001:** current style",
            "- **REQ-ARCH-002**: external-colon style",
        ]
    )
    assert extract_requirement_ids(text) == ["REQ-P0-001", "REQ-ARCH-002"]


@pytest.mark.parametrize(
    "marker",
    [
        "- **REQ-P0-001** missing colon",
        "* **REQ-P0-001:** unsupported bullet",
        "1. **REQ-P0-001:** unsupported numbered item",
        "- **REQ-P0-001:**",
    ],
)
def test_requirement_parser_rejects_malformed_or_unsupported_markers(
    marker: str,
) -> None:
    with pytest.raises(SystemExit, match="malformed or unsupported requirement marker"):
        extract_requirement_ids(marker)


def test_spec_requirements_match_conformance_map() -> None:
    spec_ids = extract_requirement_ids((ROOT / "SPEC.md").read_text(encoding="utf-8"))
    mapping = yaml.safe_load((ROOT / "tests" / "conformance-map.yaml").read_text(encoding="utf-8"))["requirements"]
    collected = collect_pytest_nodeids(ROOT)
    symbols: dict[Path, set[str]] = {}
    assert len(spec_ids) == len(set(spec_ids))
    assert set(spec_ids) == set(mapping)
    assert "REQ-P0-001" in spec_ids
    for reference in mapping.values():
        path_text, symbol = reference.split("::", 1)
        validate_test_reference(ROOT, path_text, symbol, collected, symbols)


def test_test_symbol_discovery_uses_ast_not_strings_or_nested_functions(
    tmp_path: Path,
) -> None:
    path = tmp_path / "test_fake.py"
    path.write_text(
        "\n".join(
            [
                "TEXT = 'def test_in_string('",
                "def helper():",
                "    def test_nested():",
                "        pass",
                "",
            ]
        ),
        encoding="utf-8",
    )
    assert top_level_test_functions(path) == set()


def test_reference_validation_rejects_escape_and_uncollected_file(
    tmp_path: Path,
) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    collected = tests / "test_collected.py"
    collected.write_text("def test_real():\n    pass\n", encoding="utf-8")
    outside = tmp_path / "outside_test.py"
    outside.write_text("def test_real():\n    pass\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="invalid test path"):
        validate_test_reference(
            tmp_path,
            "tests/../outside_test.py",
            "test_real",
            {"tests/../outside_test.py::test_real"},
            {},
        )
    with pytest.raises(SystemExit, match="invalid or uncollected test reference"):
        validate_test_reference(
            tmp_path,
            "tests/test_collected.py",
            "test_real",
            set(),
            {},
        )
