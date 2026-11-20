#!/usr/bin/env bash
# The tests of docs/exam_plan.md, one run after another (two runs at once lose traces:
# MLflow's store is one SQLite file). Each run's output goes to its own log, and its
# MLflow run id to a table, so the report can be made without looking anything up.
#
#   scripts/run_exam.sh LOG_DIR SPLIT...        the systems billed by DeepSeek, and the free ones
#   scripts/run_exam.sh LOG_DIR --others SPLIT...   other providers' models, asked directly
#
# A run that already has a line in the table is skipped: the script can be started again
# after an interruption without asking any system twice.
set -uo pipefail

logs="$1"; shift
others=0
if [ "${1:-}" = "--others" ]; then others=1; shift; fi
mkdir -p "$logs"
table="$logs/runs.tsv"
[ -f "$table" ] || printf 'split\tname\trun_id\n' > "$table"

run() {  # run NAME SPLIT ARGS...
  local name="$1" split="$2"; shift 2
  if grep -q "^${split}	${name}	" "$table"; then
    echo "skip  $split  $name  (already run)"; return 0
  fi
  local log="$logs/${split}__${name}.log"
  echo "start $split  $name  $(date '+%H:%M:%S')"
  uv run raredx eval run --split "$split" --final "$@" > "$log" 2>&1
  local status=$?
  local run_id
  run_id=$(grep -o 'run [0-9a-f]\{32\}' "$log" | tail -1 | cut -d' ' -f2)
  if [ -n "$run_id" ]; then printf '%s\t%s\t%s\n' "$split" "$name" "$run_id" >> "$table"; fi
  tr '\r' '\n' < "$log" | grep -v 'Evaluating\|Warning\|query_points' | tail -6
  echo "done  $split  $name  exit $status"
}

for split in "$@"; do
  if [ "$others" = 1 ]; then
    run gpt-6.1 "$split" --system llm-direct --model openrouter:openai/gpt-6.1-sol --budget-usd 3
    run claude-sonnet-5.5 "$split" --system llm-direct --model openrouter:anthropic/claude-sonnet-5.5 --budget-usd 3
    run gemini-4 "$split" --system llm-direct --model openrouter:google/gemini-4-argon --budget-usd 3
  else
    run rank-then-check "$split" --system rank-then-check
    run one-way-merged "$split" --system phenotype-rank --orphanet --similarity resnik/oneway
    run lirical "$split" --system lirical
    run llm-direct "$split" --system llm-direct
    run agent-v2 "$split" --system agent-v2
    run agent-v1.1 "$split" --system hypothesis-agent
  fi
done
