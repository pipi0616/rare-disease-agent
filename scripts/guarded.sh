#!/usr/bin/env bash
# Run one command on this shared 16 GB machine without fighting other jobs for memory:
#
#   scripts/guarded.sh COMMAND [ARGS...]
#
# It waits until memory is free, runs the command, pauses it (SIGSTOP) while memory is
# short and resumes it afterwards. The same guard as scripts/run_exam.sh, for the steps
# that are not test runs: building the case-report set, reading it into terms.
set -uo pipefail

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

descendants() {  # every process below pid $1
  ps -axo pid=,ppid= | awk -v root="$1" '{parent[$1] = $2}
    END {for (p in parent) {q = p; while ((q in parent) && q != root && q != 1) q = parent[q]
         if (q == root && p != root) print p}}'
}
signal_tree() { kill "-$1" "$2" $(descendants "$2") 2>/dev/null; }

# While a run works: if memory runs short for a minute, the run is paused (SIGSTOP: it uses
# no processor and its memory can be swapped out), and resumed when memory is free again.
# Stopping it for good would throw away what it had paid for; a paused run loses at most the
# model calls that were in flight, which the client retries or `--fill-in` asks again.
watch_memory() {
  local low=0 paused=0
  while kill -0 "$1" 2>/dev/null; do
    if [ "$paused" = 1 ]; then
      if memory_is_free; then
        echo "memory is free again ($state): resuming the run  $(date '+%H:%M:%S')"
        signal_tree CONT "$1"; paused=0; low=0
      fi
      sleep 30; continue
    fi
    local free swap big
    free=$(free_percent); swap=$(swap_used_mb); big=$(biggest_mb)
    if [ "${free:-100}" -lt 7 ] || [ "${swap:-0}" -gt 10000 ] || [ "${big:-0}" -gt 9000 ]; then
      low=$((low + 1))
    else
      low=0
    fi
    if [ "$low" -ge 2 ]; then
      echo "memory short (free ${free}%, swap ${swap} MB, largest ${big} MB): pausing the run  $(date '+%H:%M:%S')"
      signal_tree STOP "$1"; paused=1
    fi
    sleep 30
  done
}

wait_for_memory || exit 4
"$@" &
pid=$!
watch_memory "$pid" &
watcher=$!
wait "$pid"
status=$?
kill "$watcher" 2>/dev/null; wait "$watcher" 2>/dev/null
exit $status
