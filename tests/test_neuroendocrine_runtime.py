from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

from brain_role.adapters.hermes import render_prefill
from brain_role.compiler import compile_bundle, encode_compiled_bundle
from brain_role.errors import InputFailure
from brain_role.neural_compiler import compile_connectome, encode_connectome
from brain_role.neural_validator import validate_neural_instance
from brain_role.simulation import encode_trace, load_connectome, simulate_connectome
from brain_role.validator import validate_instance


def _write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _metadata(identifier: str) -> dict[str, str]:
    return {"id": identifier, "version": "0.2.0", "classification": "PUBLIC"}


def create_neural_instance(tmp_path: Path, example_root: Path) -> Path:
    root = tmp_path / "neural-instance"
    shutil.copytree(example_root, root)
    manifests = root / "neural"

    neurons = {
        "sensory": {
            "apiVersion": "brain-role.dev/v1alpha1",
            "kind": "NeuronManifest",
            "metadata": _metadata("sensory"),
            "spec": {
                "layer": "P4",
                "roleRef": "synthetic-observer",
                "capabilityRef": "architecture.read",
                "inputPorts": [
                    {"name": "request", "signalType": "task.request/v1"},
                    {"name": "feedback", "signalType": "task.approved/v1"},
                ],
                "outputPorts": [{"name": "signalOut", "signalType": "task.request/v1"}],
                "integration": {"strategy": "any", "activationThreshold": 1.0},
            },
        },
        "planner": {
            "apiVersion": "brain-role.dev/v1alpha1",
            "kind": "NeuronManifest",
            "metadata": _metadata("planner"),
            "spec": {
                "layer": "P4",
                "roleRef": "synthetic-operator",
                "capabilityRef": "workflow.execute",
                "inputPorts": [{"name": "signalIn", "signalType": "task.request/v1"}],
                "outputPorts": [{"name": "result", "signalType": "task.reviewed/v1"}],
                "integration": {"strategy": "any", "activationThreshold": 1.0},
            },
        },
        "reviewer": {
            "apiVersion": "brain-role.dev/v1alpha1",
            "kind": "NeuronManifest",
            "metadata": _metadata("reviewer"),
            "spec": {
                "layer": "P6",
                "roleRef": "synthetic-observer",
                "capabilityRef": "architecture.read",
                "inputPorts": [{"name": "review", "signalType": "task.reviewed/v1"}],
                "outputPorts": [{"name": "approved", "signalType": "task.approved/v1"}],
                "integration": {"strategy": "any", "activationThreshold": 1.0},
            },
        },
    }
    for name, document in neurons.items():
        _write(manifests / f"neuron-{name}.yaml", document)

    synapses = [
        {
            "apiVersion": "brain-role.dev/v1alpha1",
            "kind": "SynapseManifest",
            "metadata": _metadata("sensory-to-planner"),
            "spec": {
                "from": {"neuron": "sensory", "port": "signalOut"},
                "to": {"neuron": "planner", "port": "signalIn"},
                "signalType": "task.request/v1",
                "effect": "excite",
                "strength": 1.0,
                "delayTicks": 1,
            },
        },
        {
            "apiVersion": "brain-role.dev/v1alpha1",
            "kind": "SynapseManifest",
            "metadata": _metadata("planner-to-reviewer"),
            "spec": {
                "from": {"neuron": "planner", "port": "result"},
                "to": {"neuron": "reviewer", "port": "review"},
                "signalType": "task.reviewed/v1",
                "effect": "excite",
                "strength": 1.0,
                "delayTicks": 1,
            },
        },
    ]
    for index, document in enumerate(synapses):
        _write(manifests / f"synapse-{index}.yaml", document)

    _write(
        manifests / "regulator-pressure.yaml",
        {
            "apiVersion": "brain-role.dev/v1alpha1",
            "kind": "RegulatorManifest",
            "metadata": _metadata("resource-pressure"),
            "spec": {
                "class": "hormone",
                "scope": "circuit",
                "initialLevel": 0.0,
                "minLevel": 0.0,
                "maxLevel": 1.0,
                "decayPerTick": 0.25,
                "ttlTicks": 4,
            },
        },
    )
    _write(
        manifests / "receptor-planner.yaml",
        {
            "apiVersion": "brain-role.dev/v1alpha1",
            "kind": "ReceptorBinding",
            "metadata": _metadata("planner-pressure-receptor"),
            "spec": {
                "targetNeuron": "planner",
                "regulatorRef": "resource-pressure",
                "effects": [
                    {
                        "parameter": "activationThreshold",
                        "operation": "add",
                        "value": 1.0,
                        "min": 0.0,
                        "max": 2.0,
                    }
                ],
            },
        },
    )
    _write(
        manifests / "homeostat-queue.yaml",
        {
            "apiVersion": "brain-role.dev/v1alpha1",
            "kind": "HomeostatManifest",
            "metadata": _metadata("queue-controller"),
            "spec": {
                "metric": "queueDepth",
                "targetRange": {"min": 0.0, "max": 5.0},
                "regulatorRef": "resource-pressure",
                "belowLevel": 0.0,
                "normalLevel": 0.0,
                "aboveLevel": 1.0,
            },
        },
    )
    _write(
        manifests / "support-observer.yaml",
        {
            "apiVersion": "brain-role.dev/v1alpha1",
            "kind": "SupportManifest",
            "metadata": _metadata("health-observer"),
            "spec": {
                "class": "anomaly",
                "targets": ["reviewer"],
                "actions": ["observe", "quarantine-propose"],
            },
        },
    )
    _write(
        manifests / "clock-cycle.yaml",
        {
            "apiVersion": "brain-role.dev/v1alpha1",
            "kind": "ClockManifest",
            "metadata": _metadata("logical-cycle"),
            "spec": {
                "periodTicks": 4,
                "phases": [
                    {"name": "active", "startInclusive": 0, "endExclusive": 2},
                    {
                        "name": "maintenance",
                        "startInclusive": 2,
                        "endExclusive": 4,
                        "regulatorRef": "resource-pressure",
                        "level": 0.25,
                    },
                ],
            },
        },
    )
    _write(
        manifests / "plasticity-proposal.yaml",
        {
            "apiVersion": "brain-role.dev/v1alpha1",
            "kind": "PlasticityProposal",
            "metadata": _metadata("reduce-sensory-gain"),
            "spec": {
                "targetSynapse": "sensory-to-planner",
                "change": {"parameter": "strength", "from": 1.0, "to": 0.9},
                "evidence": "synthetic-overactivation-observation",
                "rollback": "restore-strength-1.0",
            },
        },
    )
    _write(
        root / "neural.yaml",
        {
            "apiVersion": "brain-role.dev/v1alpha1",
            "kind": "NeuralArchitecture",
            "metadata": _metadata("synthetic-neuroendocrine-circuit"),
            "brainRole": "architecture.yaml",
            "neurons": [f"neural/neuron-{name}.yaml" for name in reversed(tuple(neurons))],
            "synapses": ["neural/synapse-1.yaml", "neural/synapse-0.yaml"],
            "regulators": ["neural/regulator-pressure.yaml"],
            "receptors": ["neural/receptor-planner.yaml"],
            "homeostats": ["neural/homeostat-queue.yaml"],
            "supports": ["neural/support-observer.yaml"],
            "clocks": ["neural/clock-cycle.yaml"],
            "plasticityProposals": ["neural/plasticity-proposal.yaml"],
        },
    )
    return root


