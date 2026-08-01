# Tutorial: validate and export a synthetic instance

1. Install the declared environment: `uv sync --all-groups`.
2. Run `uv run brain-role validate examples/minimal-public --format json`.
3. Expect exit 0 and `"valid":true`.
4. Run `uv run brain-role render hermes examples/minimal-public --output .artifacts/hermes`.
5. Inspect `.artifacts/hermes/prefill_messages.json`.

The exporter only writes that selected output tree. It does not activate or configure Hermes.
