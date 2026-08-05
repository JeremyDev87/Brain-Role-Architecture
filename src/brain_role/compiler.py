from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from brain_role.errors import InputFailure
from brain_role.models import Document, InstanceBundle
from brain_role.output_safety import atomic_write_bytes


def _canonical_document_bytes(document: Document) -> bytes:
    return json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _metadata_sort_key(document: tuple[str, Document]) -> tuple[str, bytes]:
    metadata = document[1].get("metadata", {})
    identifier = str(metadata.get("id", "")) if isinstance(metadata, dict) else ""
    return identifier, _canonical_document_bytes(document[1])


def compile_bundle(bundle: InstanceBundle) -> Document:
    order_value = bundle.compile_order.get("order", [])
    order = [str(layer) for layer in order_value] if isinstance(order_value, list) else []
    metadata_value = bundle.architecture.get("metadata", {})
    metadata: dict[str, Any] = copy.deepcopy(metadata_value) if isinstance(metadata_value, dict) else {}
    document: Document = {
        "apiVersion": "brain-role.dev/v1alpha1",
        "kind": "CompiledBrainRole",
        "metadata": metadata,
        "compileOrder": order,
        "layers": [copy.deepcopy(bundle.layers[layer]) for layer in order],
        "roles": [copy.deepcopy(item) for _, item in sorted(bundle.roles, key=_metadata_sort_key)],
        "policies": [copy.deepcopy(item) for _, item in sorted(bundle.policies, key=_metadata_sort_key)],
    }
    validate_compiled_bundle(document)
    return document


def _document_identifier(document: object) -> str:
    if not isinstance(document, dict):
        return ""
    metadata = document.get("metadata", {})
    return str(metadata.get("id", "")) if isinstance(metadata, dict) else ""


def validate_compiled_bundle(document: Document) -> None:
    order = document.get("compileOrder")
    layers = document.get("layers")
    roles = document.get("roles")
    policies = document.get("policies")
    expected_layers = {"P0", "P1", "P2", "P3", "P4", "P5", "P6"}
    if (
        not isinstance(order, list)
        or not all(isinstance(layer, str) for layer in order)
        or len(order) != 7
        or set(order) != expected_layers
        or order[0] != "P0"
    ):
        raise InputFailure("compiled bundle has an invalid compile order")
    if not isinstance(layers, list):
        raise InputFailure("compiled bundle has invalid layers")
    layer_order: list[str] = []
    layer_dependencies: list[list[str]] = []
    for layer in layers:
        if not isinstance(layer, dict):
            raise InputFailure("compiled bundle has invalid layers")
        spec = layer.get("spec", {})
        if not isinstance(spec, dict):
            raise InputFailure("compiled bundle has invalid layers")
        layer_order.append(str(spec.get("layer", "")))
        dependencies = spec.get("dependencies", [])
        if not isinstance(dependencies, list) or not all(isinstance(item, str) for item in dependencies):
            raise InputFailure("compiled bundle has invalid layer dependencies")
        layer_dependencies.append(dependencies)
    if layer_order != order:
        raise InputFailure("compiled layers do not match compile order")
    compiled_layers: set[str] = set()
    for layer, dependencies in zip(layer_order, layer_dependencies, strict=True):
        if any(dependency not in compiled_layers for dependency in dependencies):
            raise InputFailure("compiled layer order violates declared dependencies")
        compiled_layers.add(layer)
    for name, values in (("roles", roles), ("policies", policies)):
        if not isinstance(values, list):
            raise InputFailure(f"compiled bundle has invalid {name}")
        identifiers = [_document_identifier(value) for value in values]
        if not all(identifiers) or len(set(identifiers)) != len(identifiers):
            raise InputFailure(f"compiled {name} metadata.id values must be unique")
        if identifiers != sorted(identifiers):
            raise InputFailure(f"compiled {name} are not sorted by metadata.id")


def encode_compiled_bundle(document: Document) -> bytes:
    validate_compiled_bundle(document)
    return _canonical_document_bytes(document) + b"\n"


def write_compiled_bundle(document: Document, output: Path) -> tuple[str, str]:
    encoded = encode_compiled_bundle(document)
    target = atomic_write_bytes(output, encoded)
    return target.name, hashlib.sha256(encoded).hexdigest()
