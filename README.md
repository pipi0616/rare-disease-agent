# raredx — rare-disease diagnosis agent

[![CI](https://github.com/pipi0616/rare-disease-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/pipi0616/rare-disease-agent/actions/workflows/ci.yml)

An agent that takes a patient's clinical findings (free text or HPO terms,
optionally with candidate variants), decides what to look up, and returns
ranked candidate diseases and genes with cited evidence. Evaluated on public,
leakage-controlled case collections against classical, fixed-pipeline and
single-call baselines.

**Status:** the first agent, five tools, and the baselines it is measured against. Tools:
`rank_diseases` (every OMIM disease ranked against the patient's phenotype),
`lookup_disease` (one disease's features with their frequencies, inheritance,
onset, genes and sources, sized for a model to read), `check_match` (the
patient's findings against one disease: explained, unexplained, contradicted,
and the disease's frequent features the patient lacks), `find_disease` (a
disease's OMIM id from its name) and `find_similar_patients` (the published
patients whose phenotype is closest, with their confirmed diagnoses). On the
200-case dev set (recall of the confirmed disease, 95% intervals):

| system | top-1 | top-10 |
|---|---|---|
| agent: the model calls the four tools as it decides, up to 8 turns | **39.0%** [32.5–45.9] | 54.0% [47.1–60.8] |
| fixed pipeline: the tools' top 10 with their evidence, ranked by one model call | 35.5% [29.2–42.3] | 54.5% [47.6–61.3] |
| rank, then check: T2's top 30 reordered by findings explained (no model) | 30.5% | 54.5% [47.6–61.3] |
| nearest published patients alone (tool T5, no model) | 29.0% | 46.5% [39.7–53.4] |
| phenotype similarity alone (tool T2, no model) | 19.0% | 49.0% [42.2–55.9] |
| a single call to `deepseek-flash`, no tools | 14.5% | 28.0% [22.2–34.6] |
| floor: the same diseases for every patient | 0.5% | 9.0% |

The phenotype tool scores 82.0% if a case's own source paper is left in its
knowledge: HPO curated many disease annotations from the very papers these
cases come from. Every evaluation therefore masks each case's paper from the
knowledge the tools read; the 49.0% is the masked number.
Masked, 41 of the 200 confirmed diseases have no phenotype left in HPO —
mostly diseases known from that single paper — so phenotype ranking alone
cannot pass about 80% here.

The fixed pipeline's gain at first place is paired, not just a higher rate:
on the same 200 cases it was right where rank-then-check was wrong 11 times,
and the reverse once (sign test p = 0.006), for about $0.27 a run.
The agent's lead over the fixed pipeline is not established yet: paired at
first place it is 14 cases to 7 (p = 0.19), and at top-10 10 to 11. Its ten
top-10 wins are all diseases the ranking never showed it — ones it thought
of, found by name and checked — while it often listed fewer than ten
answers. It costs about $1.17 a run at peak price ($0.58 off-peak).

An error analysis of the agent's 122 first-place misses, computed from its
traces, found 77 retrieval failures — the right disease never appeared in any
tool output — and 45 judgment failures. The next tools target them, and a
seeded variant (`seeded-agent`) starts from the fixed pipeline's evidence and
fills a short answer list from the tools' order. They are evaluated together
on dev-200, with one ablation run per tool.

The first of them, nearest published patients, beats the disease ranking at
first place on its own (35 cases to 15 paired, p = 0.007), and the two find
different diseases: either one's top 10 holds the confirmed disease about
half the time, the two together 59.5%. Its bank is the design split, each
case's own paper masked; bank and cases share one curation style, so the
number is likely optimistic for a clinician's free-text findings.

## Run

```bash
uv sync                    # create the environment from uv.lock
uv run raredx data fetch   # download every pinned source into data/raw, verify each sha256
uv run raredx data build   # parse it into data/processed: one case per line
uv run raredx data stats   # 10,374 published cases, 780 OMIM diseases, 699 genes
uv run raredx eval check   # the frozen manifests keep every rule
uv run raredx llm check    # model key and endpoint; costs nothing
uv run raredx eval run --system rank-then-check --split dev-200  # run, score, record in MLflow
uv run raredx eval run --system llm-direct --split ci-20     # the model baseline (billed)
uv run raredx eval runs --split dev-200                      # every recorded run on dev-200
uv run raredx eval compare <run id> <run id>                 # two runs, question by question
uv run raredx eval score <run id>                            # re-score recorded traces, no re-run
uv run mlflow ui --port 5050                                 # browse runs at http://127.0.0.1:5050
```

Scoring rules are fixed in `src/raredx/evals/scoring.py`: a disease counts when
its OMIM number matches, a gene when its symbol matches; a case with no answer
is a miss that stays in the denominator; every top-k rate carries a 95% Wilson
interval. Systems only ever see a `Question` (the phenotype), never the answer,
and while a system works on a case, the case's source paper is masked from the
knowledge its tools read (`src/raredx/knowledge/masking.py`).

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
`evals/datasets.toml` (every source — the cases and the HPO release the tools
read — with its version, URL, per-file checksums and licence)
and `evals/splits/` (frozen case-ID manifests):

| manifest | cases | used for |
|---|---|---|
| `dev-200` | 200, one per source paper | every change |
| `design` | 6,014 | confirming a change at full size |
| `ci-20` | 20 of dev-200 | the regression check in CI |
| `heldout` | 4,360 | the final run, once |

## Tools over MCP

The tools are served over the Model Context Protocol, the standard way AI
applications call tools (`src/raredx/mcp_server.py`, the official MCP Python SDK):

```bash
uv run raredx mcp                              # stdio: a host launches this command
uv run raredx mcp --transport streamable-http  # or serve the tools at a URL
```

Claude Code picks the server up from `.mcp.json` when it is opened in this
folder (it asks before running it). Any other host — Claude Desktop, an IDE, a
LangGraph agent — takes the same launch command:
`uv run --directory /absolute/path/to/rare-disease-agent raredx mcp`.
The schemas a model sees are generated from the tools' signatures and
docstrings; an unknown disease id comes back as a tool error the model can act
on; every tool is marked read-only. Calls are traced in the MLflow experiment
`mcp-server`.

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
  knowledge/      reference knowledge the tools read (HPO), and source masking
  tools/          the agent's tools: typed, described, tested alone, traced
  baselines/      systems the agent must beat: similarity, rank-then-check, the fixed
                  pipeline, one LLM call
  llm.py          the model client (OpenAI SDK, MLflow autologging)
  agent.py        the agent: LangChain's create_agent over the tools, with its bounds
  mcp_server.py   the tools over MCP, for any host or agent framework
  mlflow_setup.py process-wide MLflow settings, applied before mlflow loads
evals/          dataset registry and frozen manifests — what gets evaluated
tests/          pytest suite; one test per behaviour, no network, no real data
docs/           plan and design notes; start with docs/00_plan.md
docs/notebook/  step-by-step engineering notebooks (Chinese): what each step did and why
```
