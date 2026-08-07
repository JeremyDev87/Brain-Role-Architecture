from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

from brain_role.errors import DuplicateKeyFailure, InputFailure
from brain_role.loader import MAX_FILE_BYTES, MAX_NESTING_DEPTH, UniqueKeyLoader
from brain_role.models import Document
from brain_role.neural_compiler import validate_connectome
from brain_role.output_safety import atomic_write_bytes
from brain_role.public_boundary import inspect_text
from brain_role.schema_validation import validate_document


def _depth(value: Any, current: int = 0) -> int:
    if isinstance(value, dict):
        return max([current, *(_depth(item, current + 1) for item in value.values())])
    if isinstance(value, list):
        return max([current, *(_depth(item, current + 1) for item in value)])
    return current


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


def _safe_input_file(input_path: Path) -> Path:
    try:
        supplied = input_path.expanduser()
        if not supplied.exists() or not supplied.is_file() or supplied.is_symlink():
            raise InputFailure("input must be a regular non-symlink file")
        if supplied.stat().st_size > MAX_FILE_BYTES:
            raise InputFailure("input exceeds file size limit")
        return supplied.resolve(strict=True)
    except InputFailure:
        raise
    except OSError as exc:
        raise InputFailure("unable to inspect input") from exc


def load_connectome(input_path: Path) -> Document:
    path = _safe_input_file(input_path)

    def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        document: dict[str, Any] = {}
        for key, value in pairs:
            if key in document:
                raise DuplicateKeyFailure("duplicate JSON key")
            document[key] = value
        return document

    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs)
    except (UnicodeError, json.JSONDecodeError, DuplicateKeyFailure, OSError) as exc:
        raise InputFailure("unable to load compiled connectome") from exc
    if not isinstance(value, dict) or _depth(value) > MAX_NESTING_DEPTH:
        raise InputFailure("compiled connectome has invalid structure")
    validate_connectome(value)
    return value


def load_scenario(input_path: Path) -> Document:
    path = _safe_input_file(input_path)
    try:
        value = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    except (UnicodeError, yaml.YAMLError, DuplicateKeyFailure, OSError) as exc:
        raise InputFailure("unable to load activation scenario") from exc
    if not isinstance(value, dict) or _depth(value) > MAX_NESTING_DEPTH:
        raise InputFailure("activation scenario has invalid structure")
    if _has_nonfinite(value) or _has_forbidden_text(value) or validate_document(value, "<scenario>"):
        raise InputFailure("activation scenario does not conform to schema")
    return value


def _canonical_bytes(document: Document) -> bytes:
    return json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _identifier(document: dict[str, Any]) -> str:
    metadata = document.get("metadata", {})
    return str(metadata.get("id", "")) if isinstance(metadata, dict) else ""


def _spec(document: dict[str, Any]) -> dict[str, Any]:
    value = document.get("spec", {})
    return value if isinstance(value, dict) else {}


def _bounded(value: float, minimum: float, maximum: float) -> float:
    return min(maximum, max(minimum, value))


def _phase(clock: dict[str, Any], tick: int) -> dict[str, Any] | None:
    spec = _spec(clock)
    period = int(spec.get("periodTicks", 1))
    position = tick % period
    phases = spec.get("phases", [])
    if not isinstance(phases, list):
        return None
    for phase in phases:
        if not isinstance(phase, dict):
            continue
        start = int(phase.get("startInclusive", 0))
        end = int(phase.get("endExclusive", 0))
        if start <= position < end:
            return phase
    return None


def _apply_effect(base: float, level: float, effect: dict[str, Any]) -> float:
    value = float(effect.get("value", 0.0))
    operation = effect.get("operation")
    if operation == "add":
        candidate = base + value * level
    elif operation == "multiply":
        candidate = base * (1.0 + (value - 1.0) * level)
    else:
        raise InputFailure("unsupported receptor operation")
    return _bounded(candidate, float(effect.get("min", candidate)), float(effect.get("max", candidate)))


def _integrate_signals(
    signals: list[dict[str, Any]],
    strategy: str,
    input_ports: list[dict[str, Any]],
    gain: float,
    threshold: float,
) -> tuple[float, bool]:
    gained = [float(signal.get("amplitude", 0.0)) * gain for signal in signals]
    amplitude = sum(gained)
    if strategy == "any":
        selected = max(gained, default=0.0)
        return selected, selected >= threshold
    if strategy == "all":
        required_ports = {
            str(port.get("name", "")) for port in input_ports if isinstance(port, dict)
        }
        received_ports = {str(signal.get("targetPort", "")) for signal in signals}
        return amplitude, required_ports <= received_ports and amplitude >= threshold
    if strategy == "threshold":
        return amplitude, amplitude >= threshold
    raise InputFailure("unsupported neuron integration strategy")


