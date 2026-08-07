# Neural runtime reference

The 0.2.x neural extension models execution without changing governance authority.

| Plane | Contract | Authority boundary |
| --- | --- | --- |
| Governance | Existing Brainstem through Prefrontal Cortex, Role, Policy, approval and audit | Sole source of permission and invariants |
| Neural fast path | typed ports, immutable signals, Functional Neuron, active Synapse | Cannot create role capabilities or P-layer access |
| Regulatory | Regulator plus explicit ReceptorBinding | Only bounded threshold/gain changes; no business payload |
| Homeostatic | metric, acceptable range, controller, regulator level | Deterministic feedback input only |
| Support | observation plus throttle/retry/quarantine proposals | Proposal-only in 0.2.0; no destructive repair or authority |
| Clock | logical tick, period, phase | No wall-clock read |
| Plasticity | evidence and rollback proposal | Recorded but never auto-applied |

`CompiledConnectome` is a deterministic projection. `NeuralTrace` is immutable execution evidence. Neither is a
source-of-truth manifest, and neither the Wiki document graph nor graph centrality/activation/regulator level can
grant permission.

Neuron integration is executable rather than descriptive. After receptor gain, `any` selects the strongest received
signal and evaluates it against the activation threshold; `all` requires every declared input port in the same
logical tick plus an aggregate threshold pass; and `threshold` evaluates the aggregate amplitude.

Support is deliberately narrower than its manifest vocabulary: `observe` emits observation evidence, while
`throttle`, `retry`, and `quarantine-propose` emit deterministic `applied=false` proposal events. The reference
simulator does not perform those interventions or mutate business/runtime state.
