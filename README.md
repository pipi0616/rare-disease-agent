# raredx — rare-disease diagnosis agent

[![CI](https://github.com/pipi0616/rare-disease-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/pipi0616/rare-disease-agent/actions/workflows/ci.yml)

An agent that takes a patient's clinical findings (free text or HPO terms,
optionally with candidate variants), decides what to look up, and returns
ranked candidate diseases and genes with cited evidence. Evaluated on public,
leakage-controlled case collections against classical, fixed-pipeline and
single-call baselines.

**Status:** evaluation sets frozen. No model is called yet.

## Run

```bash
uv sync                    # create the environment from uv.lock
uv run raredx data fetch   # download the pinned release into data/raw, verify its sha256
uv run raredx data build   # parse it into data/processed: one case per line
uv run raredx data stats   # 10,374 published cases, 780 OMIM diseases, 699 genes
uv run raredx eval check   # the frozen manifests keep every rule
```

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
  evals/          evaluation manifests (and, next, the scorer)
evals/          dataset registry and frozen manifests — what gets evaluated
tests/          pytest suite; one test per behaviour, no network, no real data
docs/           plan and design notes; start with docs/00_plan.md
docs/notebook/  step-by-step engineering notebooks (Chinese): what each step did and why
```
