# Controlled-mutation proof

This source-checkout demo exercises one narrow claim: Brain-Role Architecture can compare canonical governance
artifacts, block an immutable Brainstem change, and accept a non-invariant layer change only when its declared
change-control fields advance. All three artifacts are synthetic `PUBLIC` derivatives of `examples/minimal-public`.

## Prerequisites

Use Python 3.11+ and `uv` from a source checkout. No registry installation is claimed.

```bash
uv sync --all-groups
```

## 1. Fail closed on an immutable change

```bash
uv run brain-role diff \
  examples/controlled-mutation-demo/baseline.json \
  examples/controlled-mutation-demo/blocked.json \
  --format json
```

Expected: exit `1`, `"allowed":false`, and finding code `E_CHANGE_BRAINSTEM`.

## 2. Accept a governed non-invariant change

```bash
uv run brain-role diff \
  examples/controlled-mutation-demo/baseline.json \
  examples/controlled-mutation-demo/allowed.json \
  --format json
```

Expected: exit `0`, `"allowed":true`, and finding code `OK_CONTROLLED_LAYER_UPDATE`. The candidate advances the
Cerebral Cortex layer version, architecture version, and `effectiveAt` value.

## Canonical artifact evidence

```text
aee6d54f66db21367dfaa58fdd9c0beb27c2b1add8f73ff1ffb60efb4ffc17f7  baseline.json
8ed2e835fb451e24349c0f460586d27c10cfa64ae26e5e2116058643472bdffe  blocked.json
03bb00a5a6abaceeb1f9cb2a6ef98dfcbf0793b9ee358abb34ef28eb398ffb9f  allowed.json
```

Re-running either command produces the same canonical JSON report for the same inputs. `make verify` validates
these outcomes and the tracked hashes.

## What this proves—and what it does not

It proves deterministic behavior for these synthetic artifacts and the current conformance contract. It does
not activate a runtime, authorize a deployment, certify security, guarantee production safety, or prove that
another system has integrated the contract correctly. This technical demo also does not prove market demand.