def _scenario() -> dict[str, Any]:
    return {
        "apiVersion": "brain-role.dev/v1alpha1",
        "kind": "ActivationScenario",
        "metadata": _metadata("bounded-pressure-scenario"),
        "spec": {
            "maxTicks": 6,
            "maxEvents": 100,
            "signals": [
                {
                    "tick": 0,
                    "targetNeuron": "sensory",
                    "targetPort": "request",
                    "signalType": "task.request/v1",
                    "amplitude": 1.0,
                    "payloadRef": "synthetic-task-1",
                    "correlationId": "corr-1",
                },
                {
                    "tick": 2,
                    "targetNeuron": "planner",
                    "targetPort": "signalIn",
                    "signalType": "task.request/v1",
                    "amplitude": 1.0,
                    "payloadRef": "synthetic-task-2",
                    "correlationId": "corr-2",
                },
            ],
            "metrics": [
                {"tick": 0, "name": "queueDepth", "value": 10.0},
                {"tick": 1, "name": "queueDepth", "value": 10.0},
                {"tick": 2, "name": "queueDepth", "value": 0.0},
            ],
        },
    }


def test_existing_artifacts_remain_exact_oracles(example_root: Path, tmp_path: Path) -> None:
    result = validate_instance(example_root)
    assert result.valid and result.bundle is not None
    compiled = encode_compiled_bundle(compile_bundle(result.bundle))
    assert len(compiled) == 5592
    assert hashlib.sha256(compiled).hexdigest() == "fe7630cd67f25d5d7e33d9a5e8629f791dcf85a9ad85fbf427a9a95f3fc4044d"
    rendered = tmp_path / "rendered"
    filename, digest = render_prefill(result.bundle, rendered)
    assert filename == "prefill_messages.json"
    assert digest == "6241a63a2f6c8dbc99a044f65d3040a05331cb7926e1ca75d1a2c81c73863a6d"


