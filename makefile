.PHONY: integration unit run tests

integration:
	uv run python -m pytest tests/integration

unit:
	uv run python -m pytest tests/unit

run:
	uv run python -m main


tests:
	uv run python -m pytest tests
