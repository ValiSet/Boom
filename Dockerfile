FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml poetry.lock* ./
COPY uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen

COPY ./app /app