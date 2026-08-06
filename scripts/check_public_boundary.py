from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

from brain_role.public_boundary import (
    contains_structured_literal_secret,
    inspect_text,
)
from brain_role.public_boundary import (
    is_private_host as _is_private_host,
)

is_private_host = _is_private_host

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {
    ".git",
    ".venv",
    ".artifacts",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".codegraph",
}
PLACEHOLDER = re.compile(r"\{\{[^{}\n]+\}\}")
ALLOWED_BINARY_DIGESTS = {
    "docs/assets/brain-role-meme.png": "b0f01c565ac7493a1e31a4cf70d60a4d5d5a24218963972be65119acd102b6f4",
}


def walk(value: Any) -> list[Any]:
    values = [value]
    if isinstance(value, dict):
        for child in value.values():
            values.extend(walk(child))
    elif isinstance(value, list):
        for child in value:
            values.extend(walk(child))
    return values


def is_github_actions_expression(
    path: Path,
    root: Path,
    text: str,
    start: int,
) -> bool:
    rel = path.relative_to(root)
    return (
        len(rel.parts) >= 3
        and rel.parts[:2] == (".github", "workflows")
        and path.suffix in {".yaml", ".yml"}
        and start > 0
        and text[start - 1] == "$"
    )


def has_structured_literal_secret(path: Path, text: str) -> bool:
    try:
        if path.suffix == ".json":
            return contains_structured_literal_secret(json.loads(text))
        if path.suffix in {".yaml", ".yml"}:
            return contains_structured_literal_secret(yaml.safe_load(text))
    except (json.JSONDecodeError, yaml.YAMLError):
        return False
    return False


def scan(root: Path) -> list[str]:
    findings: list[str] = []
    for path in sorted(root.rglob("*")):
        if any(part in EXCLUDED for part in path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        path_findings = inspect_text(rel)
        display = "<sensitive-path>" if path_findings else rel
        for reason in path_findings:
            findings.append(f"{display}: {reason}")
        if path.is_symlink():
            findings.append(f"{display}: symlink not allowed")
            continue
        if not path.is_file():
            continue
        data = path.read_bytes()
        if b"\x00" in data:
            if hashlib.sha256(data).hexdigest() == ALLOWED_BINARY_DIGESTS.get(rel):
                continue
            findings.append(f"{display}: unscannable binary file")
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            if hashlib.sha256(data).hexdigest() == ALLOWED_BINARY_DIGESTS.get(rel):
                continue
            findings.append(f"{display}: unscannable non-UTF8 file")
            continue
        for reason in inspect_text(text):
            findings.append(f"{display}: {reason}")
        if has_structured_literal_secret(path, text):
            findings.append(f"{display}: credential-like value")
        for match in PLACEHOLDER.finditer(text):
            if not is_github_actions_expression(path, root, text, match.start()):
                findings.append(f"{display}: unresolved template placeholder")
                break
    examples = root / "examples"
    for path in sorted(examples.rglob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        for value in walk(data):
            if isinstance(value, dict) and "classification" in value and value["classification"] != "PUBLIC":
                relative = path.relative_to(root).as_posix()
                display = "<sensitive-path>" if inspect_text(relative) else relative
                findings.append(f"{display}: non-public classification")
    return sorted(set(findings))


def main() -> None:
    findings = scan(ROOT)
    if findings:
        raise SystemExit("PUBLIC_BOUNDARY_FAIL\n" + "\n".join(findings))
    print("PUBLIC_BOUNDARY_OK examples=synthetic-public")


if __name__ == "__main__":
    main()
