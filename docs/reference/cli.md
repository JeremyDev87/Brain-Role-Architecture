# CLI reference

- `brain-role --version`
- `brain-role validate <instance> [--format text|json]`
- `brain-role render hermes <instance> --output <directory>`

Exit 0 means conforming or rendered, exit 1 means conformance failure, and exit 2 means CLI/input/I/O
failure. Reports are deterministic and use instance-relative paths. The CLI performs no network access.
