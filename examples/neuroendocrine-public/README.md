# Neuroendocrine public example

This synthetic `v1alpha2` example demonstrates the neural runtime as an **orthogonal execution and evidence plane**. It does not let activation, graph position, regulator level, or simulation output create Brain or Role authority.

## Governance projection

The linked Brain bundle uses the anatomical responsibility contract:

`brainstem → cerebellum → hippocampus → amygdala → cerebral-cortex → prefrontal-cortex → default-mode-network`

That list is the explicit compile order for this example, not a runtime pipeline. Brainstem remains the only absolute invariant. Roles grant capabilities and read/write permissions independently of the neural graph.

## Runtime circuit

1. `sensory` receives a synthetic `task.request/v1` signal and emits it through a typed output port.
2. `synapse-0` carries that signal to `planner` with explicit strength and logical delay.
3. `planner` integrates the input only when its capability, Role layer access, threshold, and receptor-modulated gain allow it.
4. `synapse-1` carries the plan to `reviewer`; the reviewer emits the final typed approval signal.
5. The `pressure` **Regulator** is bounded by minimum, initial, maximum, decay, and TTL values.
6. `receptor-planner` is the only path by which pressure can alter planner threshold/gain. A Regulator without a Receptor has no effect.
7. `queue-homeostat` compares the synthetic queue metric with its target range and applies bounded negative feedback to pressure.
8. `cycle-clock` advances deterministic logical phases; it does not read wall-clock time or create authority.
9. `observer-support` records health observations and emits proposal-only throttle/retry/quarantine actions. Simulation never applies those proposals.
10. `plasticity-proposal` carries evidence and rollback for a possible synapse-strength change. It remains unapplied.

## Artifacts

```bash
uv run brain-role validate examples/neuroendocrine-public --format json
uv run brain-role validate-neural examples/neuroendocrine-public
uv run brain-role compile-connectome examples/neuroendocrine-public \
  --output .artifacts/connectome.json
uv run brain-role simulate .artifacts/connectome.json \
  --scenario examples/neuroendocrine-public/scenario.yaml \
  --output .artifacts/trace.json
```

- **CompiledConnectome** is a canonical deterministic projection bound to the Brain artifact digest. It is not an authority source.
- **ActivationScenario** supplies synthetic signals, metrics, and explicit tick/event limits.
- **NeuralTrace** is immutable evidence of activations, modulation, homeostasis, Support proposals, Plasticity proposals, and the stop reason.

All files are synthetic and `PUBLIC`. The commands are offline and do not deploy, publish, activate, or mutate an external runtime.
