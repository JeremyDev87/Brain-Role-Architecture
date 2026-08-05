# CLI reference

- `brain-role --version`
- `brain-role validate <instance> [--format text|json]`
- `brain-role compile <instance> --output <file>`
- `brain-role render hermes <instance> --output <directory>`

`compile` validates first and writes nothing on conformance failure. A successful compile atomically replaces
the selected file and prints `COMPILED file=<name> sha256=<digest>`. Runtime-home, native Hermes, and symlink
destinations are rejected.

Exit 0 means conforming, compiled, or rendered; exit 1 means conformance failure; and exit 2 means CLI,
input, or I/O failure. Reports are deterministic and use instance-relative paths. The CLI performs no
network access and does not activate a runtime.
