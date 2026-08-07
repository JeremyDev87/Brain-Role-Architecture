# Brain-Role Architecture Specification 0.4.0

Status: **PRE_RELEASE**
Schema namespace: `brain-role.dev/v1alpha2` (legacy `v1alpha1` remains supported)

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are to be interpreted as
normative requirements in this document. Supporting documents are explanatory and MUST NOT override it.

## 1. Model

An architecture instance has three independent axes: the Brainstem through Prefrontal Cortex responsibility topology, a dependency
DAG, and an explicit compile order. Anatomical responsibility names do not imply compile order.

- **REQ-ARCH-001:** An instance MUST declare exactly one manifest for every layer Brainstem through Prefrontal Cortex.
- **REQ-ARCH-002:** References MUST be local, relative, contained beneath the instance root, and resolve
  to regular non-symlink files. URL, absolute, traversal, dangling, and symlink-escape references MUST
  be rejected.
- **REQ-ARCH-003:** Every structured manifest MUST reject unknown properties.

## 2. Brainstem absolute invariance

Brainstem is the only absolute invariant. It contains the minimum public core: truth/non-fabrication,
safety/security, provenance/no-loss, deterministic transition, and no higher-layer override.

- **REQ-BRAINSTEM-001:** Brainstem MUST be present, active, and `immutable`.
- **REQ-BRAINSTEM-002:** Brainstem MUST declare every minimum-core invariant.
- **REQ-BRAINSTEM-003:** Brainstem MUST NOT depend on another layer.
- **REQ-BRAINSTEM-004:** A role MUST NOT write Brainstem, override Brainstem, or grant itself authority.
- **REQ-BRAINSTEM-005:** A semantic Brainstem change is not an in-place migration; it MUST create a new
  `architectureId` and specification major version through an owner-controlled out-of-band process.

## 3. Cerebellum through Prefrontal Cortex controlled mutability

- **REQ-LAYER-001:** Cerebellum through Prefrontal Cortex MUST be `controlled` rather than absolutely immutable.
- **REQ-LAYER-002:** Every layer MUST declare owner, approval, provenance, rollback, and `effectiveAt`.
- **REQ-LAYER-003:** Cerebellum and Amygdala MAY be `reserved`; every other non-Brainstem layer MUST be active.
- **REQ-LAYER-004:** A reserved layer MUST NOT be writable by a role.

Responsibilities are: Cerebellum repeatable automation, Hippocampus durable state and memory, Amygdala risk/conflict registry,
Cerebral Cortex workflows and orchestration, Default Mode Network persona and communication, and Prefrontal Cortex goals and direction.

## 4. Dependency and compile contracts

- **REQ-GRAPH-001:** Dependencies MUST identify declared layers and MUST form a DAG.
- **REQ-GRAPH-002:** A layer MUST appear after all of its dependencies in explicit compile order.
- **REQ-GRAPH-003:** Compile order MUST contain Brainstem through Prefrontal Cortex exactly once and MUST begin with Brainstem.
- **REQ-GRAPH-004:** Compile order MUST be declared; it MUST NOT be inferred from anatomical responsibility names.

## 5. Actor and Role plane

- **REQ-ROLE-001:** Roles MUST explicitly declare purpose, owner, inputs, outputs, capabilities,
  read/write/forbidden layers, network policy, state scope, escalation, failure mode, and fallback policy.
- **REQ-ROLE-002:** Permissions are deny-by-default; write permission MUST be an explicit allowlist.
- **REQ-ROLE-003:** A role MUST NOT both write and forbid the same layer.
- **REQ-ROLE-004:** A role MUST NOT use `self` as an escalation target or enable self-escalation.

## 6. Public/private boundary

- **REQ-PUBLIC-001:** Public bundles MUST contain only `PUBLIC`, synthetic material.
- **REQ-PUBLIC-002:** Literal credentials, private URLs, real profiles/sessions/state, and personal
  absolute paths MUST NOT be present.
- **REQ-PUBLIC-003:** Secret values MUST NOT appear. A non-secret indirection such as
  `secretRef: env://VARIABLE_NAME` MAY be declared.

## 7. Compiler and validator

- **REQ-COMPILE-001:** A compiled bundle MUST contain only `apiVersion`, `kind`, source metadata,
  explicit compile order, and the validated layer, role, and policy documents; it MUST NOT add source
  paths, credentials, runtime activation data, or undeclared extension fields.
- **REQ-COMPILE-002:** Layers MUST follow explicit compile order, roles and policies MUST sort by
  `metadata.id`, and JSON serialization MUST be deterministic UTF-8 with sorted keys and one final newline.
- **REQ-COMPILE-003:** `brain-role compile` MUST validate before writing, preserve any existing output on
  validation failure, reject forbidden native-file and symlink destinations, atomically replace a
  successful file, and report its filename and SHA-256 digest.
- **REQ-CLI-001:** Validation MUST be deterministic, offline, side-effect-free, and sorted by stable
  `(path, code, pointer, message)` order.
- **REQ-CLI-002:** Exit status MUST be 0 for conformance, 1 for conformance failure, and 2 for CLI,
  input, or I/O failure.
- **REQ-CLI-003:** Error output MUST use instance-relative paths and MUST NOT echo private absolute paths
  or secret values.

