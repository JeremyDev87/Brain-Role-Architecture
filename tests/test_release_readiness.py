from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]


def load_checker() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "brain_role_check_release_readiness",
        ROOT / "scripts" / "check_release_readiness.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = load_checker()


def test_repository_release_contract_is_consistent() -> None:
    assert checker.check(ROOT) == []


def test_release_checker_detects_version_drift(tmp_path: Path) -> None:
    target = tmp_path / "repository"
    shutil.copytree(
        ROOT,
        target,
        ignore=shutil.ignore_patterns(".git", ".venv", ".artifacts", "__pycache__"),
    )
    pyproject = target / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text(encoding="utf-8").replace('version = "0.3.0"', 'version = "0.3.1"', 1),
        encoding="utf-8",
    )
    failures = checker.check(target)
    assert "src/brain_role/__init__.py: version '0.3.0' != '0.3.1'" in failures


def test_release_checker_requires_compile_cli_contract(tmp_path: Path) -> None:
    target = tmp_path / "repository"
    shutil.copytree(
        ROOT,
        target,
        ignore=shutil.ignore_patterns(".git", ".venv", ".artifacts", "__pycache__"),
    )
    cli_reference = target / "docs" / "reference" / "cli.md"
    cli_reference.write_text(
        cli_reference.read_text(encoding="utf-8").replace("brain-role compile <instance>", "compile omitted"),
        encoding="utf-8",
    )
    assert "docs/reference/cli.md: release contract missing brain-role compile <instance>" in checker.check(target)
