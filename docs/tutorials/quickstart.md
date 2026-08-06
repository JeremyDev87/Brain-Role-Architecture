# Tutorial: validate and compile a synthetic instance

1. Install the declared environment: `uv sync --all-groups`.
2. Run `uv run brain-role validate examples/minimal-public --format json`.
3. Expect exit 0 and `"valid":true`.
4. Run `uv run brain-role compile examples/minimal-public --output .artifacts/compiled.json`.
5. Inspect `.artifacts/compiled.json` and its reported SHA-256 digest.

The compiler writes only the selected deterministic artifact and does not activate or configure an external runtime.
