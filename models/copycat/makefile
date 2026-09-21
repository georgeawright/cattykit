.PHONY: reproduction reproduction-full unit tests

reproduction:
	uv run python -m pytest tests/reproduction --basic

reproduction-full:
	uv run python -m pytest -s tests/reproduction --full

unit:
	uv run python -m pytest tests/unit

tests:
	uv run python -m pytest tests