## 8. Controlled mutation diff gate

- **REQ-CHANGE-001:** `brain-role diff` MUST require matching `apiVersion` and architecture identity and MUST fail closed on identity drift.
- **REQ-CHANGE-002:** Brainstem content MUST compare by exact canonical bytes and MUST reject any byte change.
- **REQ-CHANGE-003:** Controlled layers MAY change only when semantic content changes and the layer version,
  architecture version, and `changeControl.effectiveAt` all advance strictly.
- **REQ-CHANGE-004:** Role, policy, and compile-order changes MUST be rejected as unsupported for C3-a.
- **REQ-CHANGE-005:** Change reports MUST be deterministic, public-safe, and free of raw file paths or payload echoes.
- **REQ-CHANGE-006:** `brain-role diff` MUST exit 0 for allowed or unchanged results, 1 for policy violations, and 2 for input or CLI failures.

## 9. Version and publication

Package, specification, and compatibility metadata are `0.4.0` and experimental. Governance manifests remain
compatible with `0.1.x`; neural manifests require `0.2.x`. Passing `make verify` MUST NOT be interpreted as
permission to commit, push, publish, release, deploy, or change visibility.


## 10. Orthogonal neural plane

The neural plane is execution topology, not an authority hierarchy. A Functional Neuron is a role capability
bound to typed ports in a circuit; it is not a Role, Skill, Wiki node, or new Brain authority layer. A Synapse is an internal
port binding and is not a Hexagonal Adapter.

- **REQ-NEURAL-001:** `NeuralArchitecture` MUST remain separate from `BrainArchitecture`; each neuron MUST
  reference an existing role-granted capability and a non-Brainstem layer within that role contract.
- **REQ-NEURAL-002:** Input and output port names MUST be unique per neuron. A Synapse MUST reference declared
  ports whose signal types exactly match, and each `(fromNeuron, fromPort, toNeuron, toPort)` tuple MUST be unique.
- **REQ-CONNECTOME-001:** `CompiledConnectome` MUST be deterministically derived, sorted, path-independent, and
  bound to the canonical `CompiledBrainRole` bytes by SHA-256 without becoming an authority source.

## 11. Bounded neural simulation

- **REQ-RUNTIME-001:** Simulation MUST be offline and deterministic, MUST treat capability references as data,
  MUST NOT execute dynamic code, and MUST emit an immutable canonical `NeuralTrace`.
- **REQ-RUNTIME-002:** Directed neural cycles MAY exist only under explicit positive delay and `maxTicks` and
  `maxEvents` bounds; reaching a bound MUST terminate without source or topology mutation.
- **REQ-RUNTIME-003:** Integration strategies MUST have distinct deterministic semantics after receptor gain is
  applied: `any` selects the strongest received signal and fires when it meets `activationThreshold`; `all`
  requires every declared input port to receive a signal in the tick and the summed amplitude to meet the
  threshold; and `threshold` fires when the summed amplitude meets the threshold.

## 12. Regulatory and homeostatic planes

- **REQ-MOD-001:** A regulator MAY adjust only the schema-closed runtime parameters
  `activationThreshold` and `signalGain` through bounded receptor effects. It MUST NOT carry business payloads
  or change permission, policy, ownership, layer, or publication authority.

The reference simulator additionally enforces `minLevel <= initialLevel <= maxLevel`, bounded decay, and
`ttlTicks`; a homeostat or clock phase refreshes that logical TTL. Unimplemented dynamic `gateRef` and
`transformRef` execution is intentionally outside v0.2.0 and therefore rejected by the closed Synapse schema.
- **REQ-MOD-002:** A regulator MUST have no effect on a target without an explicit matching receptor.
- **REQ-HOMEOSTAT-001:** A homeostat MUST observe a declared metric, compare it with an acceptable range, and
  set only a bounded declared regulator level through deterministic negative-feedback input.

## 13. Support, clock, and plasticity control

- **REQ-SUPPORT-001:** Support manifests MAY declare observe, throttle, retry, or quarantine-propose actions.
  The 0.2.0 reference simulator MUST emit observation evidence only when `observe` is declared, MUST record every
  declared non-observe action as an `applied=false` proposal, and MUST NOT execute it, delete business state,
  execute capabilities, or create authority. Canonical proposal evidence MUST require `applied=false`.
- **REQ-CLOCK-001:** Clock behavior MUST use scenario-provided logical ticks and declared phases; it MUST NOT
  read wall-clock time during validation, compilation, or simulation.
- **REQ-PLASTICITY-001:** Plasticity MUST begin as a provenance-bearing proposal with rollback. The reference
  simulator MUST record but MUST NOT apply a proposal or rewrite topology.

## 14. Compatibility and CLI

- **REQ-COMPAT-001:** For an unchanged `0.1.x` governance instance, legacy validation reports and
  `CompiledBrainRole` bytes/SHA MUST remain unchanged. The removed provider-specific exporter is not part of
  the 0.4.0 compatibility surface.
- **REQ-CLI-004:** `validate-neural`, `compile-connectome`, and `simulate` MUST preserve the existing exit-code,
  output-safety, no-secret-echo, canonical serialization, and SHA-receipt conventions.
