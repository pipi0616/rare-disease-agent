#!/usr/bin/env bash
# The tests of docs/exam_plan.md, one run after another (two runs at once lose traces:
# MLflow's store is one SQLite file). Each run's output goes to its own log, and its
# MLflow run id to a table, so the report can be made without looking anything up.
#
#   scripts/run_exam.sh LOG_DIR patients       MyGene2 and CADA's test set: baselines, the model
#                                            asked directly, agent v1.1
#   scripts/run_exam.sh LOG_DIR casereports    the case-report test: baselines, direct, agent v2
#   scripts/run_exam.sh LOG_DIR gpt            GPT-6.1 asked directly, on MyGene2 only
#
# A run that already has a line in the table is skipped: the script can be started again
# after an interruption without asking any system twice.
set -uo pipefail

logs="$1"; mode="$2"
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

case "$mode" in
  patients)
    for split in mygene2 cada-test; do
      run rank-then-check "$split" --system rank-then-check
      run lirical "$split" --system lirical
      run llm-direct "$split" --system llm-direct
      run agent-v1.1 "$split" --system hypothesis-agent
    done ;;
  casereports)
    run rank-then-check casereports-exam --system rank-then-check
    run one-way-merged casereports-exam --system phenotype-rank --orphanet --similarity resnik/oneway
    run lirical casereports-exam --system lirical
    run llm-direct casereports-exam --system llm-direct
    run agent-v2 casereports-exam --system agent-v2 ;;
  gpt)
    run gpt-6.1 mygene2 --system llm-direct --model openrouter:openai/gpt-6.1-sol --budget-usd 1.5 ;;
  *) echo "unknown mode: $mode" >&2; exit 2 ;;
esac
