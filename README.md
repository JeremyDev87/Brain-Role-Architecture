<!-- locales: README.md README.ko.md README.zh-CN.md README.es.md README.ja.md -->

# Brain-Role Architecture

**English** | [한국어](README.ko.md) | [简体中文](README.zh-CN.md) | [Español](README.es.md) | [日本語](README.ja.md)

[![Verify](https://github.com/JeremyDev87/Brain-Role-Architecture/actions/workflows/verify.yml/badge.svg)](https://github.com/JeremyDev87/Brain-Role-Architecture/actions/workflows/verify.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)](pyproject.toml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-D22128.svg)](LICENSE)

**PRE_RELEASE · source candidate 0.4.0 · not published**

Brain-Role Architecture is a verifiable, role-aware architecture for governing AI-agent invariants,
durable state, risk, workflows, persona, and goals without confusing responsibility with execution order.

> **One rule survives every rewrite:** Brainstem is the only absolute invariant. Cerebellum through Prefrontal Cortex can change only through
> explicit ownership, approval, provenance, rollback, and effective-time contracts.

![Brain-Role poster: Neural orthogonal band, Brainstem through Prefrontal Cortex Brain plane, Actor/Role plane, Compilation plane](docs/assets/brain-role-meme.png)

*Four visual zones: responsibilities, capabilities, deterministic build, and orthogonal modulation.*

## Why this exists

Agent systems often mix safety rules, memory, workflows, persona, and goals into one mutable prompt or
configuration. That makes it difficult to answer basic governance questions: What may change? Who owns the
change? What depends on it? Can it be rolled back? Brain-Role Architecture makes those boundaries explicit,
machine-checkable, and portable.

The README explains the project; [SPEC.md](SPEC.md) remains the normative contract and takes precedence over
all explanatory documentation.

## Responsibility topology: Brainstem through Prefrontal Cortex

| Layer | Responsibility | Change contract |
| --- | --- | --- |
| **Brainstem** | Truth/non-fabrication, safety/security, provenance/no-loss, deterministic transition | **Absolute invariant.** No higher layer or role may override it. |
| **Cerebellum** | Repeatable automation and schedules | Controlled; may be reserved. |
| **Hippocampus** | Durable state and memory | Controlled with explicit ownership and provenance. |
| **Amygdala** | Risk and conflict registry | Controlled; may be reserved. |
| **Cerebral Cortex** | Workflows and orchestration | Controlled, reviewable, and reversible. |
| **Default Mode Network** | Persona and communication behavior | Controlled with explicit change-control metadata. |
| **Prefrontal Cortex** | Goals and direction | Controlled with explicit change-control metadata. |

Anatomical names describe **responsibility and authority**, not runtime or compile order.

## Three independent planes

1. **Brain plane** — responsibility, authority, and change rules.
2. **Actor/Role plane** — capabilities, inputs/outputs, permissions, state scope, and escalation.
3. **Compilation plane** — an explicit dependency DAG and explicit compile order, independent of anatomical responsibility names.

Keeping these planes separate prevents a role from gaining authority merely because it runs first or last.
See [the three-plane explanation](docs/explanation/three-planes.md).

## Architecture at a glance

![Brain-Role structure map with Brainstem through Prefrontal Cortex, Role plane, Compilation DAG, Neural circuit](docs/assets/brain-role-overview.svg)

*The icons show responsibility, capability, build order, and modulation without turning Brainstem through Prefrontal Cortex into a pipeline.*

The additive 0.2.x neural extension is orthogonal to all three: typed Functional Neurons and Synapses carry
execution signals, while explicit receptors, homeostats, support contracts, and logical clocks provide bounded
modulation. None of activation, strength, concentration, receptor count, or graph centrality creates authority.

## What is included

- Normative specification and Draft 2020-12 JSON Schemas
- Deterministic, offline `brain-role` validator CLI
- Deterministic `CompiledConnectome` compiler and bounded offline neural simulator
- Receptor-bounded regulation, homeostasis, support, logical-clock, and proposal-only plasticity contracts
- Synthetic valid and invalid conformance fixtures
- Public/private boundary checks and a threat model
- Unit, schema-sync, documentation, and distribution smoke verification

## Quick start

Requirements: Python 3.11+ and [`uv`](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/JeremyDev87/Brain-Role-Architecture.git
cd Brain-Role-Architecture
uv sync --all-groups
uv run brain-role validate examples/minimal-public --format json
```

Expected result:

```json
{"errors":[],"specVersion":"0.1.0","valid":true}
```

Compile deterministic neutral artifacts and run every repository gate:

```bash
uv run brain-role compile examples/minimal-public --output .artifacts/compiled.json
uv run brain-role validate-neural examples/neuroendocrine-public
uv run brain-role compile-connectome examples/neuroendocrine-public --output .artifacts/connectome.json
uv run brain-role simulate .artifacts/connectome.json \
  --scenario examples/neuroendocrine-public/scenario.yaml --output .artifacts/trace.json
make verify
```

## Validation and artifact flow

![brain-role CLI flow to compiled.json connectome.json trace.json](docs/assets/brain-role-flow.svg)

*Validation produces inspectable artifacts; it does not deploy, publish, or change external runtime state.*

`compile` writes a canonical JSON file with explicit layer order and stable role/policy ordering. It adds no
source paths, credentials, or runtime activation data.

## Use it for

- Designing auditable AI-agent governance bundles
- Validating layer ownership, dependency, and permission contracts in CI
- Testing adapters against deterministic synthetic fixtures
- Reviewing persona and goal changes under their declared change-control contracts

## It is not

- A hosted agent runtime or orchestration service
- A self-modifying memory system
- Authorization to deploy, publish, activate, or mutate an external runtime
- A container for real profiles, sessions, credentials, private URLs, or personal data

## Documentation map

- [Normative specification](SPEC.md)
- [Quick-start tutorial](docs/tutorials/quickstart.md)
- [Three independent planes](docs/explanation/three-planes.md)
- [CLI reference](docs/reference/cli.md)
- [Neural runtime reference](docs/reference/neural-runtime.md)
- [Neural runtime authority decision](docs/adr/0006-neural-runtime-orthogonal-planes.md)
- [Manifest and schema model](docs/reference/manifest-model.md)
- [Threat model](docs/security/threat-model.md)
- [Contributing](CONTRIBUTING.md) and [governance](GOVERNANCE.md)

## Security and public/private boundary

Public bundles must contain only synthetic `PUBLIC` material. Do not add credentials, private URLs, real
profiles or sessions, secret values, account identifiers, or personal absolute paths. Report vulnerabilities
through [SECURITY.md](SECURITY.md), not a public issue.

The validator is offline, deterministic, and side-effect-free. Validation errors use instance-relative paths
and must not echo private absolute paths or secret values.

## Project status

Version `0.4.0` is an experimental source candidate. It is not represented as a package on a registry, a Git
tag, a GitHub Release, or a deployment. Compatibility may change while the specification remains pre-release.
See [CHANGELOG.md](CHANGELOG.md).

## Contributing

Start with [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Changes that alter
behavior must preserve the normative contract, add synthetic regression evidence, and pass:

```bash
make verify
```

## Publication boundary

Passing validation or `make verify` does **not** authorize a Git commit, push, release, package publication,
deployment, activation, or repository visibility change. Those are separate owner-controlled decisions.

Licensed under Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

## Neural runtime elements

The neural runtime is an orthogonal execution and evidence plane; it never grants Brain or Role authority.

| Element | Role |
| --- | --- |
| **Functional Neuron** | Capability-bound processor with typed ports and explicit integration thresholds. |
| **Synapse** | Typed connection with excitatory/inhibitory effect, strength, and logical delay. |
| **Regulator** | Bounded modulation value with decay and TTL; it has no effect without a receptor. |
| **Receptor** | Explicit binding that maps a regulator to a neuron's threshold or gain within limits. |
| **Homeostat** | Metric-driven negative feedback that proposes bounded regulator adjustments. |
| **Support** | Observes health and emits proposal-only throttle, retry, or quarantine actions. |
| **Logical Clock** | Deterministic tick phases with no wall-clock authority. |
| **Plasticity Proposal** | Evidence and rollback-bearing change proposal that is never applied by simulation. |
| **ActivationScenario** | Synthetic input signals, metrics, and explicit tick/event bounds. |
| **CompiledConnectome** | Canonical deterministic circuit projection bound to its Brain artifact, not an authority source. |
| **NeuralTrace** | Immutable simulation evidence containing activations, modulation, support proposals, and stop reason. |

See the [neuroendocrine walkthrough](examples/neuroendocrine-public/README.md) and [runtime reference](docs/reference/neural-runtime.md).
