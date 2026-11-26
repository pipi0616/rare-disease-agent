#!/usr/bin/env bash
# Take over a test run that is already going (its script was stopped to change the memory
# guard): guard it until it ends, write its line in the run table, then go on with the
# remaining runs.
#
#   scripts/adopt_run.sh LOG_DIR SPLIT NAME PID [paused]
set -uo pipefail
. "$(dirname "$0")/memory_guard.sh"
logs="$1"; split="$2"; name="$3"; pid="$4"
echo "adopted $split  $name  pid $pid  $(date '+%H:%M:%S')"
watch_memory "$pid" "${5:-}"
log="$logs/${split}__${name}.log"
run_id=$(grep -a -o 'MLflow: experiment [^ ]*, run [0-9a-f]\{32\}' "$log" | tail -1 | grep -a -o '[0-9a-f]\{32\}$')
if [ -n "$run_id" ] && ! grep -q "^${split}	${name}	" "$logs/runs.tsv"; then
  printf '%s\t%s\t%s\n' "$split" "$name" "$run_id" >> "$logs/runs.tsv"
fi
tr '\r' '\n' < "$log" | grep -a -v 'Evaluating\|Warning\|query_points' | tail -6
echo "done  $split  $name  (adopted)  $(date '+%H:%M:%S')"
"$(dirname "$0")/run_exam.sh" "$logs" patients && "$(dirname "$0")/run_exam.sh" "$logs" patients-lirical
