from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from brain_role.errors import DuplicateKeyFailure, InputFailure
from brain_role.layer_contract import contract_for_api_version
from brain_role.loader import MAX_FILE_BYTES, MAX_NESTING_DEPTH
from brain_role.public_boundary import inspect_text
from brain_role.schema_validation import load_schema


@dataclass(frozen=True)
class CompiledBundleArtifact:
    document: dict[str, Any]
    raw_bytes: bytes
    sha256: str
    path: Path


def _depth(value: Any, current: int = 0) -> int:
    if isinstance(value, dict):
        return max([current, *(_depth(item, current + 1) for item in value.values())])
    if isinstance(value, list):
        return max([current, *(_depth(item, current + 1) for item in value)])
    return current


def _has_nonfinite(value: Any) -> bool:
    if isinstance(value, float):
        return value != value or value in (float("inf"), float("-inf"))
    if isinstance(value, dict):
        return any(_has_nonfinite(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_nonfinite(item) for item in value)
    return False


def _has_forbidden_text(value: Any) -> bool:
    if isinstance(value, str):
        return bool(inspect_text(value))
    if isinstance(value, dict):
        return any(bool(inspect_text(str(key))) or _has_forbidden_text(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_has_forbidden_text(item) for item in value)
    return False


def _read_all(descriptor: int, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining > 0:
        chunk = os.read(descriptor, remaining)
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _read_regular_nofollow(input_path: Path) -> tuple[Path, bytes]:
    """Open and read a regular non-symlink file without pathname follow races."""
    try:
        lexical = input_path.expanduser().absolute()
        nofollow = getattr(os, "O_NOFOLLOW", 0)
        directory_flag = getattr(os, "O_DIRECTORY", 0)

        if os.name == "nt" or nofollow == 0:
            cursor = Path(lexical.anchor)
            for part in lexical.parts[1:]:
                cursor = cursor / part
                if cursor.is_symlink():
                    raise InputFailure("input must be a regular non-symlink file")
            if not lexical.exists() or not lexical.is_file() or lexical.is_symlink():
                raise InputFailure("input must be a regular non-symlink file")
            expected = lexical.lstat()
            if not stat.S_ISREG(expected.st_mode):
                raise InputFailure("input must be a regular non-symlink file")
            if expected.st_size > MAX_FILE_BYTES:
                raise InputFailure("input exceeds file size limit")
            with lexical.open("rb") as stream:
                raw_bytes = stream.read(MAX_FILE_BYTES + 1)
                actual = os.fstat(stream.fileno())
            if not stat.S_ISREG(actual.st_mode):
                raise InputFailure("input must be a regular non-symlink file")
            if (actual.st_dev, actual.st_ino) != (expected.st_dev, expected.st_ino):
                raise InputFailure("input changed during load")
            if lexical.is_symlink():
                raise InputFailure("input must be a regular non-symlink file")
            if len(raw_bytes) > MAX_FILE_BYTES or actual.st_size > MAX_FILE_BYTES:
                raise InputFailure("input exceeds file size limit")
            return lexical, raw_bytes

        parts = list(lexical.parts)
        if not parts:
            raise InputFailure("input must be a regular non-symlink file")
        directory_fd = os.open(parts[0], os.O_RDONLY | directory_flag)
        try:
            for part in parts[1:-1]:
                next_fd = os.open(part, os.O_RDONLY | directory_flag | nofollow, dir_fd=directory_fd)
                os.close(directory_fd)
                directory_fd = next_fd
            file_name = parts[-1]
            file_fd = os.open(file_name, os.O_RDONLY | nofollow, dir_fd=directory_fd)
            try:
                info = os.fstat(file_fd)
                if not stat.S_ISREG(info.st_mode):
                    raise InputFailure("input must be a regular non-symlink file")
                if info.st_size > MAX_FILE_BYTES:
                    raise InputFailure("input exceeds file size limit")
                raw_bytes = _read_all(file_fd, int(info.st_size))
                after = os.fstat(file_fd)
                if not stat.S_ISREG(after.st_mode):
                    raise InputFailure("input must be a regular non-symlink file")
                if (after.st_dev, after.st_ino) != (info.st_dev, info.st_ino):
                    raise InputFailure("input changed during load")
                if after.st_size != info.st_size or len(raw_bytes) != info.st_size:
                    raise InputFailure("input changed during load")
                return lexical, raw_bytes
            finally:
                os.close(file_fd)
        finally:
            os.close(directory_fd)
    except InputFailure:
        raise
    except OSError as exc:
        raise InputFailure("unable to inspect input") from exc


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    document: dict[str, Any] = {}
    for key, value in pairs:
        if key in document:
            raise DuplicateKeyFailure("duplicate JSON key")
        document[key] = value
    return document


def _canonical_bytes(document: dict[str, Any]) -> bytes:
    return json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _schema_version(api_version: object) -> str:
    contract = contract_for_api_version(api_version)
    if contract is None:
        raise InputFailure("compiled bundle has an unsupported apiVersion")
    return contract.api_version.rsplit("/", 1)[-1]


def _compiled_validator(version: str) -> Draft202012Validator:
    names = ("compiled-bundle", "layer", "role", "policy")
    schemas = [load_schema(f"{name}.schema.json", version) for name in names]
    resources = [(str(schema["$id"]), Resource.from_contents(schema)) for schema in schemas]
    return Draft202012Validator(
        schemas[0],
        registry=Registry().with_resources(resources),
        format_checker=FormatChecker(),
    )


def validate_compiled_bundle_document(document: dict[str, Any]) -> None:
    if not isinstance(document, dict) or _depth(document) > MAX_NESTING_DEPTH:
        raise InputFailure("compiled bundle has invalid structure")
    if _has_nonfinite(document) or _has_forbidden_text(document):
        raise InputFailure("compiled bundle does not conform to public boundary")
    api_version = document.get("apiVersion")
    version = _schema_version(api_version)
    validator = _compiled_validator(version)
    if list(validator.iter_errors(document)):
        raise InputFailure("compiled bundle does not conform to schema")
    order = document.get("compileOrder")
    layers = document.get("layers")
    roles = document.get("roles")
    policies = document.get("policies")
    contract = contract_for_api_version(api_version)
    if contract is None:
        raise InputFailure("compiled bundle has an unsupported apiVersion")
    expected_layers = set(contract.layers)
    if (
        not isinstance(order, list)
        or not all(isinstance(layer, str) for layer in order)
        or len(order) != 7
        or set(order) != expected_layers
        or order[0] != contract.invariant
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
        identifiers: list[str] = []
        for value in values:
            if not isinstance(value, dict):
                raise InputFailure(f"compiled bundle has invalid {name}")
            metadata = value.get("metadata", {})
            if not isinstance(metadata, dict):
                raise InputFailure(f"compiled bundle has invalid {name}")
            identifiers.append(str(metadata.get("id", "")))
        if not all(identifiers) or len(set(identifiers)) != len(identifiers):
            raise InputFailure(f"compiled {name} metadata.id values must be unique")
        if identifiers != sorted(identifiers):
            raise InputFailure(f"compiled {name} are not sorted by metadata.id")


def load_compiled_bundle(input_path: Path) -> CompiledBundleArtifact:
    path, raw_bytes = _read_regular_nofollow(input_path)
    if len(raw_bytes) > MAX_FILE_BYTES:
        raise InputFailure("input exceeds file size limit")
    try:
        document = json.loads(raw_bytes.decode("utf-8"), object_pairs_hook=_unique_pairs)
    except (UnicodeError, json.JSONDecodeError, DuplicateKeyFailure, OSError) as exc:
        raise InputFailure("unable to load compiled bundle") from exc
    if not isinstance(document, dict) or _depth(document) > MAX_NESTING_DEPTH:
        raise InputFailure("compiled bundle has invalid structure")
    validate_compiled_bundle_document(document)
    if _canonical_bytes(document) + b"\n" != raw_bytes:
        raise InputFailure("compiled bundle is not canonical")
    return CompiledBundleArtifact(
        document=document,
        raw_bytes=raw_bytes,
        sha256=hashlib.sha256(raw_bytes).hexdigest(),
        path=path,
    )
