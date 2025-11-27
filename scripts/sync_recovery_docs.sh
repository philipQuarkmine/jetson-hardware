#!/usr/bin/env bash
# sync_recovery_docs.sh - Sync all recovery documentation to USB backup
# Run with: sudo ./scripts/sync_recovery_docs.sh
set -euo pipefail

DOCS_DIR="$(dirname "$0")/../docs"
BACKUP_MOUNT="/media/phiip/jetson_backup"
BACKUP_DEV="/dev/sda1"

# List of recovery docs to sync
RECOVERY_DOCS=(
  "RECOVERY_ROADMAP.md"
  "GRUB_DUALBOOT_RECOVERY.md"
)

# Ensure backup drive is mounted
if ! mount | grep -q " $BACKUP_MOUNT "; then
  echo "Mounting $BACKUP_DEV to $BACKUP_MOUNT"
  sudo mkdir -p "$BACKUP_MOUNT"
  sudo mount "$BACKUP_DEV" "$BACKUP_MOUNT"
fi

# Get today's dated backup folder
DATED_BACKUP=$(ls -d "$BACKUP_MOUNT"/jetson_backup_* 2>/dev/null | sort -r | head -1)

# Sync each doc
for doc in "${RECOVERY_DOCS[@]}"; do
  src="$DOCS_DIR/$doc"
  if [[ -f "$src" ]]; then
    # Copy to USB root
    sudo cp "$src" "$BACKUP_MOUNT/$doc"
    echo "Synced $doc to $BACKUP_MOUNT/"
    
    # Also copy to dated backup folder if it exists
    if [[ -n "$DATED_BACKUP" && -d "$DATED_BACKUP" ]]; then
      sudo cp "$src" "$DATED_BACKUP/$doc"
      echo "Synced $doc to $DATED_BACKUP/"
    fi
  else
    echo "Warning: $src not found, skipping"
  fi
done

sudo sync
echo ""
echo "All recovery docs synced to USB backup"
