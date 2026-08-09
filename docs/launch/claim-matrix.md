# Launch claim matrix

This file constrains soft-preview copy. Claims must remain traceable to repository evidence and the exact
release state; marketing language never expands runtime or publication authority.

## Allowed claims

| Claim | Required evidence |
| --- | --- |
| Policy-as-code and conformance toolkit for AI-agent responsibility, authority, and change contracts | `SPEC.md`, schemas, validator/compiler, `tests/conformance-map.yaml` |
| Offline and deterministic for the documented validator/compiler/diff paths | CLI tests, canonical artifact tests, distribution smoke |
| Brainstem changes fail closed in the controlled-mutation contract | `examples/controlled-mutation-demo/blocked.json`, `E_CHANGE_BRAINSTEM` test |
| Governed non-invariant changes can pass when version and effective-time controls advance | `allowed.json`, `OK_CONTROLLED_LAYER_UPDATE` test |
| GitHub Pre-release `v0.4.0` has wheel and source-distribution assets | Live GitHub release readback; do not convert this into a registry-install claim |

## Conditional wording

- Say **source checkout** for the documented installation path until a registry readback proves otherwise.
- Say **PRE_RELEASE** and **experimental**; compatibility may change.
- Say validation produces evidence; it does not grant authority or prove external integration safety.
- Describe the demo as technical credibility evidence, not demand validation.

## Forbidden claims

| Do not say | Why |
| --- | --- |
| `production-ready` | No production deployment, operational SLO, or external adoption evidence exists. |
| `runtime authorization` | The Neural Runtime is authority-orthogonal and cannot grant Brain or Role authority. |
| `security-certified` | Tests and threat modeling are not an external certification. |
| `stable/GA` | `0.4.0` remains PRE_RELEASE. |
| “guarantees agent safety” | Conformance checks cannot guarantee host, integration, or operational safety. |
| “install with pip from PyPI” | No registry publication has been verified. |

## Publication boundary

A passing demo, test suite, or disclosure audit does not authorize commit, push, release mutation, registry
publication, deployment, repository visibility change, or launch-channel posting. Each external mutation needs
its own owner approval and authoritative readback.

## Operational surfaces

- `docs/launch/soft-preview-runbook.md` defines the gated publication, security, posting, and containment sequence.
- `docs/launch/soft-preview-ledger.md` keeps 24-hour reach, 7-day engagement, and 14-day qualified conversion
  separate.
