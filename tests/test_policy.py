from __future__ import annotations

from pathlib import Path

import pytest
from conftest import load_yaml, save_yaml

from brain_role.public_boundary import is_allowed_reference
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
        "http" + "://2130706433/admin",
        "http" + "://0177.0.0.1/admin",
        "http" + "://0x7f000001/admin",
        "http" + "://127.1/admin",
        "http" + "://1.2.3.4.5/admin",
        "http" + "://0x7g/admin",
        "http" + "://%6cocalhost/admin",
        "http" + "://%256cocalhost/admin",
        "https" + "://\uff11\uff12\uff17\u3002\uff10\u3002\uff10\u3002\uff11/admin",
        "https" + "://127\u30020\u30020\u30021/admin",
        "https" + "://\uff4c\uff4f\uff43\uff41\uff4c\uff48\uff4f\uff53\uff54/admin",
        "https" + "://\u24db\u24de\u24d2\u24d0\u24db\u24d7\u24de\u24e2\u24e3/admin",
        "http" + "://localhost%2e/admin",
        "http" + "://service.local%2e/admin",
        "env" + "://" + "https" + "://" + "user" + ":" + "password" + "@localhost/admin",
        "env" + "://" + "https" + "://" + "localhost/admin",
        "ENV" + "://127.0.0.1/admin",
        "^" + "https" + "://localhost/admin",
        "https" + "://localhost%3A443/admin",
        "https" + "://localhost%00.example.com/admin",
        "https" + "://\t127.0.0.1/admin",
        "https" + "://\n127.0.0.1/admin",
        "http" + r":\\127.0.0.1\admin",
        "http" + r":\127.0.0.1\admin",
        "http" + ":/127.0.0.1/admin",
        "http" + ":127.0.0.1/admin",
        "http" + "://[::1/admin",
        "https" + ":///missing-host",
        "https" + "://example.com:99999/path",
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


def test_only_normative_env_reference_shape_is_allowed() -> None:
    assert is_allowed_reference("env" + "://VARIABLE_NAME")
    assert not is_allowed_reference("ENV" + "://VARIABLE_NAME")
    assert not is_allowed_reference("env" + "://" + "https" + "://localhost/admin")


@pytest.mark.parametrize(
    "value",
    [
        "https" + "://localhost.example.com/health",
        "https" + "://127.0.0.1.example.com/health",
        "https" + "://example.com:443/health",
        "[https" + "://example.com]",
        "https" + "://\u4f8b\u3048.\u30c6\u30b9\u30c8/health",
        "[" + "https" + "://[2606:4700:4700::1111]]",
        "https" + "://0x7f000001.example.com/health",
        "https" + "://\texample.com/health",
        "http" + r":\\example.com\health",
        "http" + r":\example.com\health",
        "http" + ":/example.com/health",
        "http" + ":example.com/health",
    ],
)
def test_public_url_lookalikes_remain_allowed(instance_copy: Path, value: str) -> None:
    target = instance_copy / "roles" / "operator.yaml"
    document = load_yaml(target)
    document["spec"]["purpose"] = value
    save_yaml(target, document)
    result = validate_instance(instance_copy)
    assert "E_PUBLIC_BOUNDARY" not in {issue.code for issue in result.issues}
