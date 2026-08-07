# CLI reference

## Governance 0.1.x compatibility surface

- `brain-role --version`
- `brain-role validate <instance> [--format text|json]`
- `brain-role compile <instance> --output <file>`
- `brain-role diff <baseline> <candidate> [--format text|json]`

`compile` validates the source instance first and writes nothing on conformance failure. A successful compile
atomically replaces the selected file and prints `COMPILED file=<name> sha256=<digest>`. Forbidden native-file
and symlink destinations are rejected. An unchanged `0.1.x` instance retains its `specVersion=0.1.0`
validation report and exact compiled artifact bytes.

`diff` compares two canonical compiled artifacts and prints a deterministic change report. Exit 0 means
identical or allowed controlled mutation, exit 1 means policy violation, and exit 2 means CLI, input, or I/O
failure. The report never echoes absolute paths, raw component payloads, or secret values.

## Neural 0.2.x additive surface

- `brain-role validate-neural <instance> [--format text|json]`
- `brain-role compile-connectome <instance> --output <file>`
- `brain-role simulate <connectome> --scenario <scenario.yaml> --output <trace.json>`

Successful commands print `CONNECTOME file=<name> sha256=<digest>` and
`SIMULATED file=<name> sha256=<digest> events=<count>`. The simulator is an offline deterministic reference
runner: capability references are logged, never imported or executed. Directed cycles terminate under scenario
`maxTicks` and `maxEvents` bounds.

Exit 0 means conforming, compiled, or simulated; exit 1 means conformance failure; and exit 2 means
CLI, input, or I/O failure. Reports are deterministic and use instance-relative paths. No command performs
network access, activates a runtime, applies plasticity, or grants publication authority.
