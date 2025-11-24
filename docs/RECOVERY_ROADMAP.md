# Jetson Orin Nano — Recovery & Rebuild Guide

_Last updated: 2025-11-23_

This is the single source of truth for recovering, rebuilding, and documenting the Jetson Orin Nano dev kit. It merges the historical slot-based playbook with the new, proven NVMe reflash procedure that finally brought the system back online on 2025‑11‑23. Keep a copy of this file on removable media (`/media/phiip/jetson_backup/RECOVERY_ROADMAP.md`) so the process stays accessible even when the NVMe rootfs is unavailable.

---

## 0. Current Snapshot (2025-11-23)

- **Boot source:** NVMe `/dev/nvme0n1p1` mounted at `/` (EXT4 UUID `eb2a7201-ad26-4264-9b1d-404fb2ed8a45`).
- **Kernel:** `5.15.136-tegra #1 SMP PREEMPT Mon May  6 09:56:39 PDT 2024` (`uname -a`).
- **Jetson Linux:** `R36.3.0` (`/etc/nv_tegra_release`).
- **Boot slots:** `sudo nvbootctrl dump-slots-info` → active slot **A** (slot0) and slot1 both `status: normal` after a clean flash.
- **Workspace:** canonical path `/home/phiip/workspace/jetson-hardware`; `/mnt/nvme/home/...` now symlinks here so SD-based recoveries still see the same tree.
- **VS Code remote state:** restored under `/home/phiip/.vscode-server/` from the `jetson_backup_2025-11-23` snapshot.
- **Backup SD (ext4):** `/dev/sda1` labeled `jetson_backup`, mounted at `/media/phiip/jetson_backup`, holding `jetson_backup_2025-11-23/{jetson-hardware,vscode-server}`. Only the most recent dated directory is retained to avoid stale copies.
- **Last-Resort SD OS:** `/dev/mmcblk0p1` (UUID `bbc64d1c-24dc-4aa3-8c44-8dfd6c37ff3b`) relabeled to `SDLR_20251123` and auto-mounted at `/media/phiip/SDLR_20251123` for GUI-based recovery work, but it is not the active rootfs when NVMe is healthy.
- **Outstanding work:** NVMe currently uses NVIDIA’s default partition table; the prior “experimental vs stable rootfs” layout has not been recreated yet.

Use this snapshot as the baseline for future incidents—update the bullets whenever the system state meaningfully changes.

---

## 1. Architecture & Roles

- **NVMe SSD (Prime OS):** The high-performance, headless environment for agentic LLM workloads, robotics services, and kernel work. Always assume automation should target this rootfs unless explicitly booted from SD.
- **microSD (Last-Resort OS):** Desktop-oriented rescue system. Provides GUI, VS Code, and stable tooling even when NVMe is offline. Never overwrite; treat it as the safe house.
- **QSPI Boot Chain:** Stores bootloader + slot metadata. Slot0 is the experimental path; slot1 is the safety slot. After the 2025‑11‑23 flash both slots boot the same clean image, but slot discipline still applies going forward.
- **Agents must detect context:** Check `lsblk`, `mount`, or the presence of `/media/phiip/jetson_backup` to know whether they are operating from Prime NVMe or the SD fallback before modifying files.

---

## 2. Quick Survey Commands

```bash
lsblk -f                     # identify NVMe, SD, and backup volumes
df -h                        # confirm mountpoints and free space
sudo nvbootctrl dump-slots-info
cat /etc/nv_tegra_release
uname -a
ls /media/phiip              # see mounted removable media
```

When running from the SD OS, mount the NVMe rootfs at `/mnt/nvme` (`sudo mount /dev/nvme0n1p1 /mnt/nvme`) and operate on `/mnt/nvme/home/phiip/...` so both environments share the exact same path structure.

---

## 3. Images & Media

| Medium | Purpose | Image Source |
|--------|---------|--------------|
| **NVMe SSD** | Primary compute OS | Flashed via NVIDIA `flash.sh` using the `jetson-orin-nano-devkit-nvme` target. |
| **microSD** | GUI recovery + diagnostics | NVIDIA’s prebuilt SD card image written via `dd`/Etcher. |
| **Backup SD (`jetson_backup`)** | Offline copy of workspace + VS Code server | Populated with metadata-preserving `rsync -aHAX` runs before any destructive steps. |

Never mix these roles. The Last-Resort SD stays inserted but unused unless recovery is required. The backup SD only stores copies; do not boot from it.

---

## 4. Backup Assets (2025-11-23 snapshot)

