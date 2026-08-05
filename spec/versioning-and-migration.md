# Versioning and migration

The 0.x line is experimental. Backward-compatible additions increment MINOR; corrections increment
PATCH. Breaking schema, precedence, or P0 semantics increment MAJOR. P0 semantic changes also create a
new architecture identity and use an owner-controlled out-of-band migration with explicit rollback.

## 0.1.x governance compatibility

The `0.2.0` package continues to validate `0.1.x` BrainArchitecture manifests and emits their legacy
validation report as `specVersion=0.1.0`. `CompiledBrainRole` canonical bytes, SHA receipts, `compile`, and
`render hermes` stay unchanged for an unchanged `0.1.x` instance.

## 0.2.x neural extension

Neural manifests use `metadata.version: 0.2.x` and are rooted at a separate `NeuralArchitecture`. They do
not extend or rewrite `BrainArchitecture`. `CompiledConnectome` references the canonical governance bundle
by SHA-256 and is a derived artifact, not an authority source. Migration is opt-in: add `neural.yaml` and its
referenced public manifests; no `0.1.x` source file must change.
