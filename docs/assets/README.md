# README image assets

## `brain-role-meme.png`

An original, AI-assisted editorial cartoon for the multilingual project READMEs. The scene turns the P0-P6
responsibility topology into a deliberately absurd office inside a brain: P6 keeps producing new goals while
P0 calmly protects the invariant boundary.

- **Generation route:** OpenAI through the pinned Hermes still-image route
- **Provider:** `openai-codex`
- **Model:** `gpt-image-2-medium`
- **Mode:** text-to-image, no input or reference images
- **Fallbacks:** none
- **Run call accounting:** 2/2; this artifact came from call 2 after call 1 was rejected for directional
  P-number sequencing
- **Generated:** 2026-08-04
- **Decoded artifact:** RGB PNG, 1536 × 1024 pixels
- **SHA-256:** `0a7adfb7f82feb840dc656c3015ca65da1b513fabebfb3cb277d939f5012c264`

The composition was created without a third-party meme template, logo, character, or reference image. Its
repository use follows the project's Apache-2.0 distribution scope; this note does not make a broader legal
claim about copyrightability or third-party rights.

Each localized README supplies localized alternative text and a localized caption. Text embedded in the image
is limited to the layer identifiers P0-P6 so the same asset remains useful across languages.

The seven stations use an intentionally non-sequential, disconnected layout: there are no arrows, paths,
stacks, or inter-station connectors. The P numbers identify responsibility layers; they do not imply runtime
or compile order. Dependencies remain an explicitly declared DAG as defined by [`SPEC.md`](../../SPEC.md).
