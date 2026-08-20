# README image assets

All three assets are editorial diagrams for Brain-Role Architecture. They are not normative replacements for `SPEC.md` and do not grant runtime, publication, or deployment authority.

## brain-role-meme.png

An architecture-specific poster for the multilingual READMEs. It separates four visual regions:

- Neural Runtime 0.2.x: Functional Neuron, Synapse, Regulator, Receptor, Homeostat, Support, Logical Clock, and proposal-only change; the runtime never creates Brain or Role authority.
- Brain plane: seven anatomical responsibility names — Brainstem, Cerebellum, Hippocampus, Amygdala, Cerebral Cortex, Default Mode Network, and Prefrontal Cortex.
- Actor/Role plane: capability and permission without ownership of Brain rules.
- Compilation plane: an explicit dependency DAG and `compileOrder` producing deterministic `CompiledBrainRole` artifacts.

The responsibility areas have no pipeline arrows; their placement does not imply runtime or compile order. Brainstem is the only absolute invariant. The anatomical names are software-role metaphors, not claims of one-to-one neuroscience equivalence.

- Generation route: Hermes `image_generate`
- Provider/model: `openai-codex` / `gpt-image-2-medium`
- Mode: reference-guided image edit
- Fallbacks: none
- Generated: 2026-08-07
- Actual-pixel QA: PASS — seven exact names, Brainstem invariant label, orthogonal runtime, no numbered legacy labels
- Artifact: RGB PNG, 1536 × 1024
- SHA-256: `4fcc65d3d27bfaf6840a4b49533b606c12009a013ef031f20a3e96c686cb2322`

## brain-role-overview.svg

Accessible UTF-8 SVG wrapper with `<title>` and `<desc>` around the accepted OpenAI-generated overview. It shows the same seven peer responsibility areas, a distinct Actor/Role plane, Compilation DAG, and orthogonal Neural Runtime, with no cross-plane authority arrows and no pipeline arrows between responsibility areas.

- Provider/model: `openai-codex` / `gpt-image-2-medium`; fallback none
- Generated: 2026-08-07
- Actual-pixel QA: PASS — all seven labels spelled exactly; Brainstem marked `ONLY ABSOLUTE INVARIANT`; no numbered legacy labels or Ego label
- Embedded PNG: 1536 × 1024, SHA-256 `a417d464ab268367d688d7282b7c6593572e4787dcdbbceb2c1314c91418e842`
- Wrapper: `brain-role-overview.svg`, SHA-256 `e9ea05e98ce11319f237ad820f85056d3957a084cd73d6701b8fa3e7ce5d9304`

## brain-role-flow.svg

Accessible UTF-8 SVG wrapper around the accepted offline CLI flow. A synthetic public bundle crosses the public boundary and offline validation, then produces independent `CompiledBrainRole`, `CompiledConnectome`, and `NeuralTrace` artifacts. Deploy/publish is visibly outside and not authorized.

- Provider/model: `openai-codex` / `gpt-image-2-medium`; fallback none
- Generated: 2026-08-07
- Actual-pixel QA: PASS — three artifact branches, deploy/publish denial, no numbered legacy labels, no Neural-to-Brain/Role authority arrow
- Embedded PNG: 1536 × 1024, SHA-256 `54b886e71ed1bce5e94e903cc2da376f50555e8cd6a5dcb744ead0f2326f6121`
- Wrapper: `brain-role-flow.svg`, SHA-256 `ad481e9cd5e0c9c8de912b6240b5f359bdc87236ca7675aedd83e5e852c12899`

## localized terminology variants

The four localized READMEs use self-contained SVG variants under `docs/assets/localized/{ko,ja,zh-CN,es}/`. Each variant preserves the accepted 1536 × 1024 illustration pixels and adds an accessible terminology panel using the repository contract `Canonical(localized)`; canonical Schema and CLI identifiers remain English.

- Terminology SSOT: `docs/reference/localized-terminology.json`
- Deterministic generator: `scripts/build_localized_assets.py` (Python standard library only)
- Output inventory and exact source/output SHA-256 values: `docs/assets/localized/manifest.json`
- Safety: no external URL, script, `foreignObject`, font payload, image-model call, or runtime authority is added
- Actual-pixel QA: PASS for 12/12 locale assets at native render — original illustration and terminology panel visible; no clipped labels, overlap, missing glyph/tofu, or right-edge overflow
- English asset bytes remain frozen; localized README alt text and captions retain locale-specific accessibility markers

No third-party meme template, external font, URL, or script is embedded. Apache-2.0 distribution scope only.