def test_connectome_is_valid_canonical_and_path_independent(example_root: Path, tmp_path: Path) -> None:
    root = create_neural_instance(tmp_path, example_root)
    result = validate_neural_instance(root)
    assert result.valid, result.issues
    assert result.bundle is not None
    document = compile_connectome(result.bundle)
    first = encode_connectome(document)
    second = encode_connectome(compile_connectome(result.bundle))
    assert first == second
    assert first.endswith(b"\n")
    assert document["kind"] == "CompiledConnectome"
    assert document["brainRole"]["sha256"] == "fe7630cd67f25d5d7e33d9a5e8629f791dcf85a9ad85fbf427a9a95f3fc4044d"
    assert [item["metadata"]["id"] for item in document["neurons"]] == ["planner", "reviewer", "sensory"]
    assert str(root).encode() not in first


def test_semantic_validation_rejects_signal_drift_and_authority_effect(example_root: Path, tmp_path: Path) -> None:
    root = create_neural_instance(tmp_path, example_root)
    synapse = yaml.safe_load((root / "neural/synapse-0.yaml").read_text(encoding="utf-8"))
    synapse["spec"]["signalType"] = "wrong.signal/v1"
    _write(root / "neural/synapse-0.yaml", synapse)
    result = validate_neural_instance(root)
    assert any(issue.code == "E_SIGNAL_TYPE" for issue in result.issues)

    root = create_neural_instance(tmp_path / "second", example_root)
    receptor = yaml.safe_load((root / "neural/receptor-planner.yaml").read_text(encoding="utf-8"))
    receptor["spec"]["effects"][0]["parameter"] = "layer"
    _write(root / "neural/receptor-planner.yaml", receptor)
    result = validate_neural_instance(root)
    assert any(issue.code == "E_SCHEMA" for issue in result.issues)

    root = create_neural_instance(tmp_path / "third", example_root)
    regulator = yaml.safe_load((root / "neural/regulator-pressure.yaml").read_text(encoding="utf-8"))
    regulator["spec"]["minLevel"] = 2.0
    regulator["spec"]["maxLevel"] = 1.0
    _write(root / "neural/regulator-pressure.yaml", regulator)
    result = validate_neural_instance(root)
    assert any(issue.code == "E_REGULATOR_BOUNDS" for issue in result.issues)

    root = create_neural_instance(tmp_path / "fourth", example_root)
    synapse = yaml.safe_load((root / "neural/synapse-0.yaml").read_text(encoding="utf-8"))
    synapse["spec"]["gateRef"] = "unimplemented-gate"
    _write(root / "neural/synapse-0.yaml", synapse)
    result = validate_neural_instance(root)
    assert any(issue.code == "E_SCHEMA" for issue in result.issues)

    root = create_neural_instance(tmp_path / "fifth", example_root)
    regulator = yaml.safe_load((root / "neural/regulator-pressure.yaml").read_text(encoding="utf-8"))
    regulator["spec"]["initialLevel"] = float("nan")
    _write(root / "neural/regulator-pressure.yaml", regulator)
    result = validate_neural_instance(root)
    assert any(issue.code == "E_NUMBER_FINITE" for issue in result.issues)


def test_receptor_homeostat_clock_and_support_change_bounded_trace(example_root: Path, tmp_path: Path) -> None:
    root = create_neural_instance(tmp_path, example_root)
    result = validate_neural_instance(root)
    assert result.valid and result.bundle is not None
    connectome = compile_connectome(result.bundle)
    before = encode_connectome(connectome)
    trace = simulate_connectome(connectome, _scenario())
    assert encode_trace(trace) == encode_trace(simulate_connectome(connectome, _scenario()))
    assert encode_connectome(connectome) == before
    event_types = {event["type"] for event in trace["events"]}
    assert {
        "clock_phase",
        "homeostat_observed",
        "regulator_level",
        "receptor_applied",
        "neuron_blocked",
        "neuron_fired",
        "synapse_transmitted",
        "support_observed",
        "plasticity_proposed",
    } <= event_types
    blocked = [event for event in trace["events"] if event["type"] == "neuron_blocked"]
    fired = [event for event in trace["events"] if event["type"] == "neuron_fired"]
    assert any(event["tick"] == 1 and event["neuron"] == "planner" for event in blocked)
    assert any(event["tick"] == 2 and event["neuron"] == "planner" for event in fired)
    assert all(
        event.get("applied", False) is False
        for event in trace["events"]
        if event["type"] == "plasticity_proposed"
    )


