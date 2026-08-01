from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from brain_role.errors import DuplicateKeyFailure, InputFailure, ValidationIssue
from brain_role.models import Document, InstanceBundle
from brain_role.public_boundary import inspect_text

MAX_FILE_BYTES = 1_000_000
MAX_TOTAL_BYTES = 5_000_000
MAX_NESTING_DEPTH = 32
_REMOTE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")
_DRIVE = re.compile(r"^[A-Za-z]:")


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise yaml.constructor.ConstructorError(
                None,
                None,
                "mapping keys must be hashable",
                key_node.start_mark,
            ) from exc
        if duplicate:
            raise DuplicateKeyFailure("duplicate mapping key")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


def _depth(value: Any, current: int = 0) -> int:
    if isinstance(value, dict):
        return max([current, *(_depth(v, current + 1) for v in value.values())])
    if isinstance(value, list):
        return max([current, *(_depth(v, current + 1) for v in value)])
    return current


def _contained(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def _report_path(reference: str) -> str:
    return "<reference>" if inspect_text(reference) else reference


def resolve_reference(root: Path, reference: str) -> tuple[Path | None, ValidationIssue | None]:
    generic = "reference must be a contained local regular YAML file"
    if (
        not reference
        or _REMOTE.match(reference)
        or _DRIVE.match(reference)
        or "\\" in reference
        or Path(reference).is_absolute()
        or ".." in Path(reference).parts
    ):
        return None, ValidationIssue("<reference>", "E_REF_BOUNDARY", "", generic)
    candidate = root.joinpath(reference)
    try:
        resolved_root = root.resolve(strict=True)
        resolved = candidate.resolve(strict=True)
    except OSError:
        return None, ValidationIssue(_report_path(reference), "E_REF_MISSING", "", "referenced file does not exist")
    if not _contained(resolved_root, resolved):
        return None, ValidationIssue("<reference>", "E_REF_BOUNDARY", "", generic)
    cursor = resolved_root
    for part in Path(reference).parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return None, ValidationIssue(
                _report_path(reference), "E_REF_SYMLINK", "", "symlink references are forbidden"
            )
    if not resolved.is_file():
        return None, ValidationIssue(_report_path(reference), "E_REF_TYPE", "", "reference is not a regular file")
    return resolved, None


def load_yaml(root: Path, reference: str) -> tuple[Document | None, ValidationIssue | None, int]:
    path, issue = resolve_reference(root, reference)
    if issue is not None or path is None:
        return None, issue, 0
    try:
        size = path.stat().st_size
    except OSError:
        return None, ValidationIssue(_report_path(reference), "E_IO", "", "unable to inspect referenced file"), 0
    if size > MAX_FILE_BYTES:
        return None, ValidationIssue(_report_path(reference), "E_LIMIT_FILE", "", "file exceeds size limit"), size
    try:
        text = path.read_text(encoding="utf-8")
        value = yaml.load(text, Loader=UniqueKeyLoader)
    except UnicodeError:
        return None, ValidationIssue(_report_path(reference), "E_ENCODING", "", "file must be UTF-8"), size
    except DuplicateKeyFailure:
        return None, ValidationIssue(_report_path(reference), "E_YAML_DUPLICATE_KEY", "", "duplicate YAML key"), size
    except yaml.YAMLError:
        return None, ValidationIssue(_report_path(reference), "E_YAML_PARSE", "", "invalid YAML"), size
    except OSError:
        return None, ValidationIssue(_report_path(reference), "E_IO", "", "unable to read referenced file"), size
    if not isinstance(value, dict):
        return (
            None,
            ValidationIssue(_report_path(reference), "E_DOCUMENT_TYPE", "", "document root must be an object"),
            size,
        )
    if _depth(value) > MAX_NESTING_DEPTH:
        return (
            None,
            ValidationIssue(_report_path(reference), "E_LIMIT_DEPTH", "", "document exceeds nesting limit"),
            size,
        )
    return value, None, size


def load_instance(input_path: Path) -> tuple[InstanceBundle | None, list[ValidationIssue]]:
    try:
        supplied = input_path.expanduser()
        if not supplied.exists():
            raise InputFailure("input does not exist")
        if supplied.is_symlink():
            raise InputFailure("input symlink is forbidden")
        if supplied.is_dir():
            root = supplied.resolve(strict=True)
            architecture_ref = "architecture.yaml"
        elif supplied.is_file():
            root = supplied.parent.resolve(strict=True)
            architecture_ref = supplied.name
        else:
            raise InputFailure("input is not a regular file or directory")
    except OSError as exc:
        raise InputFailure("unable to inspect input") from exc

    architecture, issue, total = load_yaml(root, architecture_ref)
    if issue is not None or architecture is None:
        return None, [issue] if issue is not None else []
    bundle = InstanceBundle(root=root, architecture=architecture, architecture_path=_report_path(architecture_ref))
    issues: list[ValidationIssue] = []

    refs: list[tuple[str, str]] = []
    for key, expected_kind in (("layers", "LayerManifest"), ("roles", "RoleManifest"), ("policies", "PolicyManifest")):
        value = architecture.get(key, [])
        if isinstance(value, list):
            refs.extend((ref, expected_kind) for ref in value if isinstance(ref, str))
    compile_ref = architecture.get("compileOrder")
    if isinstance(compile_ref, str):
        refs.append((compile_ref, "CompileOrder"))

    seen_refs: set[str] = set()
    for ref, expected_kind in refs:
        report_path = _report_path(ref)
        if ref in seen_refs:
            issues.append(ValidationIssue(report_path, "E_REF_DUPLICATE", "", "reference is declared more than once"))
            continue
        seen_refs.add(ref)
        document, ref_issue, size = load_yaml(root, ref)
        total += size
        if total > MAX_TOTAL_BYTES:
            issues.append(ValidationIssue(report_path, "E_LIMIT_TOTAL", "", "instance exceeds total size limit"))
            break
        if ref_issue is not None or document is None:
            if ref_issue is not None:
                issues.append(ref_issue)
            continue
        actual_kind = document.get("kind")
        if actual_kind != expected_kind:
            issues.append(ValidationIssue(report_path, "E_KIND", "/kind", f"expected {expected_kind}"))
            continue
        if expected_kind == "LayerManifest":
            layer_id = document.get("spec", {}).get("layer") if isinstance(document.get("spec"), dict) else None
            if isinstance(layer_id, str):
                if layer_id in bundle.layers:
                    issues.append(
                        ValidationIssue(
                            report_path, "E_LAYER_DUPLICATE", "/spec/layer", "layer is declared more than once"
                        )
                    )
                else:
                    bundle.layers[layer_id] = document
                    bundle.layer_paths[layer_id] = report_path
        elif expected_kind == "RoleManifest":
            bundle.roles.append((report_path, document))
        elif expected_kind == "PolicyManifest":
            bundle.policies.append((report_path, document))
        else:
            bundle.compile_order = document
            bundle.compile_order_path = report_path
    return bundle, issues
