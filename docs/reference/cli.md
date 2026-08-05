# CLI reference

## Governance 0.1.x compatibility surface

- `brain-role --version`
- `brain-role validate <instance> [--format text|json]`
- `brain-role compile <instance> --output <file>`
- `brain-role render hermes <instance> --output <directory>`

`compile` validates first and writes nothing on conformance failure. A successful compile atomically replaces
the selected file and prints `COMPILED file=<name> sha256=<digest>`. Runtime-home, native Hermes, and symlink
destinations are rejected. An unchanged `0.1.x` instance retains its `specVersion=0.1.0` validation report and
exact compiled/adapter artifact bytes.

## Neural 0.2.x additive surface

- `brain-role validate-neural <instance> [--format text|json]`
- `brain-role compile-connectome <instance> --output <file>`
- `brain-role simulate <connectome> --scenario <scenario.yaml> --output <trace.json>`

Successful commands print `CONNECTOME file=<name> sha256=<digest>` and
`SIMULATED file=<name> sha256=<digest> events=<count>`. The simulator is an offline deterministic reference
runner: capability references are logged, never imported or executed. Directed cycles terminate under scenario
`maxTicks` and `maxEvents` bounds.

Exit 0 means conforming, compiled, rendered, or simulated; exit 1 means conformance failure; and exit 2 means
CLI, input, or I/O failure. Reports are deterministic and use instance-relative paths. No command performs
network access, activates a runtime, applies plasticity, or grants publication authority.