def test_integration_strategies_have_distinct_runtime_semantics(example_root: Path, tmp_path: Path) -> None:
    root = create_neural_instance(tmp_path, example_root)
    result = validate_neural_instance(root)
    assert result.valid and result.bundle is not None
    base = compile_connectome(result.bundle)
    base["regulators"] = []
    base["receptors"] = []
    base["homeostats"] = []
    base["supports"] = []
    base["clocks"] = []
    base["plasticityProposals"] = []
    sensory = next(item for item in base["neurons"] if item["metadata"]["id"] == "sensory")

    def signal(port: str, signal_type: str, amplitude: float, suffix: str) -> dict[str, Any]:
        return {
            "tick": 0,
            "targetNeuron": "sensory",
            "targetPort": port,
            "signalType": signal_type,
            "amplitude": amplitude,
            "payloadRef": f"synthetic-{suffix}",
            "correlationId": f"corr-{suffix}",
        }

    def run(strategy: str, signals: list[dict[str, Any]]) -> dict[str, Any]:
        sensory["spec"]["integration"]["strategy"] = strategy
        scenario = _scenario()
        scenario["spec"].update({"maxTicks": 1, "signals": signals, "metrics": []})
        trace = simulate_connectome(base, scenario)
        return next(event for event in trace["events"] if event.get("neuron") == "sensory")

    split = [
        signal("request", "task.request/v1", 0.6, "one"),
        signal("request", "task.request/v1", 0.6, "two"),
    ]
    any_event = run("any", split)
    threshold_event = run("threshold", split)
    assert any_event["type"] == "neuron_blocked"
    assert any_event["integrationStrategy"] == "any"
    assert any_event["amplitude"] == 0.6
    assert threshold_event["type"] == "neuron_fired"
    assert threshold_event["integrationStrategy"] == "threshold"
    assert threshold_event["amplitude"] == 1.2

    missing_port = run("all", [signal("request", "task.request/v1", 2.0, "request-only")])
    all_ports = run(
        "all",
        [
            signal("request", "task.request/v1", 0.5, "request"),
            signal("feedback", "task.approved/v1", 0.5, "feedback"),
        ],
    )
    assert missing_port["type"] == "neuron_blocked"
    assert all_ports["type"] == "neuron_fired"
    assert all_ports["integrationStrategy"] == "all"


def test_support_non_observe_actions_are_proposal_only(example_root: Path, tmp_path: Path) -> None:
    root = create_neural_instance(tmp_path, example_root)
    result = validate_neural_instance(root)
    assert result.valid and result.bundle is not None
    connectome = compile_connectome(result.bundle)
    connectome["plasticityProposals"] = []
    connectome["supports"][0]["spec"]["actions"] = [
        "throttle",
        "retry",
        "quarantine-propose",
    ]
    scenario = _scenario()
    scenario["spec"].update({"maxTicks": 1, "maxEvents": 100, "signals": [], "metrics": []})
    trace = simulate_connectome(connectome, scenario)
    proposals = [event for event in trace["events"] if event["type"] == "support_action_proposed"]
    assert [event["action"] for event in proposals] == ["throttle", "retry", "quarantine-propose"]
    assert all(event["applied"] is False for event in proposals)
    assert all(event["targets"] == ["reviewer"] for event in proposals)
    assert not any(event["type"] == "support_observed" for event in trace["events"])


@pytest.mark.parametrize("mutation", ["applied-true", "applied-missing"])
def test_support_proposal_trace_rejects_forged_application_evidence(
    example_root: Path,
    tmp_path: Path,
    mutation: str,
) -> None:
    root = create_neural_instance(tmp_path, example_root)
    result = validate_neural_instance(root)
    assert result.valid and result.bundle is not None
    connectome = compile_connectome(result.bundle)
    connectome["plasticityProposals"] = []
    connectome["supports"][0]["spec"]["actions"] = ["throttle"]
    scenario = _scenario()
    scenario["spec"].update({"maxTicks": 1, "maxEvents": 100, "signals": [], "metrics": []})
    trace = simulate_connectome(connectome, scenario)
    proposal = next(event for event in trace["events"] if event["type"] == "support_action_proposed")
    if mutation == "applied-true":
        proposal["applied"] = True
    else:
        del proposal["applied"]
    with pytest.raises(InputFailure, match="neural trace does not conform to schema"):
        encode_trace(trace)


