.PHONY: test lint check-contracts

test:
	uv run python -m pytest packages/cattykit/tests
	uv run python -m pytest packages/cattycam/tests
	uv run python -m pytest models/copycat/tests/unit
	uv run python -m pytest models/copycat/tests/reproduction --basic

lint:
	uv run ruff check .

check-contracts:
	uv run --group dev crosshair check \
		packages/cattykit/cattykit \
		packages/cattykit/tests \
		packages/cattycam/cattycam \
		packages/cattycam/tests \
		models/copycat/copycat \
		models/copycat/tests