| Asset | Path | Notes |
|-------|------|-------|
| Workspace tree | `/media/phiip/jetson_backup/jetson_backup_2025-11-23/jetson-hardware/` | Mirrors repo plus support dirs (`Libs/`, `Managers/`, refreshed `nvidia-oot/`, etc.). |
| VS Code Remote bundle | `/media/phiip/jetson_backup/jetson_backup_2025-11-23/vscode-server/` | Contains `code-*` binaries, `data`, and `extensions`. Restored verbatim to `~/.vscode-server`. |
| Recovery docs | Same backup path under `docs/` | Ensure this roadmap stays mirrored here after edits. |
| Legacy kernel snapshots | `/media/phiip/jetson_backup/jetson-kernel-backup-2025-11-17/` | Still useful if slot-based experiments resume. |

Refresh these assets after major changes using the rsync wrapper in `scripts/sync_recovery_docs.sh` (update script soon to target the ext4 SD instead of the old exFAT mount). Delete prior `jetson_backup_*` directories before capturing a new snapshot so only a single “last-known-good” copy exists.

---

## 5. Golden Recovery Workflows

### 5.1 Preserve Workspace Before Risky Changes

```bash
sudo mount /dev/sda1 /media/phiip/jetson_backup
sudo rm -rf /media/phiip/jetson_backup/jetson_backup_20*
BACKUP_DATE=$(date +%F)
rsync -aHAX --delete ~/workspace/jetson-hardware/ /media/phiip/jetson_backup/jetson_backup_${BACKUP_DATE}/jetson-hardware/
rsync -aHAX --delete ~/.vscode-server/ /media/phiip/jetson_backup/jetson_backup_${BACKUP_DATE}/vscode-server/
rsync -a docs/RECOVERY_ROADMAP.md /media/phiip/jetson_backup/RECOVERY_ROADMAP.md
sync
```

Exclude large build directories (e.g., `kernel_out/`) if space becomes tight, but keep kernel sources and scripts.

### 5.2 NVMe Reflash (VMware + classic `flash.sh`)

This is the proven path that succeeded on 2025‑11‑23.

1. **Versions**
   - Jetson Linux R36.3 / JetPack 6.2 image.
   - Flash host: Ubuntu 22.04 VM inside VMware Workstation.
   - Target: Jetson Orin Nano dev kit with 1 TB NVMe.

2. **Why `l4t_initrd_flash.sh --network usb0` failed**
   - Requires USB gadget networking, which is unreliable through Windows → VMware USB redirection.
   - Host never sees `usb0`, script loops forever. Do **not** use this path in VMs.

3. **Why `flash.sh` works**
   - Pure APX/RCM pipeline, no gadget networking, minimal USB hand‑offs.
   - Far more tolerant of virtualization latency.

4. **Procedure**
   ```bash
   # Wipe NVMe in USB dock (host PC)
   sudo wipefs -a /dev/sdX
   sudo sgdisk -Z /dev/sdX

   # Move NVMe back into Jetson, remove SD card, place board in Force Recovery
   lsusb | grep -i nvidia    # expect 0955:7523

   cd ~/Linux_for_Tegra
   sudo ./tools/l4t_flash_prerequisites.sh
   sudo ./apply_binaries.sh
   sudo ./flash.sh jetson-orin-nano-devkit-nvme internal
   ```

   When the script prints `*** The target generic has been flashed successfully. ***`, power-cycle, remove Force Recovery jumper, keep SD ejected, and let first boot finish the Ubuntu wizard (user `phiip`).

5. **Post-flash hardening**
   ```bash
   sudo systemctl enable ssh
   sudo systemctl start ssh
   sudo systemctl set-default multi-user.target
   ```

   Reboot to apply headless target mode.

### 5.3 Restoring Workspace + VS Code

Run these from the freshly flashed NVMe OS:

```bash
BACKUP_DATE=2025-11-23

# Restore project tree
rsync -aHAX --info=progress2 /media/phiip/jetson_backup/jetson_backup_${BACKUP_DATE}/jetson-hardware/ /home/phiip/workspace/jetson-hardware/

# Restore VS Code remote bundle
rsync -aHAX --info=progress2 --delete /media/phiip/jetson_backup/jetson_backup_${BACKUP_DATE}/vscode-server/ ~/.vscode-server/
```

After restoration, remove any duplicate placeholder copies (e.g., `/home/phiip/workspace/jetson-hardware.post-flash-placeholder`) and keep `/mnt/nvme/home/...` as a symlink that targets the canonical `/home` path so SD-based workflows remain consistent.

### 5.4 Using the SD OS as a Rescue Shell

1. Boot the Jetson with the Last-Resort SD inserted (NVMe can remain installed).
2. Mount the NVMe rootfs:
   ```bash
   sudo mkdir -p /mnt/nvme
   sudo mount /dev/nvme0n1p1 /mnt/nvme
   ```
3. Operate on `/mnt/nvme/home/phiip/...` exactly as you would on the live system—this ensures paths in scripts and documentation stay identical.
4. Keep VS Code + desktop tooling on the SD image for comfort work; never treat it as disposable.