def simulate_connectome(connectome: Document, scenario: Document) -> Document:
    validate_connectome(connectome)
    issues = validate_document(scenario, "<scenario>")
    if _has_nonfinite(scenario) or _has_forbidden_text(scenario) or issues:
        raise InputFailure("activation scenario does not conform to schema")
    if connectome.get("apiVersion") != scenario.get("apiVersion"):
        raise InputFailure("connectome and scenario apiVersion must match")
    spec = _spec(scenario)
    max_ticks = int(spec.get("maxTicks", 0))
    max_events = int(spec.get("maxEvents", 0))
    neurons = {_identifier(item): item for item in connectome["neurons"]}
    regulators = {_identifier(item): item for item in connectome["regulators"]}
    receptors: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for receptor in connectome["receptors"]:
        receptors[str(_spec(receptor).get("targetNeuron", ""))].append(receptor)
    outgoing: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for synapse in connectome["synapses"]:
        source = _spec(synapse).get("from", {})
        if isinstance(source, dict):
            outgoing[str(source.get("neuron", ""))].append(synapse)
    for values in outgoing.values():
        values.sort(key=_identifier)

    levels = {identifier: float(_spec(item).get("initialLevel", 0.0)) for identifier, item in regulators.items()}
    refreshed_at = {identifier: 0 for identifier in regulators}
    queue: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for signal in spec.get("signals", []):
        if isinstance(signal, dict):
            queue[int(signal.get("tick", 0))].append(dict(signal))
    metrics = {
        (int(item.get("tick", 0)), str(item.get("name", ""))): float(item.get("value", 0.0))
        for item in spec.get("metrics", [])
        if isinstance(item, dict)
    }
    events: list[dict[str, Any]] = []
    sequence = 0

    def emit(tick: int, event_type: str, **fields: Any) -> bool:
        nonlocal sequence
        if len(events) >= max_events:
            return False
        event = {"sequence": sequence, "tick": tick, "type": event_type, **fields}
        events.append(event)
        sequence += 1
        return True

    for proposal in connectome["plasticityProposals"]:
        if not emit(0, "plasticity_proposed", proposal=_identifier(proposal), applied=False):
            break

    termination = "maxTicks"
    for tick in range(max_ticks):
        if len(events) >= max_events:
            termination = "maxEvents"
            break
        if tick:
            for regulator_id, regulator in regulators.items():
                regulator_spec = _spec(regulator)
                minimum = float(regulator_spec.get("minLevel", 0.0))
                ttl_ticks = int(regulator_spec.get("ttlTicks", 1))
                if tick - refreshed_at[regulator_id] >= ttl_ticks:
                    levels[regulator_id] = minimum
                else:
                    decay = float(regulator_spec.get("decayPerTick", 0.0))
                    levels[regulator_id] = max(minimum, levels[regulator_id] - decay)

        for clock in connectome["clocks"]:
            phase = _phase(clock, tick)
            if phase is None:
                continue
            emit(tick, "clock_phase", clock=_identifier(clock), phase=str(phase.get("name", "")))
            regulator_ref = phase.get("regulatorRef")
            if isinstance(regulator_ref, str) and regulator_ref in levels:
                regulator = regulators[regulator_ref]
                level = float(phase.get("level", 0.0))
                levels[regulator_ref] = _bounded(
                    level,
                    float(_spec(regulator).get("minLevel", 0.0)),
                    float(_spec(regulator).get("maxLevel", 1.0)),
                )
                refreshed_at[regulator_ref] = tick

        for homeostat in connectome["homeostats"]:
            homeostat_spec = _spec(homeostat)
            metric_name = str(homeostat_spec.get("metric", ""))
            metric_key = (tick, metric_name)
            if metric_key not in metrics:
                continue
            observed = metrics[metric_key]
            target = homeostat_spec.get("targetRange", {})
            if not isinstance(target, dict):
                continue
            if observed < float(target.get("min", 0.0)):
                selected = float(homeostat_spec.get("belowLevel", 0.0))
                state = "below"
            elif observed > float(target.get("max", 0.0)):
                selected = float(homeostat_spec.get("aboveLevel", 0.0))
                state = "above"
            else:
                selected = float(homeostat_spec.get("normalLevel", 0.0))
                state = "normal"
            regulator_ref = str(homeostat_spec.get("regulatorRef", ""))
            regulator = regulators[regulator_ref]
            levels[regulator_ref] = _bounded(
                selected,
                float(_spec(regulator).get("minLevel", 0.0)),
                float(_spec(regulator).get("maxLevel", 1.0)),
            )
            refreshed_at[regulator_ref] = tick
            emit(
                tick,
                "homeostat_observed",
                homeostat=_identifier(homeostat),
                metric=metric_name,
                observed=observed,
                state=state,
            )

        for regulator_id in sorted(levels):
            emit(tick, "regulator_level", regulator=regulator_id, level=levels[regulator_id])
        for support in connectome["supports"]:
            support_spec = _spec(support)
            actions = support_spec.get("actions", [])
            targets = support_spec.get("targets", [])
            if "observe" in actions:
                emit(tick, "support_observed", support=_identifier(support), actions=actions, targets=targets)
            for action in actions:
                if action == "observe":
                    continue
                emit(
                    tick,
                    "support_action_proposed",
                    support=_identifier(support),
                    action=action,
                    targets=targets,
                    applied=False,
                )
        if len(events) >= max_events:
            termination = "maxEvents"
            break

        arrivals = sorted(
            queue.get(tick, []),
            key=lambda item: (
                str(item.get("targetNeuron", "")),
                str(item.get("targetPort", "")),
                str(item.get("correlationId", "")),
            ),
        )
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for signal in arrivals:
            target_id = str(signal.get("targetNeuron", ""))
            target = neurons.get(target_id)
            if target is None:
                raise InputFailure("scenario targets an unknown neuron")
            input_types = {
                str(port.get("name", "")): str(port.get("signalType", ""))
                for port in _spec(target).get("inputPorts", [])
                if isinstance(port, dict)
            }
            if input_types.get(str(signal.get("targetPort", ""))) != signal.get("signalType"):
                raise InputFailure("scenario targets an incompatible port")
            grouped[target_id].append(signal)

        for neuron_id in sorted(grouped):
            neuron = neurons[neuron_id]
            neuron_spec = _spec(neuron)
            integration = neuron_spec.get("integration", {})
            threshold = float(integration.get("activationThreshold", 1.0))
            strategy = str(integration.get("strategy", ""))
            gain = 1.0
            for receptor in sorted(receptors.get(neuron_id, []), key=_identifier):
                receptor_spec = _spec(receptor)
                regulator_ref = str(receptor_spec.get("regulatorRef", ""))
                level = levels.get(regulator_ref, 0.0)
                if level <= 0:
                    continue
                for effect in receptor_spec.get("effects", []):
                    if not isinstance(effect, dict):
                        continue
                    parameter = str(effect.get("parameter", ""))
                    if parameter == "activationThreshold":
                        threshold = _apply_effect(threshold, level, effect)
                    elif parameter == "signalGain":
                        gain = _apply_effect(gain, level, effect)
                    emit(
                        tick,
                        "receptor_applied",
                        receptor=_identifier(receptor),
                        regulator=regulator_ref,
                        neuron=neuron_id,
                        parameter=parameter,
                        level=level,
                    )
            input_ports = neuron_spec.get("inputPorts", [])
            amplitude, fired = _integrate_signals(
                grouped[neuron_id],
                strategy,
                input_ports if isinstance(input_ports, list) else [],
                gain,
                threshold,
            )
            emit(
                tick,
                "neuron_fired" if fired else "neuron_blocked",
                neuron=neuron_id,
                amplitude=amplitude,
                threshold=threshold,
                integrationStrategy=strategy,
                capabilityRef=str(neuron_spec.get("capabilityRef", "")),
            )
            if not fired:
                continue
            seed = grouped[neuron_id][0]
            for synapse in outgoing.get(neuron_id, []):
                synapse_spec = _spec(synapse)
                target = synapse_spec.get("to", {})
                source = synapse_spec.get("from", {})
                if not isinstance(target, dict) or not isinstance(source, dict):
                    continue
                delivered = amplitude * float(synapse_spec.get("strength", 1.0))
                if synapse_spec.get("effect") == "inhibit":
                    delivered = -delivered
                deliver_tick = tick + int(synapse_spec.get("delayTicks", 1))
                queue[deliver_tick].append(
                    {
                        "tick": deliver_tick,
                        "targetNeuron": target.get("neuron"),
                        "targetPort": target.get("port"),
                        "signalType": synapse_spec.get("signalType"),
                        "amplitude": delivered,
                        "payloadRef": seed.get("payloadRef"),
                        "correlationId": seed.get("correlationId"),
                    }
                )
                emit(
                    tick,
                    "synapse_transmitted",
                    synapse=_identifier(synapse),
                    sourceNeuron=source.get("neuron"),
                    targetNeuron=target.get("neuron"),
                    deliverTick=deliver_tick,
                    amplitude=delivered,
                )

        if len(events) >= max_events:
            termination = "maxEvents"
            break

    trace: Document = {
        "apiVersion": str(scenario.get("apiVersion", connectome.get("apiVersion", "brain-role.dev/v1alpha1"))),
        "kind": "NeuralTrace",
        "metadata": dict(scenario.get("metadata", {})),
        "connectomeSha256": hashlib.sha256(
            _canonical_bytes(connectome) + b"\n"
        ).hexdigest(),
        "termination": termination,
        "events": events,
    }
    if validate_document(trace, "<trace>"):
        raise InputFailure("neural trace does not conform to schema")
    return trace


def encode_trace(document: Document) -> bytes:
    if _has_nonfinite(document) or _has_forbidden_text(document) or validate_document(document, "<trace>"):
        raise InputFailure("neural trace does not conform to schema")
    return _canonical_bytes(document) + b"\n"


def write_trace(document: Document, output: Path) -> tuple[str, str, int]:
    encoded = encode_trace(document)
    target = atomic_write_bytes(output, encoded)
    events = document.get("events", [])
    count = len(events) if isinstance(events, list) else 0
    return target.name, hashlib.sha256(encoded).hexdigest(), count
