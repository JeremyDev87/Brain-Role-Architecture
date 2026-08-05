from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from brain_role.errors import ValidationIssue
from brain_role.graph_validation import validate_graph
from brain_role.neural_loader import load_neural_instance
from brain_role.neural_models import NeuralBundle, NeuralValidationResult
from brain_role.policy_validation import validate_policy
from brain_role.public_boundary import inspect_text, is_allowed_reference, is_sensitive_key
from brain_role.schema_validation import validate_document


def _metadata_id(document: dict[str, Any]) -> str:
    metadata = document.get("metadata", {})
    return str(metadata.get("id", "")) if isinstance(metadata, dict) else ""


def _spec(document: dict[str, Any]) -> dict[str, Any]:
    value = document.get("spec", {})
    return value if isinstance(value, dict) else {}


def _walk(value: Any, pointer: str = "") -> list[tuple[str, str, Any]]:
    found: list[tuple[str, str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            text = str(key)
            segment = "<sensitive-key>" if inspect_text(text) else text.replace("~", "~0").replace("/", "~1")
            child_pointer = f"{pointer}/{segment}"
            found.append((text, child_pointer, child))
            found.extend(_walk(child, child_pointer))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_pointer = f"{pointer}/{index}"
            found.append(("", child_pointer, child))
            found.extend(_walk(child, child_pointer))
    return found


def _public_boundary_issues(path: str, document: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for key, pointer, value in _walk(document):
        if is_sensitive_key(key) and isinstance(value, str) and not is_allowed_reference(value):
            issues.append(ValidationIssue(path, "E_SECRET_LITERAL", pointer, "literal secret fields are forbidden"))
        if isinstance(value, str) and inspect_text(value):
            issues.append(
                ValidationIssue(
                    path,
                    "E_PUBLIC_BOUNDARY",
                    pointer,
                    "private path, URL, or credential-like value is forbidden",
                )
            )
    return issues


def _brain_documents(bundle: NeuralBundle) -> list[tuple[str, dict[str, Any]]]:
    brain = bundle.brain_role
    documents: list[tuple[str, dict[str, Any]]] = [(brain.architecture_path, brain.architecture)]
    documents.extend((brain.layer_paths[layer], document) for layer, document in brain.layers.items())
    documents.extend(brain.roles)
    documents.extend(brain.policies)
    if brain.compile_order_path:
        documents.append((brain.compile_order_path, brain.compile_order))
    return documents


def _neural_documents(bundle: NeuralBundle) -> list[tuple[str, dict[str, Any]]]:
    documents = [(bundle.architecture_path, bundle.architecture)]
    for collection in bundle.documents.values():
        documents.extend(collection)
    return documents


def _ids(
    documents: list[tuple[str, dict[str, Any]]],
    code: str,
    issues: list[ValidationIssue],
) -> dict[str, tuple[str, dict[str, Any]]]:
    found: dict[str, tuple[str, dict[str, Any]]] = {}
    for path, document in documents:
        identifier = _metadata_id(document)
        if not identifier:
            continue
        if identifier in found:
            issues.append(ValidationIssue(path, code, "/metadata/id", "metadata.id is declared more than once"))
        else:
            found[identifier] = (path, document)
    return found


def _ports(document: dict[str, Any], key: str) -> dict[str, str]:
    values = _spec(document).get(key, [])
    if not isinstance(values, list):
        return {}
    result: dict[str, str] = {}
    for value in values:
        if isinstance(value, dict) and isinstance(value.get("name"), str) and isinstance(value.get("signalType"), str):
            result[value["name"]] = value["signalType"]
    return result


def _semantic_issues(bundle: NeuralBundle) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    roles = _ids(bundle.brain_role.roles, "E_ROLE_DUPLICATE", issues)
    neurons = _ids(bundle.collection("neurons"), "E_NEURON_DUPLICATE", issues)
    synapses = _ids(bundle.collection("synapses"), "E_SYNAPSE_ID_DUPLICATE", issues)
    regulators = _ids(bundle.collection("regulators"), "E_REGULATOR_DUPLICATE", issues)
    _ids(bundle.collection("receptors"), "E_RECEPTOR_DUPLICATE", issues)
    _ids(bundle.collection("homeostats"), "E_HOMEOSTAT_DUPLICATE", issues)
    _ids(bundle.collection("supports"), "E_SUPPORT_DUPLICATE", issues)
    _ids(bundle.collection("clocks"), "E_CLOCK_DUPLICATE", issues)
    _ids(bundle.collection("plasticityProposals"), "E_PLASTICITY_DUPLICATE", issues)

    for path, document in bundle.collection("regulators"):
        spec = _spec(document)
        minimum = spec.get("minLevel")
        initial = spec.get("initialLevel")
        maximum = spec.get("maxLevel")
        if (
            isinstance(minimum, int | float)
            and not isinstance(minimum, bool)
            and isinstance(initial, int | float)
            and not isinstance(initial, bool)
            and isinstance(maximum, int | float)
            and not isinstance(maximum, bool)
        ):
            if not float(minimum) <= float(initial) <= float(maximum):
                issues.append(
                    ValidationIssue(
                        path,
                        "E_REGULATOR_BOUNDS",
                        "/spec",
                        "regulator levels must satisfy minLevel <= initialLevel <= maxLevel",
                    )
                )

    for _neuron_id, (path, document) in neurons.items():
        spec = _spec(document)
        role_ref = spec.get("roleRef")
        role_entry = roles.get(str(role_ref))
        if role_entry is None:
            issues.append(ValidationIssue(path, "E_ROLE_REF", "/spec/roleRef", "neuron references an unknown role"))
            continue
        role_spec = _spec(role_entry[1])
        capabilities = role_spec.get("capabilities", [])
        if spec.get("capabilityRef") not in capabilities:
            issues.append(
                ValidationIssue(path, "E_CAPABILITY_REF", "/spec/capabilityRef", "capability is not granted by role")
            )
        layers = set(role_spec.get("readLayers", [])) | set(role_spec.get("writeLayers", []))
        if spec.get("layer") not in layers:
            issues.append(
                ValidationIssue(path, "E_LAYER_REF", "/spec/layer", "neuron layer is outside its role contract")
            )
        for port_key in ("inputPorts", "outputPorts"):
            values = spec.get(port_key, [])
            if isinstance(values, list):
                names = [item.get("name") for item in values if isinstance(item, dict)]
                if len(names) != len(set(names)):
                    issues.append(
                        ValidationIssue(path, "E_PORT_DUPLICATE", f"/spec/{port_key}", "port names must be unique")
                    )

    identities: set[tuple[str, str, str, str]] = set()
    for path, document in bundle.collection("synapses"):
        spec = _spec(document)
        source = spec.get("from", {})
        target = spec.get("to", {})
        if not isinstance(source, dict) or not isinstance(target, dict):
            continue
        source_id = str(source.get("neuron", ""))
        target_id = str(target.get("neuron", ""))
        source_port = str(source.get("port", ""))
        target_port = str(target.get("port", ""))
        identity = (source_id, source_port, target_id, target_port)
        if identity in identities:
            issues.append(ValidationIssue(path, "E_SYNAPSE_DUPLICATE", "/spec", "synapse tuple is duplicated"))
        identities.add(identity)
        source_entry = neurons.get(source_id)
        target_entry = neurons.get(target_id)
        if source_entry is None or target_entry is None:
            issues.append(ValidationIssue(path, "E_NEURON_REF", "/spec", "synapse references an unknown neuron"))
            continue
        source_type = _ports(source_entry[1], "outputPorts").get(source_port)
        target_type = _ports(target_entry[1], "inputPorts").get(target_port)
        declared = spec.get("signalType")
        if source_type is None or target_type is None:
            issues.append(ValidationIssue(path, "E_PORT_REF", "/spec", "synapse references an unknown port"))
        elif source_type != target_type or declared != source_type:
            issues.append(ValidationIssue(path, "E_SIGNAL_TYPE", "/spec/signalType", "signal types do not match"))

    for path, document in bundle.collection("receptors"):
        spec = _spec(document)
        if spec.get("targetNeuron") not in neurons:
            issues.append(ValidationIssue(path, "E_NEURON_REF", "/spec/targetNeuron", "unknown receptor target"))
        if spec.get("regulatorRef") not in regulators:
            issues.append(ValidationIssue(path, "E_REGULATOR_REF", "/spec/regulatorRef", "unknown regulator"))
        effects = spec.get("effects", [])
        if isinstance(effects, list):
            for index, effect in enumerate(effects):
                if not isinstance(effect, dict):
                    continue
                minimum = effect.get("min")
                maximum = effect.get("max")
                if (
                    isinstance(minimum, int | float)
                    and not isinstance(minimum, bool)
                    and isinstance(maximum, int | float)
                    and not isinstance(maximum, bool)
                    and float(minimum) > float(maximum)
                ):
                    issues.append(
                        ValidationIssue(
                            path,
                            "E_RECEPTOR_BOUNDS",
                            f"/spec/effects/{index}",
                            "receptor effect min must not exceed max",
                        )
                    )

    for path, document in bundle.collection("homeostats"):
        spec = _spec(document)
        if spec.get("regulatorRef") not in regulators:
            issues.append(ValidationIssue(path, "E_REGULATOR_REF", "/spec/regulatorRef", "unknown regulator"))
        target = spec.get("targetRange", {})
        if isinstance(target, dict):
            minimum = target.get("min")
            maximum = target.get("max")
            if (
                isinstance(minimum, int | float)
                and not isinstance(minimum, bool)
                and isinstance(maximum, int | float)
                and not isinstance(maximum, bool)
                and float(minimum) > float(maximum)
            ):
                issues.append(
                    ValidationIssue(
                        path,
                        "E_HOMEOSTAT_RANGE",
                        "/spec/targetRange",
                        "homeostat target min must not exceed max",
                    )
                )

    for path, document in bundle.collection("supports"):
        for target in _spec(document).get("targets", []):
            if target not in neurons:
                issues.append(ValidationIssue(path, "E_NEURON_REF", "/spec/targets", "unknown support target"))

    for path, document in bundle.collection("clocks"):
        spec = _spec(document)
        phases = spec.get("phases", [])
        if isinstance(phases, list):
            previous_end = 0
            period = spec.get("periodTicks")
            for index, phase in enumerate(phases):
                if not isinstance(phase, dict):
                    continue
                start = phase.get("startInclusive")
                end = phase.get("endExclusive")
                if (
                    isinstance(period, int)
                    and isinstance(start, int)
                    and isinstance(end, int)
                    and (start < previous_end or start >= end or end > period)
                ):
                    issues.append(
                        ValidationIssue(
                            path,
                            "E_CLOCK_PHASE",
                            f"/spec/phases/{index}",
                            "clock phases must be ordered, non-overlapping, and within periodTicks",
                        )
                    )
                if isinstance(end, int):
                    previous_end = max(previous_end, end)
                if "regulatorRef" in phase and phase["regulatorRef"] not in regulators:
                    issues.append(
                        ValidationIssue(
                            path,
                            "E_REGULATOR_REF",
                            f"/spec/phases/{index}/regulatorRef",
                            "unknown regulator",
                        )
                    )

    for path, document in bundle.collection("plasticityProposals"):
        if _spec(document).get("targetSynapse") not in synapses:
            issues.append(
                ValidationIssue(path, "E_SYNAPSE_REF", "/spec/targetSynapse", "unknown plasticity target")
            )
    return issues


def validate_neural_instance(input_path: Path) -> NeuralValidationResult:
    bundle, load_issues = load_neural_instance(input_path)
    issues = list(load_issues)
    if bundle is not None:
        for path, document in _brain_documents(bundle):
            issues.extend(validate_document(document, path))
        issues.extend(validate_graph(bundle.brain_role))
        issues.extend(validate_policy(bundle.brain_role))
        for path, document in _neural_documents(bundle):
            issues.extend(validate_document(document, path))
            issues.extend(_public_boundary_issues(path, document))
            for _key, pointer, value in _walk(document):
                if isinstance(value, float) and not math.isfinite(value):
                    issues.append(
                        ValidationIssue(
                            path,
                            "E_NUMBER_FINITE",
                            pointer,
                            "numeric values must be finite",
                        )
                    )
        issues.extend(_semantic_issues(bundle))
    return NeuralValidationResult(tuple(sorted(set(issues))), bundle)