### 5.5 Slot Policy (once experiments resume)

1. Slot0 = experimental kernel/modules; Slot1 = stable fallback.
2. Never overwrite Slot1 artifacts unless you have a verified backup on removable media.
3. Before a Slot0 reboot:
   ```bash
   sudo nvbootctrl set-active-boot-slot 0
   sudo reboot
   ```
4. If Slot0 fails, either let CBoot fall back automatically or manually run `sudo nvbootctrl set-active-boot-slot 1 && sudo reboot` from a rescue shell.
5. Always snapshot `/boot` (and module trees) before installing test builds:
   ```bash
   sudo cp /boot/Image /boot/Image.pre-$(date +%Y%m%d-%H%M%S)
   sudo tar -czf /home/phiip/backups/modules-$(uname -r)-$(date +%F).tar.gz -C /lib/modules $(uname -r)
   ```

### 5.6 Boot Device Priority

- Keep the UEFI boot order set to **NVMe first, SD second** so the board always prefers the Prime OS but still lets you drop into the Last-Resort OS via the boot menu.
- Check the current order from either OS:

   ```bash
   sudo efibootmgr -v
   ```

   Expect something like `BootOrder: 0001,0008,0009,...` where `0001` is the NVMe entry (`UEFI WD_BLACK ...`) and `0008` is the SD device.
- If the SD ever bubbles to the top (common after firmware resets), rewrite the order once and it persists across reboots:

   ```bash
   sudo efibootmgr -o 0001,0008,0009,0004,0003,0002,0005,0000,0006,0007
   ```

   Adjust the trailing IDs as needed for your network/USB preferences, but keep `0001` (NVMe) ahead of `0008` (SD). You can still press **ESC** during the NVIDIA splash to force the SD entry when you intentionally want the rescue OS.

---

## 6. Evidence & Logging

- Persistent journald is enabled (`/var/log/journal`). Use `sudo journalctl --list-boots` plus `sudo journalctl -b <ID>` for forensics.
- `ramoops` (`/sys/fs/pstore/console-ramoops-0`) retains the previous boot’s kernel console—collect it immediately after failures.
- Networking profiles remain under `/etc/NetworkManager/system-connections/` (e.g., `LincolnStreet_5G.nmconnection`). Backup as part of the workspace sync if you modify them.

---

## 7. Lessons Learned / Open Items

1. **`l4t_initrd_flash.sh` + `--network usb0` is unreliable inside VMware.** Prefer `flash.sh` until a bare-metal host can be dedicated to custom network flashing.
2. **Always keep the backup SD formatted as ext4.** exFAT corrupted permissions and broke symlinks; ext4 preserved xattrs, ownership, and device files.
3. **Maintain a single workspace location.** The `/mnt/nvme` symlink avoids double trees and keeps documentation accurate regardless of boot source.
4. **Outstanding task:** Recreate the dual-rootfs NVMe partition layout (experimental vs stable) once the system stays quiet for a while. Document that process here when executed.

---

## 8. Keeping This Document Current

1. Edit `docs/RECOVERY_ROADMAP.md` whenever procedures change.
2. Mirror it to removable media:
   ```bash
   rsync -a docs/RECOVERY_ROADMAP.md /media/phiip/jetson_backup/RECOVERY_ROADMAP.md
   ```
3. Capture dated appendices (e.g., `docs/Slot1_Investigation_2025-11-20.md`) only for deep-dives; summarize key outcomes back here so this file remains the authoritative playbook.

---

## Appendix A — 2025-11-23 Rebuild Log

1. Reformatted the backup SD to ext4 and reran metadata-preserving rsync backups of `jetson-hardware` and `.vscode-server`.
2. Reflashed NVMe via VMware + `flash.sh jetson-orin-nano-devkit-nvme internal` (R36.3 image).
3. Completed first boot wizard, re-enabled SSH, switched to `multi-user.target`.
4. Restored workspace + VS Code server from the SD backup.
5. Removed duplicate placeholder repo and created `/mnt/nvme/...` symlink pointing to `/home/...` for consistent paths.
6. Verified devices via `lsblk -f`, mounts via `df -h`, and slot state via `sudo nvbootctrl dump-slots-info`.
7. Renamed the Last-Resort SD label to `SDLR_20251123`, ensured the auto-mount path reflects the new name, refreshed `/usr/local/sbin/mount_nvme_workspace.sh` + `nvme-mount.service` on that OS, and verified the `jetson_backup` SD now holds only the dated `jetson_backup_2025-11-23` snapshot.
8. Replaced the `nvidia-oot/` tree with the stock R36.3 sources from `/usr/src/nvidia/nvidia-oot` so camera/kernel work can restart from a pristine baseline.

Update this appendix with future rebuilds so we always know the most recent chain of actions that returned the system to a healthy baseline.
