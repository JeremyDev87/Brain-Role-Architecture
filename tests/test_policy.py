from __future__ import annotations

from pathlib import Path

import pytest
from conftest import load_yaml, save_yaml

from brain_role.validator import validate_instance


def test_role_cannot_write_p0(instance_copy: Path) -> None:
    target = instance_copy / "roles" / "operator.yaml"
    document = load_yaml(target)
    document["spec"]["writeLayers"].append("P0")
    save_yaml(target, document)
    result = validate_instance(instance_copy)
    assert "E_ROLE_P0_WRITE" in {issue.code for issue in result.issues}


def test_role_cannot_write_reserved_layer(instance_copy: Path) -> None:
    target = instance_copy / "roles" / "operator.yaml"
    document = load_yaml(target)
    document["spec"]["writeLayers"].append("P1")
    document["spec"]["forbiddenLayers"].remove("P1")
    save_yaml(target, document)
    result = validate_instance(instance_copy)
    assert "E_ROLE_RESERVED_WRITE" in {issue.code for issue in result.issues}


def test_self_escalation_is_rejected(instance_copy: Path) -> None:
    target = instance_copy / "roles" / "operator.yaml"
    document = load_yaml(target)
    document["spec"]["selfEscalation"] = True
    document["spec"]["escalation"] = "self"
    save_yaml(target, document)
    result = validate_instance(instance_copy)
    codes = {issue.code for issue in result.issues}
    assert "E_ROLE_SELF_ESCALATION" in codes


@pytest.mark.parametrize(
    "value",
    [
        "/" + "Users/example/private",
        "/" + "users/alice/private",
        "c:" + chr(92) + "users" + chr(92) + "alice" + chr(92) + "private",
        "http" + "://127.0.0.1/admin",
        "postgresql" + "://127.0.0.1/database",
        "https" + "://user:password@public.example/path",
        "AKIA" + "A" * 16,
        "glpat-" + "A" * 20,
        "Author" + "ization: Bearer " + "synthetic-bearer-value-123",
    ],
)
def test_private_absolute_path_is_rejected(instance_copy: Path, value: str) -> None:
    target = instance_copy / "roles" / "operator.yaml"
    document = load_yaml(target)
    document["spec"]["purpose"] = value
    save_yaml(target, document)
    result = validate_instance(instance_copy)
    assert "E_PUBLIC_BOUNDARY" in {issue.code for issue in result.issues}


def test_literal_secret_field_is_rejected(instance_copy: Path) -> None:
    target = instance_copy / "roles" / "operator.yaml"
    document = load_yaml(target)
    document["spec"]["token"] = "synthetic-not-a-real-value"
    save_yaml(target, document)
    result = validate_instance(instance_copy)
    codes = {issue.code for issue in result.issues}
    assert {"E_SCHEMA", "E_SECRET_LITERAL"}.issubset(codes)
