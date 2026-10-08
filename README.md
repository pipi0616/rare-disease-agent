# raredx — rare-disease diagnosis agent

[![CI](https://github.com/pipi0616/rare-disease-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/pipi0616/rare-disease-agent/actions/workflows/ci.yml)

An agent that takes a patient's clinical findings (free text or HPO terms,
optionally with candidate variants), decides what to look up, and returns
ranked candidate diseases and genes with cited evidence. Evaluated on public,
leakage-controlled case collections against classical, fixed-pipeline and
single-call baselines.

**Status:** first model baseline. On the 200-case dev set, a single call to
`deepseek-flash` (no tools) finds the confirmed disease in its top 10 for
28.0% of patients [22.2–34.6], against a 9.0% floor that ignores the
phenotype; top-1 is 14.5%. The agent has to beat this.

## Run

```bash
uv sync                    # create the environment from uv.lock
uv run raredx data fetch   # download the pinned release into data/raw, verify its sha256
uv run raredx data build   # parse it into data/processed: one case per line
uv run raredx data stats   # 10,374 published cases, 780 OMIM diseases, 699 genes
uv run raredx eval check   # the frozen manifests keep every rule
uv run raredx llm check    # model key and endpoint; costs nothing
uv run raredx eval run --system llm-direct --split ci-20     # run, score, record in MLflow
uv run raredx eval runs --split dev-200                      # every recorded run on dev-200
uv run raredx eval score <run id>                            # re-score recorded traces, no re-run
uv run mlflow ui --port 5050                                 # browse runs at http://127.0.0.1:5050
```

Scoring rules are fixed in `src/raredx/evals/scoring.py`: a disease counts when
its OMIM number matches, a gene when its symbol matches; a case with no answer
is a miss that stays in the denominator; every top-k rate carries a 95% Wilson
interval. Systems only ever see a `Question` (the phenotype), never the answer.

Evaluation runs on MLflow's native GenAI evaluation (`src/raredx/evals/harness.py`):
each frozen manifest is registered as an MLflow evaluation dataset, the scoring
rules are a code-based `@scorer`, and `mlflow.genai.evaluate` asks the system
about every case in parallel. Every question becomes a trace; every evaluation
is an MLflow run with params (system, manifest checksum, dataset version, code
commit), metrics (top-k means plus Wilson bounds) and those traces. A run whose
answers were not all recorded fails instead of reporting a number. The store is
local SQLite (`mlflow.db` + `mlruns/`, both ignored by git); pointing
`RAREDX_MLFLOW_TRACKING_URI` at a shared tracking server is the only change a
team setup needs.

Data never enters git: `data/` is ignored and the commands above recreate it
byte-for-byte. What *is* in git is the definition of what gets evaluated:
`evals/datasets.toml` (every source, its version, URL, checksum and licence)
and `evals/splits/` (frozen case-ID manifests):

| manifest | cases | used for |
|---|---|---|
| `dev-200` | 200, one per source paper | every change |
| `design` | 6,014 | confirming a change at full size |
| `ci-20` | 20 of dev-200 | the regression check in CI |
| `heldout` | 4,360 | the final run, once |

## Model

Any OpenAI-compatible endpoint, through the official OpenAI SDK: DeepSeek by
default (`DEEPSEEK_API_KEY` in a git-ignored `.env`; see `.env.example`), or a
self-hosted vLLM server by setting `RAREDX_LLM_BASE_URL` and
`RAREDX_LLM_MODEL`. `mlflow.openai.autolog()` records every model call inside
the question's trace, and each run logs tokens, seconds per case and a cost
estimate. MLflow telemetry is switched off, so nothing is reported off the
machine (`src/raredx/mlflow_setup.py`).

## Check

```bash
uv run pre-commit install --hook-type pre-commit --hook-type pre-push  # once per clone
uv run pre-commit run --all-files   # ruff, mypy and the hygiene hooks, by hand
uv run pytest                       # the test suite (also runs before every push)
```

## Layout

```
src/raredx/     all application code — an installed package, no path hacks
  cli.py          the `raredx` command; thin
  config.py       settings from RAREDX_* environment variables / .env
  data/           datasets: registry, fetch, verify, parse, processed layer
  evals/          manifests, systems, scoring rules, MLflow evaluation harness
  baselines/      systems the agent must beat: the single-call LLM baseline
  llm.py          the model client (OpenAI SDK, MLflow autologging)
  mlflow_setup.py process-wide MLflow settings, applied before mlflow loads
evals/          dataset registry and frozen manifests — what gets evaluated
tests/          pytest suite; one test per behaviour, no network, no real data
docs/           plan and design notes; start with docs/00_plan.md
docs/notebook/  step-by-step engineering notebooks (Chinese): what each step did and why
```
