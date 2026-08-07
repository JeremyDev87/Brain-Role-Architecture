from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import NoReturn

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = {
    "activation-scenario",
    "architecture",
    "clock",
    "compile-order",
    "compiled-bundle",
    "compiled-connectome",
    "homeostat",
    "layer",
    "neural-architecture",
    "neural-trace",
    "neuron",
    "change-report",
    "plasticity-proposal",
    "policy",
    "receptor-binding",
    "regulator",
    "role",
    "support",
    "synapse",
}
REQUIREMENT_MARKER = re.compile(r"(?m)^\s*-\s+\*\*(REQ-[A-Z0-9]+-[0-9]{3})(?::\*\*|\*\*:)[ \t]+(\S.*)$")
REQUIREMENT_CANDIDATE = re.compile(r"(?m)^\s*(?:[-*+]|[0-9]+[.)])\s+\*\*REQ-")


def fail(message: str) -> NoReturn:
    raise SystemExit(f"SPEC_SCHEMA_SYNC_FAIL: {message}")


def extract_requirement_ids(spec_text: str) -> list[str]:
    matches = REQUIREMENT_MARKER.findall(spec_text)
    candidate_count = len(REQUIREMENT_CANDIDATE.findall(spec_text))
    if candidate_count != len(matches):
        fail("malformed or unsupported requirement marker")
    if not matches:
        fail("no normative requirement markers found")
    return [requirement for requirement, _body in matches]


def top_level_test_functions(path: Path) -> set[str]:
    try:
        tree = ast.parse(
            path.read_text(encoding="utf-8"),
            filename=path.as_posix(),
        )
    except SyntaxError as error:
        fail(f"invalid Python test file: {path.name}: {error.msg}")
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
    }


def collect_pytest_nodeids(root: Path) -> set[str]:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "--color=no",
            "tests",
        ],
        cwd=root,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        fail(f"pytest collection failed: {result.stdout.strip()} {result.stderr.strip()}")
    return {line.split("[", 1)[0] for line in result.stdout.splitlines() if "::" in line}


def validate_test_reference(
    root: Path,
    path_text: str,
    symbol: str,
    collected_nodeids: set[str],
    test_symbols: dict[Path, set[str]],
) -> None:
    relative = Path(path_text)
    tests_root = (root / "tests").resolve()
    test_path = root / relative
    if relative.is_absolute() or ".." in relative.parts or relative.parts[:1] != ("tests",):
        fail(f"invalid test path: {path_text}")
    valid_file = (
        test_path.is_file()
        and not test_path.is_symlink()
        and test_path.suffix == ".py"
        and test_path.name.startswith("test_")
    )
    if not valid_file:
        fail(f"invalid test path: {path_text}")
    try:
        test_path.resolve().relative_to(tests_root)
    except ValueError:
        fail(f"test path escapes tests directory: {path_text}")
    symbols = test_symbols.setdefault(test_path, top_level_test_functions(test_path))
    nodeid = f"{relative.as_posix()}::{symbol}"
    if symbol not in symbols or nodeid not in collected_nodeids:
        fail(f"invalid or uncollected test reference: {nodeid}")


def main() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    package_version = project["project"]["version"]
    compatibility = yaml.safe_load((ROOT / "spec" / "compatibility.yaml").read_text(encoding="utf-8"))
    if package_version != compatibility["packageVersion"] or package_version != compatibility["specVersion"]:
        fail("package/spec compatibility versions differ")
    init_text = (ROOT / "src" / "brain_role" / "__init__.py").read_text(encoding="utf-8")
    if f'__version__ = "{package_version}"' not in init_text:
        fail("runtime version differs")

    paths = sorted((ROOT / "schemas" / "v1alpha1").glob("*.schema.json"))
    names = {path.name.removesuffix(".schema.json") for path in paths}
    if names != SCHEMAS:
        fail(f"schema set differs: {sorted(names)}")
    ids: set[str] = set()
    for path in paths:
        schema = json.loads(path.read_text(encoding="utf-8"))
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            fail(f"wrong JSON Schema draft: {path.name}")
        expected_id = f"https://brain-role.dev/schemas/v1alpha1/{path.name}"
        if schema.get("$id") != expected_id or expected_id in ids:
            fail(f"schema id mismatch or duplicate: {path.name}")
        ids.add(expected_id)
        packaged = ROOT / "src" / "brain_role" / "schemas" / "v1alpha1" / path.name
        if not packaged.is_file() or packaged.read_bytes() != path.read_bytes():
            fail(f"packaged schema drift: {path.name}")

    spec_text = (ROOT / "SPEC.md").read_text(encoding="utf-8")
    requirements = extract_requirement_ids(spec_text)
    if len(requirements) != len(set(requirements)):
        fail("duplicate requirement id")
    mapping = yaml.safe_load((ROOT / "tests" / "conformance-map.yaml").read_text(encoding="utf-8"))["requirements"]
    if set(requirements) != set(mapping):
        missing = sorted(set(requirements) - set(mapping))
        extra = sorted(set(mapping) - set(requirements))
        fail(f"requirement coverage drift missing={missing} extra={extra}")
    collected_nodeids = collect_pytest_nodeids(ROOT)
    test_symbols: dict[Path, set[str]] = {}
    for requirement, reference in mapping.items():
        path_text, symbol = reference.split("::", 1)
        try:
            validate_test_reference(
                ROOT,
                path_text,
                symbol,
                collected_nodeids,
                test_symbols,
            )
        except SystemExit as error:
            fail(f"{requirement}: {error}")
    print(f"SPEC_SCHEMA_SYNC_OK version={package_version} schemas={len(paths)} requirements={len(requirements)}")


if __name__ == "__main__":
    main()
