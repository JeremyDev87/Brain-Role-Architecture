from __future__ import annotations

from pathlib import Path

import pytest
from conftest import load_yaml as load_fixture_yaml
from conftest import save_yaml

from brain_role.loader import load_yaml
from brain_role.schema_validation import validate_document
from brain_role.validator import validate_instance


def test_valid_example_conforms(example_root: Path) -> None:
    result = validate_instance(example_root)
    assert result.valid, [issue.as_dict() for issue in result.issues]


def test_unknown_property_fails_closed(instance_copy: Path) -> None:
    target = instance_copy / "layers" / "p2.yaml"
    document = load_fixture_yaml(target)
    document["spec"]["surprise"] = True
    save_yaml(target, document)
    result = validate_instance(instance_copy)
    assert "E_SCHEMA" in {issue.code for issue in result.issues}


def test_standalone_schema_rejects_mutable_p0(example_root: Path) -> None:
    document, issue, _ = load_yaml(example_root, "layers/p0.yaml")
    assert issue is None and document is not None
    document["spec"]["mutability"] = "controlled"
    codes = {item.code for item in validate_document(document, "layers/p0.yaml")}
    assert "E_SCHEMA" in codes


def test_duplicate_yaml_key_is_rejected(instance_copy: Path) -> None:
    target = instance_copy / "layers" / "p2.yaml"
    target.write_text(
        "apiVersion: brain-role.dev/v1alpha1\nkind: LayerManifest\nkind: RoleManifest\n",
        encoding="utf-8",
    )
    result = validate_instance(instance_copy)
    assert "E_YAML_DUPLICATE_KEY" in {issue.code for issue in result.issues}


@pytest.mark.parametrize(
    ("target_name", "key", "value"),
    [
        ("roles/operator.yaml", "spec", []),
        ("roles/operator.yaml", "readLayers", 42),
        ("layers/p2.yaml", "spec", []),
        ("layers/p0.yaml", "p0Core", [{}]),
        ("policies/p0-protection.yaml", "spec", []),
    ],
)
def test_schema_invalid_documents_return_issues_without_traceback(
    instance_copy: Path,
    target_name: str,
    key: str,
    value: object,
) -> None:
    target = instance_copy / target_name
    document = load_fixture_yaml(target)
    if key == "spec":
        document["spec"] = value
    else:
        document["spec"][key] = value
    save_yaml(target, document)
    result = validate_instance(instance_copy)
    codes = {issue.code for issue in result.issues}
    assert not result.valid
    assert {"E_SCHEMA", "E_LAYER_MISSING"} & codes


def test_unhashable_yaml_key_returns_parse_issue(instance_copy: Path) -> None:
    target = instance_copy / "roles" / "operator.yaml"
    target.write_text("? [a, b]\n: value\n", encoding="utf-8")
    result = validate_instance(instance_copy)
    assert not result.valid
    assert "E_YAML_PARSE" in {issue.code for issue in result.issues}
