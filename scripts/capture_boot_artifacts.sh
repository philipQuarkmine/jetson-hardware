#!/bin/bash
set -euo pipefail

BOOT_ID=$(cat /proc/sys/kernel/random/boot_id)
STAMP=$(date -u +%Y%m%d-%H%M%S)
BASE_DIR="/var/log/boot-diagnostics/${STAMP}-${BOOT_ID}"
PSTORE_SRC="/sys/fs/pstore"

mkdir -p "$BASE_DIR"
chmod 700 "$BASE_DIR"

echo "Saving boot diagnostics to $BASE_DIR"

if command -v nvbootctrl >/dev/null 2>&1; then
    nvbootctrl dump-slots-info >"$BASE_DIR/nvbootctrl.txt" 2>&1 || true
    nvbootctrl dump-slots-info -x >"$BASE_DIR/nvbootctrl-xml.txt" 2>&1 || true
fi

cat /proc/cmdline >"$BASE_DIR/proc-cmdline.txt"

if [ -d "$PSTORE_SRC" ]; then
    mkdir -p "$BASE_DIR/pstore"
    cp -a "$PSTORE_SRC/." "$BASE_DIR/pstore/" 2>/dev/null || true
fi

journalctl -b -o short-monotonic --no-pager >"$BASE_DIR/journalctl.short" || true
journalctl -b -o short-precise --no-pager >"$BASE_DIR/journalctl.precise" || true

dmesg -T >"$BASE_DIR/dmesg.txt" || true

if [ -d /sys/kernel/debug/17000000.gpu ]; then
    mkdir -p "$BASE_DIR/nvgpu-debugfs"
    cp -a /sys/kernel/debug/17000000.gpu/. "$BASE_DIR/nvgpu-debugfs/" 2>/dev/null || true
fi

tar -czf "${BASE_DIR}.tar.gz" -C "$(dirname "$BASE_DIR")" "$(basename "$BASE_DIR")" && rm -rf "$BASE_DIR"
