# syntax=docker/dockerfile:1
# One Dockerfile for both Python services. Targets:
#   dev       local development (code mounted, all dependency groups)
#   django    production web + Celery image, includes the built Vue assets
# >>> realtime
#   realtime  production FastAPI image
# <<< realtime
# Runtime versions are set once here and in compose.local.yml (ARG defaults).

ARG PYTHON_VERSION=__PYTHON_VERSION__
ARG NODE_VERSION=__NODE_VERSION__
# Pinned on purpose: unsuffixed -slim tags move to a new Debian suite on their own.
ARG DEBIAN_SUITE=__DEBIAN_SUITE__

FROM ghcr.io/astral-sh/uv:__UV_VERSION__ AS uv

# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-${DEBIAN_SUITE} AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    PATH=/opt/venv/bin:$PATH
COPY --from=uv /uv /uvx /usr/local/bin/
WORKDIR /app

# ---------------------------------------------------------------------------
FROM base AS deps-dev
COPY pyproject.toml uv.lock .python-version ./
# --locked fails the build when uv.lock is out of date with pyproject.toml.
# The docs group (MkDocs) is for the dev image only; production installs neither.
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-install-project --group docs

FROM base AS deps-prod
COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-install-project --no-dev

# ---------------------------------------------------------------------------
# Built once on the build machine's platform: the output is plain JS/CSS, so a
# multi-platform build does not repeat (or emulate) it per target platform.
FROM --platform=$BUILDPLATFORM node:${NODE_VERSION}-${DEBIAN_SUITE}-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN PNPM_VERSION="$(node -p "require('./package.json').packageManager.split('@')[1]")" \
    && npm install -g "pnpm@${PNPM_VERSION}"
RUN --mount=type=cache,target=/root/.local/share/pnpm/store pnpm install --frozen-lockfile
COPY frontend/ ./
# Tailwind also scans the Django templates for class names (see src/styles.css).
COPY backend/templates/ /app/backend/templates/
# Type-check and lint run in CI; the image build only bundles.
RUN pnpm run build-only

# ---------------------------------------------------------------------------
FROM base AS dev
ARG USER_ID=1000
ARG GROUP_ID=1000
# --non-unique: the host's IDs may already exist in the image (macOS users have
# GID 20 = dialout; CI runners often run as root, UID/GID 0).
RUN groupadd --non-unique --gid ${GROUP_ID} app \
    && useradd --non-unique --uid ${USER_ID} --gid ${GROUP_ID} --create-home app
COPY --from=deps-dev /opt/venv /opt/venv
COPY docker/app/ /docker/
RUN chmod +x /docker/entrypoint /docker/start-*
USER app
ENTRYPOINT ["/docker/entrypoint"]

# ---------------------------------------------------------------------------
FROM base AS runtime
ARG APP_VERSION=development
# High, fixed IDs and no sudo: a compromised process gains nothing on the host.
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10000 --gid app --home-dir /app app
COPY --from=deps-prod /opt/venv /opt/venv
COPY docker/app/ /docker/
RUN chmod +x /docker/entrypoint /docker/start-*
COPY --chown=app:app backend/ /app/backend/
# >>> realtime
COPY --chown=app:app realtime/ /app/realtime/
# <<< realtime
RUN echo "${APP_VERSION}" > /app/VERSION.txt
ENTRYPOINT ["/docker/entrypoint"]

# >>> realtime
FROM runtime AS realtime
USER app
CMD ["/docker/start-realtime"]
# <<< realtime

FROM runtime AS django
COPY --from=frontend-build --chown=app:app /app/backend/static/vue /app/backend/static/vue
# collectstatic needs importable settings, not real secrets.
RUN DJANGO_SETTINGS_MODULE=backend.config.settings.production \
    DJANGO_SECRET_KEY=build DATABASE_URL=sqlite:////tmp/build.db REDIS_URL=redis://localhost \
    INTERNAL_API_SECRET=build EMAIL_URL=consolemail:// \
    python backend/manage.py collectstatic --noinput \
    && chown -R app:app /app/backend/staticfiles
USER app
CMD ["/docker/start-django"]
