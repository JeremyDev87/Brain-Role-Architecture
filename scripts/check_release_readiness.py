from __future__ import annotations

import ast
import tomllib
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
README_NAMES = (
    "README.md",
    "README.ko.md",
    "README.zh-CN.md",
    "README.es.md",
    "README.ja.md",
)


def package_version(root: Path) -> str:
    tree = ast.parse((root / "src" / "brain_role" / "__init__.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets):
            value = ast.literal_eval(node.value)
            if isinstance(value, str):
                return value
    return ""


def check(root: Path) -> list[str]:
    failures: list[str] = []
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    compatibility: Any = yaml.safe_load((root / "spec" / "compatibility.yaml").read_text(encoding="utf-8"))
    project_version = str(pyproject["project"]["version"])
    source_version = package_version(root)
    if not isinstance(compatibility, dict):
        return ["spec/compatibility.yaml: mapping required"]
    versions = {
        "pyproject.toml": project_version,
        "src/brain_role/__init__.py": source_version,
        "spec/compatibility.yaml specVersion": str(compatibility.get("specVersion", "")),
        "spec/compatibility.yaml packageVersion": str(compatibility.get("packageVersion", "")),
    }
    for owner, version in versions.items():
        if version != project_version:
            failures.append(f"{owner}: version {version!r} != {project_version!r}")
    if compatibility.get("status") != "PRE_RELEASE":
        failures.append("spec/compatibility.yaml: status must remain PRE_RELEASE")
    if compatibility.get("publicationAuthority") != "MAINTAINER_APPROVAL_REQUIRED":
        failures.append("spec/compatibility.yaml: publication authority drift")

    required_tokens = {
        "SPEC.md": (f"Specification {project_version}", "Status: **PRE_RELEASE**"),
        "CHANGELOG.md": (
            f"## [{project_version}] - PRE_RELEASE",
            "No tag, release, or registry publication exists yet.",
        ),
        "SECURITY.md": (f"`{project_version}`", "PRE_RELEASE", "Validation does not grant publication authority."),
        "spec/versioning-and-migration.md": ("0.x line is experimental", "P0 semantic changes"),
        "docs/reference/cli.md": (
            "brain-role --version",
            "brain-role validate <instance>",
            "brain-role compile <instance>",
            "brain-role render hermes <instance>",
        ),
        "docs/release-checklist.md": (
            "make verify",
            "fresh wheel",
            "PRE_RELEASE",
            "does not authorize",
        ),
    }
    for relative, tokens in required_tokens.items():
        text = (root / relative).read_text(encoding="utf-8")
        for token in tokens:
            if token not in text:
                failures.append(f"{relative}: release contract missing {token}")
    for name in README_NAMES:
        text = (root / name).read_text(encoding="utf-8")
        for token in (project_version, "PRE_RELEASE", "CHANGELOG.md"):
            if token not in text:
                failures.append(f"{name}: release status missing {token}")

    sdist = set(pyproject["tool"]["hatch"]["build"]["targets"]["sdist"]["include"])
    for path in ("/CHANGELOG.md", "/SECURITY.md", "/SPEC.md", "/spec", "/schemas", "/scripts", "/docs"):
        if path not in sdist:
            failures.append(f"pyproject.toml: sdist missing {path}")
    return sorted(failures)


def main() -> None:
    failures = check(ROOT)
    if failures:
        raise SystemExit("RELEASE_READINESS_FAIL\n" + "\n".join(failures))
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    print(
        f"RELEASE_READINESS_OK version={project['project']['version']} "
        f"status=PRE_RELEASE readmes={len(README_NAMES)}"
    )


if __name__ == "__main__":
    main()