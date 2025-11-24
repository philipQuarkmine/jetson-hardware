#!/usr/bin/env bash
set -euo pipefail

DOC_SOURCE="$(dirname "$0")/../docs/RECOVERY_ROADMAP.md"
BACKUP_MOUNT="/media/phiip/jetson_backup"
BACKUP_DEV="/dev/sda1"
DEST_FILE="$BACKUP_MOUNT/RECOVERY_ROADMAP.md"

if [[ ! -f "$DOC_SOURCE" ]]; then
  echo "Source roadmap not found: $DOC_SOURCE" >&2
  exit 1
fi

if ! mount | grep -q " $BACKUP_MOUNT "; then
  echo "Mounting $BACKUP_DEV to $BACKUP_MOUNT"
  sudo mkdir -p "$BACKUP_MOUNT"
  sudo mount "$BACKUP_DEV" "$BACKUP_MOUNT"
fi

sudo cp "$DOC_SOURCE" "$DEST_FILE"
sudo sync

echo "Roadmap synced to $DEST_FILE"
