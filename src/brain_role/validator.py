from __future__ import annotations

from pathlib import Path

from brain_role.graph_validation import validate_graph
from brain_role.loader import load_instance
from brain_role.models import InstanceBundle, ValidationResult
from brain_role.policy_validation import validate_policy
from brain_role.schema_validation import validate_document


def _schema_documents(bundle: InstanceBundle) -> list[tuple[str, dict[str, object]]]:
    documents: list[tuple[str, dict[str, object]]] = [(bundle.architecture_path, bundle.architecture)]
    documents.extend((bundle.layer_paths[layer], document) for layer, document in bundle.layers.items())
    documents.extend(bundle.roles)
    documents.extend(bundle.policies)
    if bundle.compile_order_path:
        documents.append((bundle.compile_order_path, bundle.compile_order))
    return documents


def validate_instance(input_path: Path) -> ValidationResult:
    bundle, load_issues = load_instance(input_path)
    issues = list(load_issues)
    if bundle is not None:
        for path, document in _schema_documents(bundle):
            issues.extend(validate_document(document, path))
        issues.extend(validate_graph(bundle))
        issues.extend(validate_policy(bundle))
    return ValidationResult(tuple(sorted(set(issues))), bundle)
