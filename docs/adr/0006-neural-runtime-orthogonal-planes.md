# ADR 0006: Neural runtime as authority-orthogonal planes

Status: accepted for the 0.2.0 PRE_RELEASE source candidate.

## Decision

Keep P0-P6 as the only governance plane. Add a separate neural fast path, receptor-bounded regulatory plane,
homeostatic feedback plane, support plane, logical clock, and proposal-only plasticity control plane.
`NeuralArchitecture` references but does not extend `BrainArchitecture`; `CompiledConnectome` binds the
canonical governance bundle by SHA-256 and carries no new permission.

The reference runtime is a deterministic offline simulator. It records capability activation but never imports
or executes capabilities. Synapses use positive tick delay, and every scenario sets event/tick bounds. A
regulator affects a target only through an explicit receptor and only for schema-closed numeric parameters.
Neuron integration strategies have distinct deterministic firing semantics. Support observation is executable,
while throttle, retry, and quarantine remain explicit non-applied proposals in the 0.2.0 reference simulator.

## Rejected alternatives

- P7/P8 authority layers for neurons or hormones.
- `Synapse = Adapter`, `Neuron = Role/Skill`, or `Hormone = global config` one-to-one mappings.
- Named biological hormone pharmacology without a verified runtime consumer.
- Wall-clock coupling, autonomous topology rewrites, or runtime self-authorization.
- Reusing the Wiki document/heading Connectome as runtime authority.

## Consequences

Existing 0.1.x governance source and canonical artifacts remain unchanged. Neural use is opt-in and versioned
0.2.x. Cross-revision diff, real capability execution, precise biological kinetics, and plasticity application
require later evidence and separate contracts.
