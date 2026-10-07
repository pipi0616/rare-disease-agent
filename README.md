# raredx — rare-disease diagnosis agent

An agent that takes a patient's clinical findings (free text or HPO terms,
optionally with candidate variants), decides what to look up, and returns
ranked candidate diseases and genes with cited evidence. Evaluated on public,
leakage-controlled case collections against classical, fixed-pipeline and
single-call baselines.

**Status:** skeleton. Nothing works yet beyond `raredx` printing a greeting.

## Run

```bash
uv sync        # create the environment from uv.lock
uv run raredx  # the CLI entry point
```

## Check

```bash
uv run pre-commit install --hook-type pre-commit --hook-type pre-push  # once per clone
uv run pre-commit run --all-files   # ruff, mypy and the hygiene hooks, by hand
uv run pytest                       # the test suite (also runs before every push)
```

## Layout

```
src/raredx/     all application code — an installed package, no path hacks
tests/          pytest suite; one test per behaviour
docs/           plan and design notes; start with docs/00_plan.md
docs/notebook/  step-by-step engineering notebooks (Chinese): what each step did and why
```
