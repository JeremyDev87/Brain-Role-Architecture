.PHONY: sync lint type test spec-check boundary-check docs-check build smoke verify

sync:
	uv sync --frozen --all-groups --no-editable

lint:
	uv run --no-sync ruff check .

type:
	uv run --no-sync mypy src

test:
	uv run --no-sync pytest -q

spec-check:
	uv run --no-sync python scripts/check_spec_schema_sync.py

boundary-check:
	uv run --no-sync python scripts/check_public_boundary.py

docs-check:
	uv run --no-sync python scripts/check_docs.py

build:
	rm -rf .artifacts/dist
	uv build --no-sources --out-dir .artifacts/dist

smoke: build
	uv run --no-sync python scripts/smoke_distribution.py

verify: sync lint type test spec-check boundary-check docs-check smoke
