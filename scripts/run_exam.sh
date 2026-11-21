#!/usr/bin/env bash
# The tests of docs/exam_plan.md, one run after another (two runs at once lose traces:
# MLflow's store is one SQLite file). Each run's output goes to its own log, and its
# MLflow run id to a table, so the report can be made without looking anything up.
#
#   scripts/run_exam.sh LOG_DIR patients       MyGene2 and CADA's test set: the no-model baseline,
#                                            the model asked directly, agent v1.1
#   scripts/run_exam.sh LOG_DIR patients-lirical   LIRICAL on the same two sets
#   scripts/run_exam.sh LOG_DIR casereports    the case-report test: baselines, direct, agent v2
#   scripts/run_exam.sh LOG_DIR gpt            GPT-6.1 asked directly, on MyGene2 only
#
# A run that already has a line in the table is skipped: the script can be started again
# after an interruption without asking any system twice.
set -uo pipefail

logs="$1"; mode="$2"
# The tests are recorded in a store of their own. The project's store has grown to 14 GB,
# and a run on it lost 11 of 146 records to "database is locked" (2026-11-20; the run was
# void and unscored). A small store writes fast; fewer parallel workers write less at once.
export RAREDX_MLFLOW_TRACKING_URI="sqlite:///data/mlflow-exam-2026-11.db"
# MLflow's evaluation sizes its thread pool from a request rate when this is unset: about
# fifty threads. With LIRICAL each thread is a Java process, and fifty of them filled a
# 16 GB machine (2026-11-20). Always set; LIRICAL gets three (below).
export MLFLOW_GENAI_EVAL_MAX_WORKERS=4
mkdir -p "$logs"
# One script at a time: two at once ask every system twice and write to one store together
# (it happened on 2026-11-20; both copies' unfinished runs were void).
lock="$logs/.lock"
if [ -f "$lock" ] && kill -0 "$(cat "$lock")" 2>/dev/null; then
  echo "another run_exam.sh (pid $(cat "$lock")) is using $logs" >&2; exit 3
fi
echo $$ > "$lock"; trap 'rm -f "$lock"' EXIT
table="$logs/runs.tsv"
[ -f "$table" ] || printf 'split\tname\trun_id\n' > "$table"

# This machine has 16 GB and is shared: a run starts only when memory is free and is paused
# while memory is short (scripts/memory_guard.sh).
. "$(dirname "$0")/memory_guard.sh"

run() {  # run NAME SPLIT ARGS...
  local name="$1" split="$2"; shift 2
  if grep -q "^${split}	${name}	" "$table"; then
    echo "skip  $split  $name  (already run)"; return 0
  fi
  local log="$logs/${split}__${name}.log"
  wait_for_memory || exit 4
  echo "start $split  $name  $(date '+%H:%M:%S')"
  uv run raredx eval run --split "$split" --final "$@" > "$log" 2>&1 &
  local pid=$!
  watch_memory "$pid" &
  local watcher=$!
  wait "$pid"
  local status=$?
  kill "$watcher" 2>/dev/null; wait "$watcher" 2>/dev/null
  local run_id
  # -a: the log holds a progress bar's control characters, and grep would call it binary
  run_id=$(grep -a -o 'MLflow: experiment [^ ]*, run [0-9a-f]\{32\}' "$log" | tail -1 | grep -a -o '[0-9a-f]\{32\}$')
  if [ -n "$run_id" ]; then printf '%s\t%s\t%s\n' "$split" "$name" "$run_id" >> "$table"; fi
  tr '\r' '\n' < "$log" | grep -a -v 'Evaluating\|Warning\|query_points' | tail -6
  echo "done  $split  $name  exit $status"
}

case "$mode" in
  patients)
    for split in mygene2 cada-test; do
      run rank-then-check "$split" --system rank-then-check
      run llm-direct "$split" --system llm-direct
      run agent-v1.1 "$split" --system hypothesis-agent
    done ;;
  patients-lirical)  # last: slow, free, and one Java process per worker
    export MLFLOW_GENAI_EVAL_MAX_WORKERS=3
    run lirical mygene2 --system lirical
    run lirical cada-test --system lirical ;;
  casereports)
    run rank-then-check casereports-exam --system rank-then-check
    run one-way-merged casereports-exam --system phenotype-rank --orphanet --similarity resnik/oneway
    run llm-direct casereports-exam --system llm-direct
    run agent-v2 casereports-exam --system agent-v2
    export MLFLOW_GENAI_EVAL_MAX_WORKERS=3
    run lirical casereports-exam --system lirical ;;
  gpt)
    run gpt-6.1 mygene2 --system llm-direct --model openrouter:openai/gpt-6.1-sol --budget-usd 1.5 ;;
  *) echo "unknown mode: $mode" >&2; exit 2 ;;
esac
