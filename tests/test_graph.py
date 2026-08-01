from __future__ import annotations

from pathlib import Path

from conftest import load_yaml, save_yaml

from brain_role.validator import validate_instance


def test_dependency_cycle_is_rejected(instance_copy: Path) -> None:
    target = instance_copy / "layers" / "p2.yaml"
    document = load_yaml(target)
    document["spec"]["dependencies"] = ["P4"]
    save_yaml(target, document)
    result = validate_instance(instance_copy)
    assert "E_DEP_CYCLE" in {issue.code for issue in result.issues}


def test_dependency_must_precede_dependent(instance_copy: Path) -> None:
    target = instance_copy / "compile-order.yaml"
    document = load_yaml(target)
    document["order"] = ["P0", "P1", "P4", "P2", "P3", "P6", "P5"]
    save_yaml(target, document)
    result = validate_instance(instance_copy)
    assert "E_COMPILE_DEPENDENCY" in {issue.code for issue in result.issues}


def test_compile_order_is_explicit_not_numeric(example_root: Path) -> None:
    result = validate_instance(example_root)
    assert result.bundle is not None
    assert result.bundle.compile_order["order"] == ["P0", "P1", "P2", "P3", "P4", "P6", "P5"]
    assert result.valid
