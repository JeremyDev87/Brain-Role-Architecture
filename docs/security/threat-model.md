# Threat model

## Protected assets

Brainstem semantics, architecture identity, role permission boundaries, provenance, rollback metadata, public
package contents, and the operator-selected export directory.

## Threats and controls

1. Prompt or knowledge injection: manifests are data, never dynamically executed.
2. Priority inversion: Brainstem writes and higher-layer overrides are rejected.
3. Confused deputy: roles use deny-by-default explicit read/write/forbidden sets.
4. Self-escalation: self targets and self-escalation flags are rejected.
5. Memory poisoning: provenance and controlled change metadata are required.
6. Secret/private leakage: PUBLIC-only synthetic examples and boundary scans. URL authorities are parsed
   offline and fail closed when the host is missing, brackets or ports are malformed, or host percent-decoding
   remains ambiguous after two bounded rounds. After decoding, host names are IDNA-canonicalized and trailing
   root dots are removed before classification, covering Unicode and encoded browser-equivalent private hosts.
   HTTP(S) candidates are also scanned after WHATWG-equivalent tab/LF/CR removal, backslash-to-slash
   conversion, and special-scheme authority-separator normalization. Decimal, octal, hexadecimal, and
   shortened IPv4 forms are normalized without DNS, network access, or a platform resolver. Only the exact
   normative `env://VARIABLE_NAME` shape bypasses URL classification; malformed or nested
   environment-reference payloads fail closed.
7. Path traversal or symlink escape: contained relative regular-file references only.
8. Dependency confusion/cycle: local schema set, dangling checks, DAG validation.
9. Resource exhaustion: per-file, total-byte, and nesting limits.
10. Unsafe adapter write: explicit output, symlink checks, atomic replacement, runtime-home denial.

## Residual risk

Static schemas cannot prove model behavior, human review quality, repository settings, package registry
state, or host compromise. Behavioral prompt-injection evaluation, CodeQL, Scorecard, and SLSA release
provenance are intentionally deferred until real v0.2 usage or failure evidence justifies them.


## Neural extension threats

11. Signal forgery or port confusion: exact source/output/target/input signal-type equality and canonical IDs.
12. Unbounded recurrent circuit: positive delay plus explicit `maxTicks` and `maxEvents` termination bounds.
13. Modulation authority escalation: schema-closed receptor effects exclude policy, permission, owner, and layer.
14. Broadcast regulator abuse: no matching receptor means no target effect; levels remain bounded.
15. Support-worker confused deputy: observation is evidence-only; throttle, retry, and quarantine are recorded
    as `applied=false` proposals and never executed by the 0.2.0 reference simulator.
16. Time nondeterminism: simulation accepts logical ticks and does not read the host wall clock.
17. Self-rewriting topology: plasticity is immutable proposal evidence and is never applied by the simulator.
18. Artifact substitution: a connectome carries the exact canonical governance bundle SHA-256 and every loaded
    nested manifest, reference, and numeric bound is revalidated before simulation.
19. Numeric/output poisoning: neural sources, compiled artifacts, scenarios, and traces reject non-finite numbers
    and reapply the public-boundary scan so secret-like values cannot be serialized into derived artifacts.
