from __future__ import annotations

from pathlib import Path

import pytest
from conftest import load_yaml, save_yaml

from brain_role.validator import validate_instance


@pytest.mark.parametrize(
    "reference",
    [
        "../outside.yaml",
        "https://example.invalid/layer.yaml",
        "/tmp/layer.yaml",
        "C:/" + "Users/example/layer.yaml",
    ],
)
def test_nonlocal_references_are_rejected(instance_copy: Path, reference: str) -> None:
    target = instance_copy / "architecture.yaml"
    document = load_yaml(target)
    document["layers"][1] = reference
    save_yaml(target, document)
    result = validate_instance(instance_copy)
    assert "E_REF_BOUNDARY" in {issue.code for issue in result.issues}


def test_symlink_reference_is_rejected(instance_copy: Path, tmp_path: Path) -> None:
    source = instance_copy / "layers" / "p1.yaml"
    link = instance_copy / "layers" / "linked.yaml"
    try:
        link.symlink_to(source)
    except OSError:
        pytest.skip("symlinks unavailable")
    target = instance_copy / "architecture.yaml"
    document = load_yaml(target)
    document["layers"][1] = "layers/linked.yaml"
    save_yaml(target, document)
    result = validate_instance(instance_copy)
    assert "E_REF_SYMLINK" in {issue.code for issue in result.issues}
