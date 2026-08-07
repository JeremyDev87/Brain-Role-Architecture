# Compiled change validation

`brain-role diff BASELINE CANDIDATE [--format text|json]` is the C3-a gate for comparing two canonical
`CompiledBrainRole` artifacts. It is an offline policy decision, not an apply operation: it emits no patch,
mutates no source, and grants no publication, deployment, or merge authority.

## Input contract

Both inputs must be regular non-symlink files containing canonical UTF-8 JSON with one final newline. The loader
rejects malformed or duplicate-key JSON, non-finite numbers, excessive size or nesting, forbidden public-boundary
text, schema-invalid bundles, invalid compile topology, and bytes that differ from canonical re-encoding. Input and
I/O failures return exit 2 with a fixed stderr message; paths and source values are not echoed.

The artifacts must use the same `apiVersion`, `metadata.architectureId`, `metadata.id`, and
`metadata.classification`. Cross-version comparison is not migration and is denied fail-closed.

## C3-a decision matrix

- Identical canonical artifacts are allowed with no findings.
- Brainstem is compared as an exact canonical component and any change is denied.
- A Cerebellum-through-Prefrontal-Cortex semantic change is allowed only when:
  - the layer `metadata.version` advances strictly;
  - the architecture `metadata.version` advances strictly;
  - `spec.changeControl.effectiveAt` advances strictly; and
  - the complete candidate remains schema-valid with approval, provenance, rollback, and effective-time evidence.
- Version or change-control edits without a semantic layer change are denied as empty control updates.
- Role, policy, and compile-order changes are denied because C3-a defines no trusted mutation authority for them.

C3-a reports that structural evidence is present; it does not claim that a human approval occurred beyond the
schema-valid evidence carried by the artifact.

## Output contract

Text and JSON reports are deterministic and contain only architecture/component identifiers, fixed decision codes,
fixed messages, canonical artifact SHA-256 values, and public metadata. They do not include raw payloads or paths.
Findings sort by component type, component identifier, code, and message.

Exit status is:

- `0` for identical or allowed controlled mutation;
- `1` when both artifacts are valid but the mutation policy denies the candidate;
- `2` for CLI, file, JSON, schema, canonicalization, or I/O failure.
