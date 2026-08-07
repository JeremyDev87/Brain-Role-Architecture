# Changelog

## [0.4.0] - PRE_RELEASE

Breaking PRE_RELEASE candidate that removes the provider-specific exporter so the public architecture
surface stays provider-neutral.

- Removed the provider-specific exporter module and its `render` CLI surface.
- Neutralized README, tutorial, CLI, release, and flow-diagram language away from product-specific
  runtime homes while keeping offline deterministic validation and artifact boundaries.
- Updated workflow smoke inputs after the deleted exporter test path.
- Preserved `0.1.x` governance validation and exact `CompiledBrainRole` artifact compatibility.
- Preserved the additive `0.2.x` neural surfaces: `validate-neural`, `compile-connectome`, and `simulate`.

## [0.2.0] - PRE_RELEASE

Unreleased additive source candidate introducing an authority-orthogonal neural reference runtime.

- Added typed Functional Neuron and active Synapse manifests plus deterministic `CompiledConnectome` output.
- Added receptor-bounded regulator, homeostat, logical clock, proposal-only support interventions, and
  proposal-only plasticity contracts.
- Added a bounded offline simulator that emits immutable deterministic `NeuralTrace` artifacts.
- Preserved `0.1.x` governance validation and exact `CompiledBrainRole` artifact compatibility.

## [0.1.0] - PRE_RELEASE

Unreleased source candidate establishing the normative Brainstem through Prefrontal Cortex model, schemas, validator, conformance
fixtures, threat model, and verification gates.

- Hardened the public boundary against non-canonical IPv4, encoded localhost, and malformed URL authorities.
- Added source-bound test execution, release metadata consistency checks, and fresh wheel install/CLI smoke for
  the existing `version`, `validate`, and `compile` surfaces.
- Added the deterministic `CompiledBrainRole` schema, canonical compiler, safe atomic `compile` CLI surface,
  and installed-distribution compile smoke without changing PRE_RELEASE status.

No tag, release, or registry publication exists yet.
