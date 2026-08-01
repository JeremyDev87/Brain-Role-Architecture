# Agent instructions

- Preserve the normative contract in `SPEC.md`; explanatory documents MUST NOT redefine it.
- P0 is the only absolute invariant. P1-P6 are controlled-mutable responsibility layers.
- Use generic schemas and synthetic fixtures only. Never add personal canon, real profiles, sessions,
  credentials, private URLs, account identifiers, or home-directory paths.
- The validator and adapters are offline and deterministic. Do not add network access, dynamic code
  execution, or mutation of runtime homes such as `~/.hermes`.
- Run `make verify` before proposing publication.
- Validation does not authorize commit, push, release, publication, deployment, or visibility changes.
