# Brain-Role Architecture

**PRE_RELEASE · source candidate 0.1.0 · not published**

Brain-Role Architecture is a verifiable, role-aware architecture for governing AI-agent invariants,
state, workflows, persona, and goals from P0 to P6.

> P0 is the only absolute invariant. P1-P6 are controlled-mutable responsibility layers with explicit
> ownership, approval, provenance, rollback, and effective-time contracts.

The project separates three concepts that are often conflated:

- **Brain plane:** responsibility, authority, and change rules.
- **Actor/Role plane:** capabilities, inputs/outputs, permissions, and escalation.
- **Compilation plane:** an explicit dependency DAG and explicit compile order, independent of P numbers.

## What is included

- Normative specification and Draft 2020-12 JSON Schemas
- Deterministic, offline `brain-role` validator CLI
- Synthetic valid/invalid conformance fixtures
- Read-only Hermes `prefill_messages_file` reference exporter
- Public/private boundary, threat model, tests, and package smoke verification

## Quick start

```bash
uv sync --all-groups
uv run brain-role validate examples/minimal-public --format json
uv run brain-role render hermes examples/minimal-public --output .artifacts/hermes
make verify
```

`render hermes` only generates files under the selected output directory. It does not activate Hermes,
change configuration, or touch `SOUL.md`, `USER.md`, `MEMORY.md`, or `~/.hermes`.

Read the [normative specification](SPEC.md), [Korean README](README.ko.md), and
[quick-start tutorial](docs/tutorials/quickstart.md).

## Publication boundary

Passing validation does **not** authorize a Git commit, push, release, package publication, deployment,
or repository visibility change. No tag, release, or registry package is represented by source version
`0.1.0`.

Licensed under Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
