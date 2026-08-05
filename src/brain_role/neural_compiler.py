from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from brain_role.compiler import compile_bundle, encode_compiled_bundle
from brain_role.errors import InputFailure
from brain_role.models import Document
from brain_role.neural_models import NeuralBundle
from brain_role.output_safety import atomic_write_bytes
from brain_role.public_boundary import inspect_text
from brain_role.schema_validation import validate_document

_COLLECTION_KEYS = (
    "neurons",
    "synapses",
    "regulators",
    "receptors",
    "homeostats",
    "supports",
    "clocks",
    "plasticityProposals",
)

_COLLECTION_KINDS = {
    "neurons": "NeuronManifest",
    "synapses": "SynapseManifest",
    "regulators": "RegulatorManifest",
    "receptors": "ReceptorBinding",
    "homeostats": "HomeostatManifest",
    "supports": "SupportManifest",
    "clocks": "ClockManifest",
    "plasticityProposals": "PlasticityProposal",
}


def _has_nonfinite(value: Any) -> bool:
    if isinstance(value, float):
        return not math.isfinite(value)
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


def _canonical_bytes(document: Document) -> bytes:
    return json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _identifier(document: Document) -> str:
    metadata = document.get("metadata", {})
    return str(metadata.get("id", "")) if isinstance(metadata, dict) else ""


def _synapse_key(document: Document) -> tuple[str, str, str, str, str]:
    spec = document.get("spec", {})
    if not isinstance(spec, dict):
        return ("", "", "", "", _identifier(document))
    source = spec.get("from", {})
    target = spec.get("to", {})
    if not isinstance(source, dict) or not isinstance(target, dict):
        return ("", "", "", "", _identifier(document))
    return (
        str(source.get("neuron", "")),
        str(source.get("port", "")),
        str(target.get("neuron", "")),
        str(target.get("port", "")),
        _identifier(document),
    )


def compile_connectome(bundle: NeuralBundle) -> Document:
    compiled_brain = encode_compiled_bundle(compile_bundle(bundle.brain_role))
    metadata_value = bundle.architecture.get("metadata", {})
    metadata: dict[str, Any] = copy.deepcopy(metadata_value) if isinstance(metadata_value, dict) else {}
    architecture_metadata = bundle.brain_role.architecture.get("metadata", {})
    architecture_id = str(architecture_metadata.get("id", "")) if isinstance(architecture_metadata, dict) else ""
    document: Document = {
        "apiVersion": "brain-role.dev/v1alpha1",
        "kind": "CompiledConnectome",
        "metadata": metadata,
        "brainRole": {
            "architectureId": architecture_id,
            "sha256": hashlib.sha256(compiled_brain).hexdigest(),
        },
    }
    for collection in _COLLECTION_KEYS:
        values = [copy.deepcopy(item) for _, item in bundle.collection(collection)]
        key = _synapse_key if collection == "synapses" else _identifier
        document[collection] = sorted(values, key=key)
    validate_connectome(document)
    return document


