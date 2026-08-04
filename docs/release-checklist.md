# 0.1.0 release-readiness checklist

`make verify` is the single local release-readiness gate for the current command surface. It runs source-bound
lint, type, tests, specification/schema synchronization, public-boundary and documentation checks, release
metadata consistency, then builds an sdist and wheel. The distribution smoke installs the fresh wheel into an
isolated environment and exercises the installed `brain-role` console command for `--version`, `validate`, and
`render hermes` from a non-repository working directory.

The isolated install may resolve declared dependencies through the configured package index or cache. The
project's offline guarantee applies to validation and rendering at runtime, not to package installation.

The candidate remains **PRE_RELEASE**. A green gate does not authorize commit, push, tag creation, GitHub
Release creation, registry publication, deployment, or visibility changes. Those actions require a separate
maintainer-approved publication lane. The project currently exposes no standalone `compile` or cross-revision
`diff` command; release readiness must not claim or test commands that do not exist.