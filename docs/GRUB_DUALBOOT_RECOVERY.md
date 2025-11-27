# Jetson Orin Nano Dual-Boot GRUB Recovery Guide
## Created: November 26, 2025

### CRITICAL SUCCESS: GRUB Dual-Boot Working!

Both NVMe partitions boot successfully using GRUB. The SD card MUST be removed
for the GRUB menu to appear (otherwise it may auto-boot SD).

---

## Partition Layout (NVMe: WD_BLACK SN7100 1TB)

| Partition | Name             | Size    | Purpose                          | PARTUUID                               |
|-----------|------------------|---------|----------------------------------|----------------------------------------|
| p1        | APP_STABLE       | 65 GiB  | Production/Stable OS             | 8b93935b-fed8-4807-81ea-32acdfde9318   |
| p10       | esp              | 64 MiB  | EFI System Partition (GRUB)      | 089b8c1a-4d14-4495-986a-8276f81b782f   |
| p16       | APP_EXPERIMENTAL | 865 GiB | Kernel Development/Experimental  | 0cc559e6-2902-4fcd-ad19-4bfed3c5a97d   |

### Filesystem UUIDs:
- **STABLE (p1)**: eb2a7201-ad26-4264-9b1d-404fb2ed8a45
- **ESP (p10)**: 9C6B-251D
- **EXPERIMENTAL (p16)**: 184ab802-b7b9-4c6a-8f1a-07cda6f537a4

---

## Key File Locations

### On ESP Partition (/dev/nvme0n1p10):
\`\`\`
/EFI/BOOT/BOOTAA64.efi   - GRUB bootloader binary
/EFI/BOOT/grub.cfg       - Bootstrap config (points to main grub.cfg)
\`\`\`

### On STABLE Partition (/dev/nvme0n1p1):
\`\`\`
/boot/grub/grub.cfg      - MAIN GRUB configuration with menu
/boot/grub/arm64-efi/    - GRUB modules
/boot/Image              - Linux kernel
/boot/initrd             - Initial ramdisk
\`\`\`

### On EXPERIMENTAL Partition (/dev/nvme0n1p16):
\`\`\`
/boot/Image              - Linux kernel (for development)
/boot/initrd             - Initial ramdisk
/boot/dtb/               - Device tree blobs
\`\`\`

---

## GRUB Configuration Explained

### ESP Bootstrap (/dev/nvme0n1p10 -> /EFI/BOOT/grub.cfg):
\`\`\`
search.fs_uuid eb2a7201-ad26-4264-9b1d-404fb2ed8a45 root 
set prefix=(\$root)'/boot/grub'
configfile \$prefix/grub.cfg
\`\`\`
This finds the STABLE partition by UUID and loads the main grub.cfg from there.

### Main GRUB Menu (/dev/nvme0n1p1 -> /boot/grub/grub.cfg):
- **Entry 1**: Jetson NVMe - STABLE (boots p1)
- **Entry 2**: Jetson NVMe - EXPERIMENTAL (boots p16)  
- **Entry 3**: Jetson SD Card - LAST RESORT (boots mmcblk0p1)
- **Entry 4**: UEFI Firmware Setup

---

## Recovery Procedures

### If GRUB Menu Doesn't Appear:
1. Remove SD card before power-on
2. GRUB menu has 10-second timeout
3. Serial console available at ttyTCU0,115200

### To Reinstall GRUB (from working system):
\`\`\`bash
# Mount ESP and rootfs
sudo mount /dev/nvme0n1p10 /mnt/esp
sudo mount /dev/nvme0n1p1 /mnt/stable

# Install GRUB
sudo grub-install --target=arm64-efi --efi-directory=/mnt/esp --boot-directory=/mnt/stable/boot --removable

# Copy grub.cfg from this backup
sudo cp /path/to/this/backup/grub.cfg /mnt/stable/boot/grub/grub.cfg
\`\`\`

### To Restore Full Configuration:
1. Boot from SD card (last resort option, or insert SD)
2. Mount partitions as above
3. Extract boot-snapshot tarball if needed
4. Copy grub.cfg from this backup
5. Ensure WiFi config is in place (see below)

---

## WiFi Configuration

The working WiFi connection file is at:
\`\`\`
/etc/NetworkManager/system-connections/LincolnStreet_5G.nmconnection
\`\`\`

Copy this file to both NVMe partitions to enable SSH access:
\`\`\`bash
sudo cp LincolnStreet_5G.nmconnection /mnt/nvme/etc/NetworkManager/system-connections/
sudo cp LincolnStreet_5G.nmconnection /mnt/experimental/etc/NetworkManager/system-connections/
sudo chmod 600 /mnt/nvme/etc/NetworkManager/system-connections/LincolnStreet_5G.nmconnection
sudo chmod 600 /mnt/experimental/etc/NetworkManager/system-connections/LincolnStreet_5G.nmconnection
\`\`\`

---

## Files Included in This Backup

- \`grub.cfg\` - Working GRUB configuration
- \`boot_reference.txt\` - Boot environment info
- \`boot-snapshot-2025-11-26.tar.gz\` - Full /boot directory backup
- \`modules-snapshot-2025-11-26.tar.gz\` - Kernel modules
- \`LincolnStreet_5G.nmconnection\` - WiFi configuration
- \`esp-backup/\` - Complete ESP partition backup
- \`partition-info.txt\` - Full partition table and UUIDs
- \`jetson-hardware/\` - Workspace backup
- \`vscode-server/\` - VS Code server backup

---

## Quick Reference: Mount Commands

\`\`\`bash
# Mount from SD card OS:
sudo mount /dev/nvme0n1p1 /mnt/nvme           # STABLE
sudo mount /dev/nvme0n1p16 /mnt/experimental  # EXPERIMENTAL  
sudo mount /dev/nvme0n1p10 /mnt/esp           # ESP (GRUB)

# Mount from NVMe STABLE:
sudo mount /dev/nvme0n1p16 /mnt/experimental
sudo mount /dev/nvme0n1p10 /mnt/esp
\`\`\`

---

## Important Notes

1. **SD Card Presence**: Remove SD for GRUB menu, insert for SD fallback boot
2. **Serial Console**: ttyTCU0 at 115200 baud for headless debug
3. **Hostname**: jetson-orin
4. **SSH IP**: 192.168.50.8 (when WiFi working)
5. **Default User**: phiip

---

## Document Locations (Cross-References)

This document is available at:
- USB Recovery: /media/phiip/jetson_backup/jetson_backup_2025-11-26/
- NVMe STABLE: /mnt/nvme/home/phiip/workspace/jetson-hardware/docs/
- NVMe EXPERIMENTAL: /mnt/experimental/home/phiip/RECOVERY_DOCS/ (if exists)
- Workspace: ~/workspace/jetson-hardware/docs/GRUB_DUALBOOT_RECOVERY.md
