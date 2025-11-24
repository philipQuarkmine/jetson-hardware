# Slot1 Restore Notes — 2025-11-21

This file captures the exact steps taken from the microSD rescue OS to restore the NVMe slot1 kernel and modules back to the pre-slot0 snapshot so we can safely reboot without losing context.

## Context Recap
- Running from rescue microSD root (`/dev/mmcblk0p1`, kernel `5.15.148-tegra`).
- NVMe rootfs mounted at `/mnt/nvme`; do **not** boot it until after step 4 below.
- Primary snapshot assets:
  - `/mnt/nvme/boot/Image.pre-slot0-20251120-162519` (sha256 `0b650625cce4828f33c08890d3730a39ef9e603da56c952a932b83f0094b12aa`).
  - `/mnt/nvme/home/phiip/jetson-hardware-pre-restore-20251120.tar.gz` (workspace).
  - Modules restored from `/mnt/backup/jetson-kernel-backup-2025-11-17/modules/5.15.136-prod-tegra.tar.gz` because the Nov 20 archive was not present; this is the set that previously matched the Nov 20 kernel build.
- Rescue USB (`/dev/sda1`) mounted read-only with `sudo mount.exfat-fuse -o ro /dev/sda1 /mnt/backup` only while copying.

## Actions Performed
1. **Safeguarded current broken assets**
   - `sudo cp -a /mnt/nvme/boot/Image /mnt/nvme/boot/Image.slot0-20251121-current`
   - `sudo tar -czf /mnt/nvme/home/phiip/backups/5.15.136-prod-tegra-current-20251121.tar.gz -C /mnt/nvme/lib/modules 5.15.136-prod-tegra`
2. **Restored kernel image**
   - `sudo cp -a /mnt/nvme/boot/Image.pre-slot0-20251120-162519 /mnt/nvme/boot/Image`
   - Verified hashes match (`sha256sum` equals `0b6506…12aa`).
3. **Replaced module tree**
   - `cd /mnt/nvme/lib/modules && sudo rm 5.15.136-prod && sudo rm -rf 5.15.136-prod-tegra`
   - `sudo tar -xzf /mnt/backup/jetson-kernel-backup-2025-11-17/modules/5.15.136-prod-tegra.tar.gz -C /mnt/nvme/lib/modules`
   - `sudo ln -s 5.15.136-prod-tegra /mnt/nvme/lib/modules/5.15.136-prod`
   - `sudo depmod -b /mnt/nvme 5.15.136-prod-tegra`
4. **Boot slot selection**
   - `sudo nvbootctrl set-active-boot-slot 1`
   - `sudo nvbootctrl dump-slots-info` now reports `Active bootloader slot: B` and both slots `status: normal`.
5. **Cleanup**
   - Unmounted rescue USB (`sudo umount /mnt/backup`) so it remains untouched.

## Pre-Reboot Checklist
1. From rescue OS, run `sync`.
2. Trigger reboot (user action) and verify:
   - `uname -a` → `5.15.136-tegra #1 SMP PREEMPT Sat Nov 15 18:05:24 UTC 2025`
   - `sudo nvbootctrl get-current-slot` → `1`
   - `/boot/Image` hash equals `0b650625…0094b12aa`
   - `/lib/modules/5.15.136-prod-tegra` exists and matches restored content
3. Capture diagnostics:
   - `sudo journalctl -b --no-pager > /var/log/slot1-boot-$(date +%Y%m%d).log`
   - `sudo journalctl -b -1 --no-pager` (preserve failing slot0 logs)
   - `sudo cat /sys/fs/pstore/console-ramoops-0`
4. After confirming stability, run `scripts/sync_recovery_docs.sh` to mirror these docs and `/boot` back onto the rescue media.

### Snapshot – 2025-11-22 14:55 UTC
- `sudo nvbootctrl dump-slots-info`

