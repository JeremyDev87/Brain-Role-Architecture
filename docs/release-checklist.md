# 0.3.0 release-readiness checklist

`make verify` is the single local release-readiness gate for the current command surface. It runs source-bound
lint, type checks, tests, specification/schema synchronization, public-boundary and documentation checks,
release metadata consistency, then builds an sdist and wheel. The distribution smoke installs the fresh wheel
into an isolated environment and exercises `--version`, `validate`, and `compile`,
`validate-neural`, `compile-connectome`, and `simulate` from a non-repository working directory.

The isolated install may resolve declared dependencies through the configured package index or cache. The
The project's offline guarantee applies to validation, compilation, and simulation at runtime, not to
package installation.

Compatibility evidence MUST compare the exact legacy `CompiledBrainRole` bytes/SHA against the pinned 0.1.x
oracle. Neural artifact success MUST NOT substitute for legacy compatibility proof. The removed exporter is
covered by the breaking-change note rather than a compatibility oracle.

The candidate remains **PRE_RELEASE**. A green gate does not authorize commit, push, tag creation, GitHub
Release creation, registry publication, deployment, or visibility changes. Those actions require a separate
maintainer-approved publication lane. C3 cross-revision `diff`, native runtime activation, and autonomous
plasticity application remain out of scope.