def test_regulator_without_receptor_has_no_effect(example_root: Path, tmp_path: Path) -> None:
    root = create_neural_instance(tmp_path, example_root)
    architecture = yaml.safe_load((root / "neural.yaml").read_text(encoding="utf-8"))
    architecture["receptors"] = []
    _write(root / "neural.yaml", architecture)
    result = validate_neural_instance(root)
    assert result.valid and result.bundle is not None
    trace = simulate_connectome(compile_connectome(result.bundle), _scenario())
    assert not any(event["type"] == "receptor_applied" for event in trace["events"])
    assert any(
        event["type"] == "neuron_fired" and event["tick"] == 1 and event["neuron"] == "planner"
        for event in trace["events"]
    )


def test_directed_cycle_terminates_at_explicit_tick_bound(example_root: Path, tmp_path: Path) -> None:
    root = create_neural_instance(tmp_path, example_root)
    feedback = {
        "apiVersion": "brain-role.dev/v1alpha1",
        "kind": "SynapseManifest",
        "metadata": _metadata("reviewer-to-sensory"),
        "spec": {
            "from": {"neuron": "reviewer", "port": "approved"},
            "to": {"neuron": "sensory", "port": "feedback"},
            "signalType": "task.approved/v1",
            "effect": "excite",
            "strength": 1.0,
            "delayTicks": 1,
        },
    }
    _write(root / "neural/synapse-feedback.yaml", feedback)
    architecture = yaml.safe_load((root / "neural.yaml").read_text(encoding="utf-8"))
    architecture["synapses"].append("neural/synapse-feedback.yaml")
    _write(root / "neural.yaml", architecture)
    result = validate_neural_instance(root)
    assert result.valid and result.bundle is not None
    trace = simulate_connectome(compile_connectome(result.bundle), _scenario())
    assert len(trace["events"]) <= 100
    assert max(event["tick"] for event in trace["events"]) < 6
    assert trace["termination"] == "maxTicks"


def test_loaded_connectome_rejects_forged_nested_manifest(example_root: Path, tmp_path: Path) -> None:
    root = create_neural_instance(tmp_path, example_root)
    result = validate_neural_instance(root)
    assert result.valid and result.bundle is not None
    connectome = compile_connectome(result.bundle)
    connectome["neurons"][0]["kind"] = "PolicyManifest"
    artifact = tmp_path / "forged-connectome.json"
    artifact.write_text(json.dumps(connectome, sort_keys=True), encoding="utf-8")
    with pytest.raises(InputFailure):
        load_connectome(artifact)

    valid = compile_connectome(result.bundle)
    mutations = (
        lambda item: item["regulators"][0]["spec"].update({"minLevel": 2.0, "maxLevel": 1.0}),
        lambda item: item["receptors"][0]["spec"]["effects"][0].update({"min": 2.0, "max": 1.0}),
        lambda item: item["homeostats"][0]["spec"]["targetRange"].update({"min": 2.0, "max": 1.0}),
        lambda item: item["clocks"][0]["spec"]["phases"][1].update({"startInclusive": 1}),
        lambda item: item["synapses"][0]["spec"].update({"strength": float("nan")}),
        lambda item: item["neurons"][0]["spec"].update({"capabilityRef": "sk-" + "a" * 24}),
        lambda item: item["homeostats"][0]["spec"].update({"regulatorRef": "absent"}),
        lambda item: (
            item["plasticityProposals"].clear(),
            item["synapses"][1]["metadata"].update(
                {"id": item["synapses"][0]["metadata"]["id"]}
            ),
        ),
        lambda item: item["neurons"][0]["spec"]["inputPorts"].append(
            dict(item["neurons"][0]["spec"]["inputPorts"][0])
        ),
        lambda item: item["synapses"][1].update(
            {"spec": json.loads(json.dumps(item["synapses"][0]["spec"]))}
        ),
    )
    for index, mutate in enumerate(mutations):
        forged = json.loads(json.dumps(valid))
        mutate(forged)
        forged["synapses"].sort(
            key=lambda document: (
                document["spec"]["from"]["neuron"],
                document["spec"]["from"]["port"],
                document["spec"]["to"]["neuron"],
                document["spec"]["to"]["port"],
                document["metadata"]["id"],
            )
        )
        artifact = tmp_path / f"forged-bounds-{index}.json"
        artifact.write_text(json.dumps(forged, sort_keys=True), encoding="utf-8")
        with pytest.raises(InputFailure):
            load_connectome(artifact)


