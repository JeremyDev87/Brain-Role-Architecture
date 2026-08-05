from __future__ import annotations

from pathlib import Path

from brain_role.errors import InputFailure, ValidationIssue
from brain_role.loader import MAX_TOTAL_BYTES, load_instance, load_yaml, resolve_reference
from brain_role.models import Document
from brain_role.neural_models import NeuralBundle
from brain_role.public_boundary import inspect_text

_COLLECTIONS = {
    "neurons": "NeuronManifest",
    "synapses": "SynapseManifest",
    "regulators": "RegulatorManifest",
    "receptors": "ReceptorBinding",
    "homeostats": "HomeostatManifest",
    "supports": "SupportManifest",
    "clocks": "ClockManifest",
    "plasticityProposals": "PlasticityProposal",
}


def _report_path(reference: str) -> str:
    return "<reference>" if inspect_text(reference) else reference


def _input_root(input_path: Path) -> tuple[Path, str]:
    try:
        supplied = input_path.expanduser()
        if not supplied.exists():
            raise InputFailure("input does not exist")
        if supplied.is_symlink():
            raise InputFailure("input symlink is forbidden")
        if supplied.is_dir():
            return supplied.resolve(strict=True), "neural.yaml"
        if supplied.is_file():
            return supplied.parent.resolve(strict=True), supplied.name
    except OSError as exc:
        raise InputFailure("unable to inspect input") from exc
    raise InputFailure("input is not a regular file or directory")


def load_neural_instance(input_path: Path) -> tuple[NeuralBundle | None, list[ValidationIssue]]:
    root, architecture_ref = _input_root(input_path)
    architecture, issue, total = load_yaml(root, architecture_ref)
    if issue is not None or architecture is None:
        return None, [issue] if issue is not None else []

    issues: list[ValidationIssue] = []
    brain_ref = architecture.get("brainRole")
    if not isinstance(brain_ref, str):
        return None, [
            ValidationIssue(
                _report_path(architecture_ref),
                "E_REF_MISSING",
                "/brainRole",
                "brainRole is required",
            )
        ]
    brain_path, brain_issue = resolve_reference(root, brain_ref)
    if brain_issue is not None or brain_path is None:
        return None, [brain_issue] if brain_issue is not None else []
    brain_role, brain_issues = load_instance(brain_path)
    issues.extend(brain_issues)
    if brain_role is None:
        return None, issues

    documents: dict[str, list[tuple[str, Document]]] = {name: [] for name in _COLLECTIONS}
    seen_refs: set[str] = {brain_ref}
    for collection, expected_kind in _COLLECTIONS.items():
        refs = architecture.get(collection, [])
        if not isinstance(refs, list):
            continue
        for reference in refs:
            if not isinstance(reference, str):
                continue
            report_path = _report_path(reference)
            if reference in seen_refs:
                issues.append(
                    ValidationIssue(report_path, "E_REF_DUPLICATE", "", "reference is declared more than once")
                )
                continue
            seen_refs.add(reference)
            document, ref_issue, size = load_yaml(root, reference)
            total += size
            if total > MAX_TOTAL_BYTES:
                issues.append(
                    ValidationIssue(report_path, "E_LIMIT_TOTAL", "", "neural instance exceeds total size limit")
                )
                break
            if ref_issue is not None or document is None:
                if ref_issue is not None:
                    issues.append(ref_issue)
                continue
            if document.get("kind") != expected_kind:
                issues.append(ValidationIssue(report_path, "E_KIND", "/kind", f"expected {expected_kind}"))
                continue
            documents[collection].append((report_path, document))

    return (
        NeuralBundle(
            root=root,
            architecture=architecture,
            architecture_path=_report_path(architecture_ref),
            brain_role=brain_role,
            documents=documents,
        ),
        issues,
    )
