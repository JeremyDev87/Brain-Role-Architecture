# Changelog

## [0.3.0] - PRE_RELEASE

Unreleased additive source candidate introducing an authority-orthogonal neural reference runtime.

- Added typed Functional Neuron and active Synapse manifests plus deterministic `CompiledConnectome` output.
- Added receptor-bounded regulator, homeostat, logical clock, proposal-only support interventions, and
  proposal-only plasticity contracts.
- Added a bounded offline simulator that emits immutable deterministic `NeuralTrace` artifacts.
- Preserved `0.1.x` governance validation and exact `CompiledBrainRole` artifact compatibility.
- Removed the provider-specific exporter and its `render` CLI surface as a breaking change.

## [0.1.0] - PRE_RELEASE

Unreleased source candidate establishing the normative P0-P6 model, schemas, validator, conformance
fixtures, threat model, and verification gates.

- Hardened the public boundary against non-canonical IPv4, encoded localhost, and malformed URL authorities.
- Added source-bound test execution, release metadata consistency checks, and fresh wheel install/CLI smoke for
  the existing `version`, `validate`, and `compile` surfaces.
- Added the deterministic `CompiledBrainRole` schema, canonical compiler, safe atomic `compile` CLI surface,
  and installed-distribution compile smoke without changing PRE_RELEASE status.

No tag, release, or registry publication exists yet.