def validate_connectome(document: Document) -> None:
    if document.get("kind") != "CompiledConnectome":
        raise InputFailure("compiled connectome kind is invalid")
    if _has_nonfinite(document):
        raise InputFailure("compiled connectome contains a non-finite number")
    if _has_forbidden_text(document):
        raise InputFailure("compiled connectome crosses the public boundary")
    issues = validate_document(document, "<compiled-connectome>")
    if issues:
        raise InputFailure("compiled connectome does not conform to schema")
    brain_role = document.get("brainRole", {})
    if not isinstance(brain_role, dict) or len(str(brain_role.get("sha256", ""))) != 64:
        raise InputFailure("compiled connectome authority receipt is invalid")
    for collection in _COLLECTION_KEYS:
        values = document.get(collection)
        if not isinstance(values, list):
            raise InputFailure(f"compiled connectome {collection} is invalid")
        expected_kind = _COLLECTION_KINDS[collection]
        for item in values:
            if not isinstance(item, dict) or item.get("kind") != expected_kind:
                raise InputFailure(f"compiled connectome {collection} contains an invalid kind")
            if validate_document(item, f"<compiled-connectome>/{collection}"):
                raise InputFailure(f"compiled connectome {collection} contains an invalid manifest")
        key = _synapse_key if collection == "synapses" else _identifier
        keys = [key(item) if isinstance(item, dict) else "" for item in values]
        if any(not item for item in keys) or keys != sorted(keys) or len(set(keys)) != len(keys):
            raise InputFailure(f"compiled connectome {collection} is not canonical")
        identifiers = [_identifier(item) if isinstance(item, dict) else "" for item in values]
        if any(not item for item in identifiers) or len(set(identifiers)) != len(identifiers):
            raise InputFailure(f"compiled connectome {collection} has duplicate identifiers")

    neurons = {_identifier(item): item for item in document["neurons"]}
    regulators = {_identifier(item): item for item in document["regulators"]}
    synapses = {_identifier(item): item for item in document["synapses"]}
    for neuron in document["neurons"]:
        for port_key in ("inputPorts", "outputPorts"):
            names = [item["name"] for item in neuron["spec"][port_key]]
            if len(names) != len(set(names)):
                raise InputFailure("compiled connectome neuron has duplicate ports")
    for regulator in document["regulators"]:
        spec = regulator["spec"]
        if not float(spec["minLevel"]) <= float(spec["initialLevel"]) <= float(spec["maxLevel"]):
            raise InputFailure("compiled connectome regulator bounds are invalid")
    synapse_identities: set[tuple[str, str, str, str]] = set()
    for synapse in document["synapses"]:
        spec = synapse["spec"]
        source = spec["from"]
        target = spec["to"]
        identity = (source["neuron"], source["port"], target["neuron"], target["port"])
        if identity in synapse_identities:
            raise InputFailure("compiled connectome has a duplicate synapse tuple")
        synapse_identities.add(identity)
        source_neuron = neurons.get(source["neuron"])
        target_neuron = neurons.get(target["neuron"])
        if source_neuron is None or target_neuron is None:
            raise InputFailure("compiled connectome synapse references an unknown neuron")
        output_types = {item["name"]: item["signalType"] for item in source_neuron["spec"]["outputPorts"]}
        input_types = {item["name"]: item["signalType"] for item in target_neuron["spec"]["inputPorts"]}
        signal_type = spec["signalType"]
        if output_types.get(source["port"]) != signal_type or input_types.get(target["port"]) != signal_type:
            raise InputFailure("compiled connectome synapse has incompatible ports")
    for receptor in document["receptors"]:
        spec = receptor["spec"]
        if spec["targetNeuron"] not in neurons or spec["regulatorRef"] not in regulators:
            raise InputFailure("compiled connectome receptor has an unknown reference")
        if any(float(effect["min"]) > float(effect["max"]) for effect in spec["effects"]):
            raise InputFailure("compiled connectome receptor bounds are invalid")
    for homeostat in document["homeostats"]:
        spec = homeostat["spec"]
        if spec["regulatorRef"] not in regulators:
            raise InputFailure("compiled connectome homeostat has an unknown regulator")
        if float(spec["targetRange"]["min"]) > float(spec["targetRange"]["max"]):
            raise InputFailure("compiled connectome homeostat range is invalid")
    for support in document["supports"]:
        if any(target not in neurons for target in support["spec"]["targets"]):
            raise InputFailure("compiled connectome support has an unknown target")
    for clock in document["clocks"]:
        phases = clock["spec"]["phases"]
        if any(
            "regulatorRef" in phase and phase["regulatorRef"] not in regulators
            for phase in phases
        ):
            raise InputFailure("compiled connectome clock has an unknown regulator")
        period = int(clock["spec"]["periodTicks"])
        previous_end = 0
        for phase in phases:
            start = int(phase["startInclusive"])
            end = int(phase["endExclusive"])
            if start < previous_end or start >= end or end > period:
                raise InputFailure("compiled connectome clock phase is invalid")
            previous_end = end
    for proposal in document["plasticityProposals"]:
        if proposal["spec"]["targetSynapse"] not in synapses:
            raise InputFailure("compiled connectome plasticity proposal has an unknown synapse")


def encode_connectome(document: Document) -> bytes:
    validate_connectome(document)
    return _canonical_bytes(document) + b"\n"


def write_connectome(document: Document, output: Path) -> tuple[str, str]:
    encoded = encode_connectome(document)
    target = atomic_write_bytes(output, encoded)
    return target.name, hashlib.sha256(encoded).hexdigest()
