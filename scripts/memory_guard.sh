# Memory guard for a shared 16 GB machine. Sourced by run_exam.sh and guarded.sh.
#
# On 2026-11-21 another job of the user's (PyTorch on Metal, 9-18 GB) and a run of ours
# together ended in a kernel panic. So: a run starts or resumes only when memory is free,
# and is paused at once (SIGSTOP: no processor, and its memory can be swapped out) when
# memory runs short. A paused run keeps what it has paid for; the model calls in flight
# are retried by the client, or asked again with --fill-in.
#
# `memory_pressure`'s "free percentage" and `ps` both miss a job whose memory is in swap or
# in the compressor: the guard also reads swap in use and `top`'s footprint of the largest
# process. Thresholds sit well under the load that panicked the machine (a 13 GB job
# beside 2 GB of ours).
free_percent() { memory_pressure 2>/dev/null | sed -n 's/.*free percentage: \([0-9]*\)%.*/\1/p' | tail -1; }
swap_used_mb() { sysctl -n vm.swapusage 2>/dev/null | sed -n 's/.*used = \([0-9]*\)\..*/\1/p'; }
biggest_mb() {
  top -l 1 -o mem -n 1 -stats mem 2>/dev/null | tail -1 | awk '{v=$1}
    v ~ /G/ {sub(/G.*/, "", v); print int(v * 1024); next}
    v ~ /M/ {sub(/M.*/, "", v); print int(v); next}
    {print 0}'
}
read_memory() {
  mem_free=$(free_percent); mem_swap=$(swap_used_mb); mem_big=$(biggest_mb)
  state="free ${mem_free}%, swap used ${mem_swap} MB, largest process ${mem_big} MB"
}
memory_is_free() {  # room to start or resume
  read_memory
  [ "${mem_free:-0}" -ge "${MIN_FREE:-25}" ] && [ "${mem_swap:-99999}" -lt "${MAX_SWAP_MB:-8500}" ] \
    && [ "${mem_big:-99999}" -lt "${MAX_PROCESS_MB:-8500}" ]
}
memory_is_short() {  # pause now
  read_memory
  [ "${mem_free:-100}" -lt "${LOW_FREE:-12}" ] || [ "${mem_swap:-0}" -gt "${HIGH_SWAP_MB:-10000}" ] \
    || [ "${mem_big:-0}" -gt "${HIGH_PROCESS_MB:-10000}" ]
}

wait_for_memory() {
  local waited=0
  until memory_is_free; do
    if [ "$waited" -ge "${MAX_WAIT_S:-172800}" ]; then echo "gave up waiting for memory ($state)"; return 1; fi
    [ $((waited % 1800)) -eq 0 ] && echo "waiting for memory: $state  $(date '+%H:%M:%S')"
    sleep 30; waited=$((waited + 30))
  done
  echo "memory is free: $state  $(date '+%H:%M:%S')"
}

descendants() {  # every process below pid $1
  ps -axo pid=,ppid= | awk -v root="$1" '{parent[$1] = $2}
    END {for (p in parent) {q = p; while ((q in parent) && q != root && q != 1) q = parent[q]
         if (q == root && p != root) print p}}'
}
signal_tree() { kill "-$1" "$2" $(descendants "$2") 2>/dev/null; }

# watch_memory PID [paused]: until the process ends, pause it while memory is short and
# resume it when memory is free again. Give "paused" for a process already stopped.
watch_memory() {
  local paused=0 pauses=0
  [ "${2:-}" = "paused" ] && paused=1
  while kill -0 "$1" 2>/dev/null; do
    if [ "$paused" = 1 ]; then
      if memory_is_free; then
        echo "resuming ($state)  $(date '+%H:%M:%S')"
        signal_tree CONT "$1"; paused=0
      fi
      sleep 20; continue
    fi
    if memory_is_short; then
      pauses=$((pauses + 1))
      echo "pausing, time $pauses ($state)  $(date '+%H:%M:%S')"
      signal_tree STOP "$1"; paused=1
    fi
    sleep 15
  done
}
