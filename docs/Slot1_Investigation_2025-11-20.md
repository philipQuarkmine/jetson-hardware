# Slot1 Recovery & Investigation Log (2025-11-20)

## Context
- Host: Jetson Orin Nano booted in slot1 (bootloader slot B per `nvbootctrl get-current-slot`).
- Rootfs A/B disabled; active root partition `/dev/nvme0n1p1` (PARTUUID=47faf214-f280-4347-8886-66eaf34c3ef7).
- Kernel: `5.15.136-tegra` (stock slot1 image, `/boot/Image` timestamp Nov 20 01:10 UTC).
- Goal: keep Slot1 stable while collecting diagnostics about Slot0 boot issues and recovering VS Code workspace state lost after reboot.

## Workspace state
- Primary project path: `/home/phiip/workspace/jetson-hardware` (5.4 GB).
- Safety snapshot made before any changes: `/home/phiip/jetson-hardware-pre-restore-20251120.tar.gz` (~1.1 GB).
- VS Code metadata still present under `~/.vscode-server/data/User/{History,workspaceStorage}` with entries through Nov 19 20:46 UTC.
- Repository cleaned back to `master` @ `5976f6b` (Nov 15 2025). Untracked build trees (`kernel/`, `nvidia-oot/`, `nvethernetrm/`) restored from the pre-change snapshot so Slot1 tooling remains available.

## Backup media located
- USB (exFAT) at `/dev/sda1` → mount with `sudo mount.exfat-fuse /dev/sda1 /mnt/backup`.
  - Contains `jetson-kernel-backup-2025-11-17/` with:
    - `boot/`: full `/boot` snapshot (Images, DTBs, `extlinux.conf` variants, ssh keys, etc.).
    - `modules/5.15.136-prod-tegra.tar.gz`: module tree matching backed-up kernel.
    - `README_RECOVERY.txt`: documented restore workflow.
- MicroSD (`/dev/mmcblk0p1`) holds backup OS; only mounted temporarily to copy SSH host keys—left unchanged.

## Slot0 failure breadcrumbs
- `console-ramoops-0` captured boot of custom kernel (`5.15.148-tegra`, build date Jan 7 2025) showing GPU PMU timeouts and EMEM decode errors before forced reboot.
- `/boot/extlinux/extlinux.conf` updated on Nov 17 to label new IMX708 build as “primary” while keeping `/boot/Image.backup` as fallback.
- Kernel command line still forces `root=PARTUUID=47faf214...`, so Slot0 attempts the same NVMe rootfs. No `/etc/fstab` overrides, so failure likely earlier (initramfs) when kernel modules/initrd mismatch prevents mounting `/mnt` overlay.

## Journald & crash logs
- Persistent journal enabled (`/var/log/journal/5dbf...`, ~153 MB). Boot IDs:
  - `05c0cfb9…` (current slot1 boot).
  - `2a79dcee…` (Nov 20 01:12 UTC, slot0 attempt that progressed further).
  - `13427cef…` / `21236c38…` covering Nov 19 testing loop.
- Ramoops at `/sys/fs/pstore/console-ramoops-0` retains early-boot console for failure reproduction.

## Networking recap
- Active Wi‑Fi profile `LincolnStreet_5G` (`nmcli dev status` shows wlan0 connected, IP 192.168.50.8/24).
- Saved settings under `/etc/NetworkManager/system-connections/LincolnStreet_5G.nmconnection`.

## Next steps
1. When ready to keep post-Nov19 edits, retrieve them from `~/jetson-hardware-pre-restore-20251120.tar.gz` or USB backups before deleting the archive.
2. Continue documenting fixes in `docs/Slot1_Investigation_YYYY-MM-DD.md` to avoid losing forensic notes during slot swaps.
3. For Slot0 work:
   - Rebuild kernel+modules in isolated output (`kernel_out_rebuild`), ensure matching initrd.
   - Validate `/boot/extlinux/extlinux.conf` root entries before switching slots via `nvbootctrl set-active-boot-slot 0`.
   - Keep ramoops enabled for quicker post-mortem.

## 2025-11-20 Evening slot0 prep
- Rebuilt `5.15.136-prod` from `kernel/kernel-jammy-src` with `CONFIG_NV_VIDEO_IMX708=m` into `kernel_out_rebuild/` (same config that previously booted the farthest).
- Installed modules via `sudo make O=../../kernel_out_rebuild modules_install`; reran `sudo depmod 5.15.136-prod` (expected NVIDIA `preempt_count_*` warning spam still present but benign).
- Snapshotted `/boot/Image` to `/boot/Image.pre-slot0-20251120-162519` before copying the new `Image` and `System.map-5.15.136-prod` from `kernel_out_rebuild/`.
- Verified `/boot/extlinux/extlinux.conf` primary entry still points at `/boot/Image` and backup entry still references `/boot/Image.backup`.
- Confirmed hashes: `sha256sum kernel_out_rebuild/arch/arm64/boot/Image /boot/Image` → `0b650625cce4828f33c08890d3730a39ef9e603da56c952a932b83f0094b12aa` for both files.
- Set next boot to slot0 via `sudo nvbootctrl set-active-boot-slot 0`; `nvbootctrl dump-slots-info` now shows Active bootloader slot A (slot0) while we still operate from slot1.
- Ready to reboot once we finish any final log captures; post-boot triage should grab `journalctl -b -1` and `/sys/fs/pstore/console-ramoops-0` immediately if slot0 fails again.

## 2025-11-20 16:45 rootfs pointer audit
- Reran `sudo blkid` to capture authoritative PARTUUIDs. Active root (`/dev/nvme0n1p1`) remains `47faf214-f280-4347-8886-66eaf34c3ef7`, matching both `/boot/extlinux/extlinux.conf` entries and the current `APPEND` line in `/proc/cmdline`.
- `console-ramoops-0` from the most recent failure shows the kernel command line already contains the correct PARTUUID and the initramfs logs "Root device found" before the crash, so the earlier console photo that mis-reported `47af2f14-…` was either a transcription error or came from CBoot before extlinux handed control to Linux.
- Since storage wiring checks out, the next round of slot0 debugging should concentrate on the late-boot GPU PMU timeout that immediately precedes the watchdog reset in `console-ramoops-0` rather than on rootfs discovery.