def test_regulator_ttl_expires_without_refresh(example_root: Path, tmp_path: Path) -> None:
    root = create_neural_instance(tmp_path, example_root)
    result = validate_neural_instance(root)
    assert result.valid and result.bundle is not None
    connectome = compile_connectome(result.bundle)
    connectome["homeostats"] = []
    connectome["clocks"] = []
    connectome["regulators"][0]["spec"].update(
        {"initialLevel": 1.0, "decayPerTick": 0.0, "ttlTicks": 2}
    )
    scenario = _scenario()
    scenario["spec"]["signals"] = [
        {
            "tick": tick,
            "targetNeuron": "planner",
            "targetPort": "signalIn",
            "signalType": "task.request/v1",
            "amplitude": 1.0,
            "payloadRef": f"synthetic-task-{tick}",
            "correlationId": f"corr-{tick}",
        }
        for tick in (0, 2)
    ]
    scenario["spec"]["metrics"] = []
    trace = simulate_connectome(connectome, scenario)
    assert any(
        event["type"] == "neuron_blocked" and event["neuron"] == "planner" and event["tick"] == 0
        for event in trace["events"]
    )
    assert any(
        event["type"] == "neuron_fired" and event["neuron"] == "planner" and event["tick"] == 2
        for event in trace["events"]
    )


def test_simulation_rejects_nonfinite_scenario(example_root: Path, tmp_path: Path) -> None:
    root = create_neural_instance(tmp_path, example_root)
    result = validate_neural_instance(root)
    assert result.valid and result.bundle is not None
    scenario = _scenario()
    scenario["spec"]["signals"][0]["amplitude"] = float("nan")
    with pytest.raises(InputFailure):
        simulate_connectome(compile_connectome(result.bundle), scenario)

    scenario = _scenario()
    scenario["spec"]["signals"][0]["payloadRef"] = "sk-" + "a" * 24
    with pytest.raises(InputFailure):
        simulate_connectome(compile_connectome(result.bundle), scenario)


def test_exact_event_cap_reports_max_events(example_root: Path, tmp_path: Path) -> None:
    root = create_neural_instance(tmp_path, example_root)
    result = validate_neural_instance(root)
    assert result.valid and result.bundle is not None
    connectome = compile_connectome(result.bundle)
    connectome["plasticityProposals"] = []
    scenario = _scenario()
    scenario["spec"].update({"maxTicks": 1, "maxEvents": 1, "signals": [], "metrics": []})
    trace = simulate_connectome(connectome, scenario)
    assert len(trace["events"]) == 1
    assert trace["termination"] == "maxEvents"


def test_neural_cli_compiles_and_simulates_with_deterministic_receipts(example_root: Path, tmp_path: Path) -> None:
    root = create_neural_instance(tmp_path, example_root)
    scenario = tmp_path / "scenario.yaml"
    _write(scenario, _scenario())
    connectome = tmp_path / "connectome.json"
    trace = tmp_path / "trace.json"

    compile_result = subprocess.run(
        [sys.executable, "-m", "brain_role", "compile-connectome", str(root), "--output", str(connectome)],
        text=True,
        capture_output=True,
        check=False,
    )
    first_bytes = connectome.read_bytes()
    second_compile = subprocess.run(
        [sys.executable, "-m", "brain_role", "compile-connectome", str(root), "--output", str(connectome)],
        text=True,
        capture_output=True,
        check=False,
    )
    digest = hashlib.sha256(first_bytes).hexdigest()
    assert compile_result.returncode == second_compile.returncode == 0
    assert compile_result.stdout == second_compile.stdout == f"CONNECTOME file=connectome.json sha256={digest}\n"
    assert connectome.read_bytes() == first_bytes

    simulate_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "brain_role",
            "simulate",
            str(connectome),
            "--scenario",
            str(scenario),
            "--output",
            str(trace),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    trace_document = json.loads(trace.read_bytes())
    trace_digest = hashlib.sha256(trace.read_bytes()).hexdigest()
    assert simulate_result.returncode == 0
    assert simulate_result.stdout == (
        f"SIMULATED file=trace.json sha256={trace_digest} events={len(trace_document['events'])}\n"
    )
    assert simulate_result.stderr == ""
