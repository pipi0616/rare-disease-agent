#!/usr/bin/env bash
# Run one command on this shared 16 GB machine without fighting other jobs for memory:
#
#   scripts/guarded.sh COMMAND [ARGS...]
#
# It waits until memory is free, runs the command, pauses it while memory is short and
# resumes it afterwards (scripts/memory_guard.sh). For the steps that are not test runs:
# building the case-report set, reading it into terms.
set -uo pipefail
. "$(dirname "$0")/memory_guard.sh"

wait_for_memory || exit 4
"$@" &
pid=$!
watch_memory "$pid" &
watcher=$!
wait "$pid"
status=$?
kill "$watcher" 2>/dev/null; wait "$watcher" 2>/dev/null
exit $status
