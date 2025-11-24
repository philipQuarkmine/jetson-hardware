#!/bin/bash
set -euo pipefail

DEBUG_ROOT="/sys/kernel/debug/17000000.gpu"
LOG_ROOT="/var/log/nvgpu-debug"
BOOT_ID=$(cat /proc/sys/kernel/random/boot_id)
STAMP=$(date -u +%Y%m%d-%H%M%S)
LOG_FILE="${LOG_ROOT}/${STAMP}-${BOOT_ID}.log"

mkdir -p "$LOG_ROOT"
exec >>"$LOG_FILE" 2>&1

echo "=== nvgpu debug setup $(date -u --iso-8601=seconds) ==="
echo "boot_id=${BOOT_ID}"
echo "debug_root=${DEBUG_ROOT}"

for _ in $(seq 1 30); do
    if [ -d "$DEBUG_ROOT" ]; then
        break
    fi
    sleep 1
done

if [ ! -d "$DEBUG_ROOT" ]; then
    echo "nvgpu debugfs path not found; giving up"
    exit 0
fi

apply_setting() {
    local value="$1"
    local path="$2"
    if [ ! -w "$path" ]; then
        printf 'skipped %s (not writable)\n' "$path"
        return
    fi

    if printf '%s\n' "$value" >"$path"; then
        printf 'set %s => %s\n' "$path" "$value"
    else
        local rc=$?
        printf 'failed to set %s (rc=%s)\n' "$path" "$rc"
    fi
}

apply_setting 0xffffffff "$DEBUG_ROOT/log_mask"
apply_setting 1 "$DEBUG_ROOT/log_trace"
apply_setting 1 "$DEBUG_ROOT/enable_platform_dbg"
if [ -e "$DEBUG_ROOT/falc_trace" ]; then
    apply_setting 1 "$DEBUG_ROOT/falc_trace"
fi
if [ -e "$DEBUG_ROOT/trace_cmdbuf" ]; then
    apply_setting 1 "$DEBUG_ROOT/trace_cmdbuf"
fi

printf '\n-- status --\n'
cat "$DEBUG_ROOT/status" || true

printf '\n-- sched_ctrl --\n'
cat "$DEBUG_ROOT/sched_ctrl" || true

printf '\n-- pmu_security --\n'
cat "$DEBUG_ROOT/pmu_security" || true

printf '\n-- timeout knobs --\n'
cat "$DEBUG_ROOT/ch_wdt_init_limit_ms" 2>/dev/null || true
cat "$DEBUG_ROOT/poll_timeout_default_ms" 2>/dev/null || true

printf '\nsetup complete\n'
