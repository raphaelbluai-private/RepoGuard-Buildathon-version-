# syntax=docker/dockerfile:1

FROM node:22-bookworm-slim AS frontend
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@9 --activate
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml tsconfig.base.json ./
COPY artifacts ./artifacts
RUN pnpm install --frozen-lockfile
RUN pnpm typecheck && pnpm build

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TMPDIR=/tmp/repoguard
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system repoguard \
    && useradd --system --gid repoguard --home-dir /app --shell /usr/sbin/nologin repoguard
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
COPY backend /app/backend
COPY --from=frontend /app/artifacts /app/artifacts
RUN mkdir -p /data /tmp/repoguard \
    && chown -R repoguard:repoguard /app /data /tmp/repoguard
WORKDIR /app/backend
USER repoguard
EXPOSE 8080
CMD ["python", "run.py"]
