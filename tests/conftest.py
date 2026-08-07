from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml


@pytest.fixture
def example_root() -> Path:
    return Path(__file__).resolve().parent / "fixtures" / "legacy-v1alpha1" / "minimal-public"


@pytest.fixture
def anatomical_example_root() -> Path:
    return Path(__file__).resolve().parents[1] / "examples" / "minimal-public"


@pytest.fixture
def instance_copy(tmp_path: Path, example_root: Path) -> Path:
    target = tmp_path / "instance"
    shutil.copytree(example_root, target)
    return target


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def save_yaml(path: Path, value: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def set_pointer(document: dict[str, Any], pointer: str, value: Any) -> None:
    parts = [part.replace("~1", "/").replace("~0", "~") for part in pointer.strip("/").split("/") if part]
    cursor: Any = document
    for part in parts[:-1]:
        cursor = cursor[int(part)] if isinstance(cursor, list) else cursor[part]
    final = parts[-1]
    if value == "__REMOVE__":
        if isinstance(cursor, list):
            cursor.pop(int(final))
        else:
            cursor.pop(final, None)
    elif isinstance(cursor, list):
        cursor[int(final)] = value
    else:
        cursor[final] = value
