# syntax=docker/dockerfile:1

FROM node:22-bookworm-slim AS frontend
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@9 --activate
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml tsconfig.base.json ./
COPY artifacts ./artifacts
RUN pnpm install --frozen-lockfile
RUN pnpm typecheck && pnpm build

FROM python:3.11-slim AS runtime
COPY --from=ghcr.io/astral-sh/uv:0.11.33 /uv /uvx /bin/
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH=/app/.venv/bin:$PATH \
    REPOGUARD_CACHE_DB=/data/repoguard-cache.sqlite3 \
    REPOGUARD_TELEMETRY_DB=/data/repoguard-commerce.sqlite3 \
    TMPDIR=/tmp/repoguard
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system repoguard \
    && useradd --system --gid repoguard --home-dir /app --shell /usr/sbin/nologin repoguard \
    && mkdir -p /data /tmp/repoguard \
    && chown -R repoguard:repoguard /data /tmp/repoguard
COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-dev --no-install-project
COPY backend /app/backend
COPY --from=frontend /app/artifacts /app/artifacts
RUN mkdir -p /data /tmp/repoguard \
    && chown -R repoguard:repoguard /app /data /tmp/repoguard
WORKDIR /app/backend
USER repoguard
EXPOSE 8080
CMD ["python", "run.py"]
