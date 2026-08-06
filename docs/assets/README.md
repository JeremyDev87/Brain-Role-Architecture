# README image assets

## brain-role-meme.png

architecture-specific poster for multilingual READMEs. It depicts this model as a cute four-zone campus, not a generic software cartoon:

- Neural Runtime 0.2.x orthogonal band: Functional Neurons, Synapse, Regulator to matching Receptor, Homeostat feedback, Support observation, Logical Clock ticks, and an unapplied Plasticity proposal; it has no P-authority and never creates Brain authority
- Brain plane: P0-P6 with brain-element names (Brainstem through Prefrontal), presented as disconnected responsibility stations rather than a pipeline
- Actor/Role plane: a capability badge and permission key allow action without ownership of Brain rules
- Compilation plane: sealed P0 input, dependency DAG, compileOrder, and three sealed CompiledBrainRole / Connectome / Trace artifacts

- Generation route: OpenAI image generation through Hermes `image_generate`
- Provider: openai-codex
- Model: gpt-image-2-medium
- Mode: reference-guided architecture-poster regeneration
- Fallbacks: none
- Run call accounting: 2/2 OpenAI calls for this slot; call 1 exposed an unlabeled Compilation input and call 2 produced the accepted SEALED P0 INPUT correction
- Generated: 2026-08-06
- Decoded artifact: RGB PNG, 1536 x 1024 pixels
- SHA-256: b0f01c565ac7493a1e31a4cf70d60a4d5d5a24218963972be65119acd102b6f4

No third-party meme template. Apache-2.0 distribution scope only.

The image uses short labels and pictograms instead of explanatory paragraphs. P-layer cards remain non-sequential: there are no pipeline arrows between responsibility stations. Neural internal edges do not grant Brain authority. Dependencies remain an explicitly declared DAG as defined by SPEC.md. Station placement does not imply runtime or compile order.

### brain-role-overview.svg

Cute structural map of the same four regions and binding rules. It keeps P0-P6 disconnected, depicts Actor/Role capability, shows sealed deterministic Compilation, and places Neural Runtime in a separate orthogonal band with no cross-zone authority arrows. The source is a UTF-8 SVG accessibility wrapper with `<title>` and `<desc>` around the accepted OpenAI-generated visual; no external fonts, URLs, or scripts. Editorial documentation, not a SPEC.md replacement. OpenAI call accounting: 2/2 for this slot; the second call removed cross-zone Neural arrows and labeled SEALED P0. Embedded PNG: 1619 x 971, SHA-256 `645c062c938c1adf40103506a1dd0dcaab6b22da5b31ef3585ebaa5f8417cb77`. Wrapper file: brain-role-overview.svg, SHA-256: `f228df01e7390750e31987eab29b77046732da7d21e7656cd91efa12049beba5`.

### brain-role-flow.svg

Cute CLI-true offline flow in brain-role-flow.svg: public bundle to public-boundary to validate to validate-neural, then three visually independent branches for compile / compile-connectome / simulate and their compiled.json / connectome.json / trace.json artifacts. Deploy/publish remains outside and MAKE VERIFY is an unconnected footer badge. Soft gray rounded arrows terminate once at destination cards. OpenAI call accounting: 2/2 for this slot; both generated candidates retained ambiguous fanout, so the accepted candidate received a deterministic local connector-only repair with no additional provider call. The source is a UTF-8 SVG accessibility wrapper with `<title>` and `<desc>` around the final visual; no external fonts, URLs, or scripts. Embedded PNG: 1672 x 941, SHA-256 `6ac29085c9e3d31d3139d4bfe33566987c971d49324cd03a14226ddd4063ec65`. Wrapper SHA-256: `67d566d3ae323c55084375361d18a90a408c793d3f44a76828de2749c6abcee7`.
