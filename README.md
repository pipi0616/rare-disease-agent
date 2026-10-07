# raredx — rare-disease diagnosis agent

[![CI](https://github.com/pipi0616/rare-disease-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/pipi0616/rare-disease-agent/actions/workflows/ci.yml)

An agent that takes a patient's clinical findings (free text or HPO terms,
optionally with candidate variants), decides what to look up, and returns
ranked candidate diseases and genes with cited evidence. Evaluated on public,
leakage-controlled case collections against classical, fixed-pipeline and
single-call baselines.

**Status:** data layer. The evaluation set loads; no model is called yet.

## Run

```bash
uv sync                    # create the environment from uv.lock
uv run raredx data fetch   # Phenopacket Store release, checksum-verified, into ./data
uv run raredx data stats   # 10,374 published cases, 780 OMIM diseases, 699 genes
```

Data never enters git: `data/` is ignored and `raredx data fetch` recreates it
byte-for-byte (release version and sha256 are pinned in `src/raredx/data/phenopackets.py`).

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
  data/           datasets: fetch, verify, parse, split
tests/          pytest suite; one test per behaviour, no network, no real data
docs/           plan and design notes; start with docs/00_plan.md
docs/notebook/  step-by-step engineering notebooks (Chinese): what each step did and why
```
