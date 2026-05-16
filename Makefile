.PHONY: fetch-headers sync clean setup

fetch-headers:
	uv run --env-file .env --package fetcher fetch --headers

fetch-bars:
	uv run --env-file .env --package fetcher fetch --bars

setup:
	uv run --env-file .env apps/setup/main.py

dev-api:
	uv run --env-file .env --package api fastapi dev apps/api/src/api/main.py

sync:
	uv sync

clean:
	rm -rf .venv