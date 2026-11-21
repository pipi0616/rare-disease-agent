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

# This machine has 16 GB and is shared: on 2026-11-21 another job of the user's (PyTorch on
# Metal, 9-13 GB) and a run of this script together ended in a kernel panic. So a run starts
# only when memory is free, and is stopped if memory runs out while it works. A run stopped
# that way is void (it has no line in the table) and is asked again later.
free_percent() { memory_pressure 2>/dev/null | sed -n 's/.*free percentage: \([0-9]*\)%.*/\1/p' | tail -1; }
swap_used_mb() { sysctl -n vm.swapusage 2>/dev/null | sed -n 's/.*used = \([0-9]*\)\..*/\1/p'; }
# The largest process's memory footprint in MB, as `top` counts it (compressed and swapped
# pages included: `ps` and the "free percentage" both miss a job whose memory is in swap).
biggest_mb() {
  top -l 1 -o mem -n 1 -stats mem 2>/dev/null | tail -1 | awk '{v=$1}
    v ~ /G/ {sub(/G.*/, "", v); print int(v * 1024); next}
    v ~ /M/ {sub(/M.*/, "", v); print int(v); next}
    {print 0}'
}

memory_is_free() {  # nothing large is running, little is in swap, and a third is free
  local free swap big
  free=$(free_percent); swap=$(swap_used_mb); big=$(biggest_mb)
  state="free ${free}%, swap used ${swap} MB, largest process ${big} MB"
  [ "${free:-0}" -ge "${MIN_FREE:-30}" ] && [ "${swap:-99999}" -lt "${MAX_SWAP_MB:-6000}" ] \
    && [ "${big:-99999}" -lt "${MAX_PROCESS_MB:-6000}" ]
}

wait_for_memory() {
  local waited=0
  until memory_is_free; do
    if [ "$waited" -ge "${MAX_WAIT_S:-86400}" ]; then echo "gave up waiting for memory ($state)"; return 1; fi
    [ $((waited % 900)) -eq 0 ] && echo "waiting for memory: $state  $(date '+%H:%M:%S')"
    sleep 60; waited=$((waited + 60))
  done
  echo "memory is free: $state"
}

watch_memory() {  # stop the run (pid $1) if memory runs short for a minute and a half
  local low=0
  while kill -0 "$1" 2>/dev/null; do
    local free swap big
    free=$(free_percent); swap=$(swap_used_mb); big=$(biggest_mb)
    if [ "${free:-100}" -lt 7 ] || [ "${swap:-0}" -gt 10000 ] || [ "${big:-0}" -gt 9000 ]; then
      low=$((low + 1))
    else
      low=0
    fi
    if [ "$low" -ge 3 ]; then
      echo "memory short (free ${free}%, swap ${swap} MB, largest ${big} MB): stopping the run  $(date '+%H:%M:%S')"
      pkill -TERM -P "$1" 2>/dev/null; kill -TERM "$1" 2>/dev/null; sleep 5
      pkill -KILL -P "$1" 2>/dev/null; kill -KILL "$1" 2>/dev/null
      return 0
    fi
    sleep 30
  done
}

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