```
Current version: 36.4.7
Capsule update status: 0
Current bootloader slot: B
Active bootloader slot: B
num_slots: 2
slot: 0,             status: normal
slot: 1,             status: normal
```

- `lsblk -o NAME,PARTUUID,MOUNTPOINT`

```
NAME         PARTUUID                             MOUNTPOINT
loop0                                             
sda                                               
└─sda1       fa2cb833-01                          
mmcblk0                                           
├─mmcblk0p1  d396698e-e4d8-439c-b07c-8475769809fe /
├─mmcblk0p2  34e72d74-a9f6-4791-b657-b3144e28ba25 
├─mmcblk0p3  4f384e6c-8f33-476c-a639-2669f6c2114b 
├─mmcblk0p4  1bb501ca-5a05-49b6-a11b-b42f9c477401 
├─mmcblk0p5  95e5eede-bac9-45c6-9ce7-edb460720985 
├─mmcblk0p6  5c5069e4-a953-4329-a476-d9aa84e046ca 
├─mmcblk0p7  ee4bcfa0-1905-47f7-9483-5c8fe32887d3 
├─mmcblk0p8  6a9aa298-6b2b-4a25-a92a-68cb420f6cd3 
├─mmcblk0p9  da64284a-21a3-4eeb-b795-be76aa117c6a 
├─mmcblk0p10 a24a8abe-fff0-4087-8f92-873354d3662d /boot/efi
├─mmcblk0p11 191a0ff1-6410-4958-87b2-36bc5f70784f 
├─mmcblk0p12 2b3f7b12-6b7d-478d-8e96-cb97000dbdc1 
├─mmcblk0p13 0d24ee72-c893-44ba-9337-36d179717429 
├─mmcblk0p14 9bed4889-1b93-4a49-b6eb-fc193ccf1470 
└─mmcblk0p15 6070a95a-9c0f-4a85-a746-c1e1a1c25f55 
zram0                                             [SWAP]
zram1                                             [SWAP]
zram2                                             [SWAP]
zram3                                             [SWAP]
zram4                                             [SWAP]
zram5                                             [SWAP]
nvme0n1                                            
├─nvme0n1p1  47faf214-f280-4347-8886-66eaf34c3ef7 /mnt/nvme
├─nvme0n1p2  b96f9860-268f-4c7e-8759-a7f24927b4f3 
├─nvme0n1p3  622741eb-0054-47c7-a529-023674d46b11 
├─nvme0n1p4  926fe179-f485-43c9-95a6-97f92fa7ea8d 
├─nvme0n1p5  564a3e9b-8619-4a47-9181-992066bf00cb 
├─nvme0n1p6  b5eef0d8-0f72-40d4-a29a-cec7bd55d207 
├─nvme0n1p7  39934f0b-ffe3-449e-acda-70591ff1f093 
├─nvme0n1p8  82b347fc-c70b-4f30-a327-52a527a6f690 
├─nvme0n1p9  81fc2b64-217c-42b4-b36d-262b8894f539 
├─nvme0n1p10 885fc058-8c0c-4ba6-bd6d-bddfb5669a37 /mnt/p10
├─nvme0n1p11 0451aa90-baf3-48a4-bb0c-1795707bd907 
├─nvme0n1p12 d2bf2d65-90df-4f5e-bced-427e309e31ab 
├─nvme0n1p13 67f77fac-6abc-4e89-a261-cdfc5ca3e79a 
├─nvme0n1p14 cb08d237-6a9f-47cc-b5fc-8b795b114184 
└─nvme0n1p15 8dbb52ec-9e77-4824-bcda-1dd9e06945c9 
```

## Notes
- The absence of a `jetson-kernel-backup-2025-11-20` directory implies we never copied the most recent `/boot` to USB. If that snapshot surfaces later, repeat the module and kernel restore using those artifacts.
- The workspace tarball from Nov 20 remains at `/mnt/nvme/home/phiip/jetson-hardware-pre-restore-20251120.tar.gz`; re-extract if future slot0 work corrupts the repo again.
