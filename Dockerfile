# syntax=docker/dockerfile:1
#
# The service as a container image: the code, its locked dependencies, and the
# pinned knowledge it reads — everything an answer depends on, as one versioned
# artifact. No secret is in it: the model API key arrives in the environment at
# run time (see compose.yaml), and .dockerignore keeps .env out of the build.
#
#   docker build --build-arg VERSION=$(git rev-parse --short HEAD) -t raredx .
#   docker run --rm -p 8000:8000 raredx          # no key: answers from the tools alone
#
# Three stages, so the final image holds no build tool and no download cache.

# ── build: the locked dependencies and the package, into a virtual environment ──
FROM python:3.12-slim-bookworm AS build
COPY --from=ghcr.io/astral-sh/uv:0.12.3 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never UV_NO_CACHE=1
WORKDIR /app
# Dependencies first, from the lockfile alone: this layer is rebuilt only when
# uv.lock changes, not on every change to the code. `dev` (tests, linters,
# notebooks) is left out; `demo` (the Streamlit page) is in.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-default-groups --group demo
COPY README.md ./
COPY src ./src
RUN uv sync --locked --no-editable --no-default-groups --group demo

# ── data: the pinned knowledge, downloaded and checked against the registry ──
# evals/datasets.toml names each file's version and sha256; a download that does
# not match fails the build. Then the published patients are parsed into cases,
# and HPO's names and synonyms embedded for reading notes (the embedding models,
# FastEmbed's, are downloaded once into data/models and run on the CPU).
FROM build AS data
ENV PATH="/app/.venv/bin:$PATH"
COPY evals ./evals
RUN raredx data fetch hpo phenopacket-store && raredx data build && raredx data hpo-index

# ── runtime: what runs ──
FROM python:3.12-slim-bookworm AS runtime
RUN groupadd --system app && useradd --system --gid app --no-create-home app \
    && mkdir -p /app/state && chown app:app /app/state
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
COPY --from=data /app/data /app/data
COPY evals ./evals
# The commit the image was built from: what /v1/system and every answer report.
ARG VERSION=unknown
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    RAREDX_BUILD_VERSION=$VERSION \
    RAREDX_MLFLOW_TRACKING_URI=sqlite:////app/state/mlflow.db \
    RAREDX_MLFLOW_ARTIFACT_ROOT=/app/state/mlruns \
    MLFLOW_DISABLE_TELEMETRY=true
# Not root: a process that only reads its knowledge and answers needs no more.
USER app
EXPOSE 8000
# Liveness, for whatever runs the container. It does not call the model.
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2)"]
CMD ["raredx", "serve", "--host", "0.0.0.0", "--port", "8000"]
