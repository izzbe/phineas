FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:0.10.4 /uv /uvx /bin/
WORKDIR /app
COPY ./uv.lock uv.lock
COPY ./pyproject.toml pyproject.toml
COPY ./libraries libraries
COPY ./apps/api apps/api
RUN uv sync --package api
CMD ["uv", "run", "fastapi", "run", "apps/api/src/api/main.py", "--port", "80"]
