# Threat model

## Protected assets

P0 semantics, architecture identity, role permission boundaries, provenance, rollback metadata, public
package contents, and the operator-selected export directory.

## Threats and controls

1. Prompt or knowledge injection: manifests are data, never dynamically executed.
2. Priority inversion: P0 writes and higher-layer overrides are rejected.
3. Confused deputy: roles use deny-by-default explicit read/write/forbidden sets.
4. Self-escalation: self targets and self-escalation flags are rejected.
5. Memory poisoning: provenance and controlled change metadata are required.
6. Secret/private leakage: PUBLIC-only synthetic examples and boundary scans.
7. Path traversal or symlink escape: contained relative regular-file references only.
8. Dependency confusion/cycle: local schema set, dangling checks, DAG validation.
9. Resource exhaustion: per-file, total-byte, and nesting limits.
10. Unsafe adapter write: explicit output, symlink checks, atomic replacement, runtime-home denial.

## Residual risk

Static schemas cannot prove model behavior, human review quality, repository settings, package registry
state, or host compromise. Behavioral prompt-injection evaluation, CodeQL, Scorecard, and SLSA release
provenance are intentionally deferred until real v0.1 usage or failure evidence justifies them.
