# README image assets

## `brain-role-meme.png`

An original, AI-assisted editorial cartoon for the multilingual project READMEs. The scene turns the seven
responsibility layers into a deliberately absurd office inside a brain: Prefrontal keeps producing new goals
while Brainstem calmly protects the invariant boundary.

- **Generation route:** OpenAI through the pinned project image route
- **Provider:** `openai-codex`
- **Model:** `gpt-image-2-medium`
- **Mode:** image-to-image signage edit from the prior OpenAI-generated project artifact
- **Fallbacks:** none
- **Run call accounting:** 3/3; call 1 was rejected for directional P-number sequencing, call 2 produced the
  accepted disconnected scene, and the owner-approved call 3 replaced its signs with brain-element names only
- **Generated:** 2026-08-04
- **Decoded artifact:** RGB PNG, 1536 × 1024 pixels
- **SHA-256:** `cf81bd082b86ed1570f6c1bbf62d8d85d76790a46b529182f2eeb30243c30f4f`

The composition was created without a third-party meme template, logo, character, or reference image; call 3
used only the project's own call-2 artifact as its input image. Its repository use follows the project's
Apache-2.0 distribution scope; this note does not make a broader legal claim about copyrightability or
third-party rights.

Each localized README supplies localized alternative text and a localized caption. Text embedded in the image
is limited to exactly the seven canonical brain-element names `Brainstem`, `Cerebellum`, `Hippocampus`,
`Amygdala`, `Cortex`, `Ego`, and `Prefrontal`, each shown once. The image contains no P0-P6 identifiers.

The seven stations use an intentionally non-sequential, disconnected layout: there are no arrows, paths,
stacks, or inter-station connectors. The brain-element names identify responsibility stations; their placement
does not imply runtime or compile order. Dependencies remain an explicitly declared DAG as defined by
[`SPEC.md`](../../SPEC.md).

The repository also contains two authored, text-bearing SVG diagrams used by the multilingual READMEs:

### `brain-role-overview.svg`

A deterministic architecture overview of the Brain, Actor/Role, Compilation, and orthogonal Neural Runtime planes.
It explicitly states that P0 is the only absolute invariant and that P numbers do not imply execution or compile order.
The diagram is an editorial documentation asset, not a normative replacement for `SPEC.md`.

### `brain-role-flow.svg`

A deterministic validation, compilation, and simulation flow. It shows public-boundary checks and the artifact
outputs while keeping deployment, publication, and external runtime mutation outside the flow.
Both diagrams are UTF-8 SVG files with embedded `<title>` and `<desc>` metadata; no external fonts, URLs, scripts,
private paths, credentials, or third-party assets are referenced.
