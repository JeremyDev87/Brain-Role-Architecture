from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from brain_role.compiled_loader import validate_compiled_bundle_document
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
        "apiVersion": str(bundle.architecture.get("apiVersion", "brain-role.dev/v1alpha1")),
        "kind": "CompiledBrainRole",
        "metadata": metadata,
        "compileOrder": order,
        "layers": [copy.deepcopy(bundle.layers[layer]) for layer in order],
        "roles": [copy.deepcopy(item) for _, item in sorted(bundle.roles, key=_metadata_sort_key)],
        "policies": [copy.deepcopy(item) for _, item in sorted(bundle.policies, key=_metadata_sort_key)],
    }
    validate_compiled_bundle(document)
    return document


def validate_compiled_bundle(document: Document) -> None:
    validate_compiled_bundle_document(document)


def encode_compiled_bundle(document: Document) -> bytes:
    validate_compiled_bundle(document)
    return _canonical_document_bytes(document) + b"\n"


def write_compiled_bundle(document: Document, output: Path) -> tuple[str, str]:
    encoded = encode_compiled_bundle(document)
    target = atomic_write_bytes(output, encoded)
    return target.name, hashlib.sha256(encoded).hexdigest()
