# Manifest reference

An architecture references seven layer manifests, one or more role manifests, one or more policy
manifests, and one compile-order manifest. Schemas live in `schemas/v1alpha1/`. All documents use
`apiVersion: brain-role.dev/v1alpha1` and reject unknown fields.

`compiled-bundle.schema.json` defines the neutral `CompiledBrainRole` artifact. Its v1alpha1 top level is
limited to `apiVersion`, `kind`, source `metadata`, `compileOrder`, `layers`, `roles`, and `policies`.
Layers follow the declared compile order; roles and policies sort by `metadata.id`. Source paths,
credentials, runtime activation data, and undeclared extension fields are not part of the contract.
