# Analysis of `huawei_xt26g04c_dump9.bin` NAND Flash Dump

This report documents the structural analysis and reverse-engineering findings of the raw NAND flash dump `huawei_xt26g04c_dump9.bin` from a Huawei XT26G04C ONT device.

---

## 1. File Overview
- **File Name:** `huawei_xt26g04c_dump9.bin`
- **File Size:** 512 MB (536,870,912 bytes)
- **File Type:** Raw SPI-NAND flash dump
- **Device Model:** Huawei XT26G04C (Optical Network Terminal)
- **Firmware Version:** V500R021C00SPC128B130 / V500R021C00SPC128B345
- **SoC Architecture:** ARM (Little-Endian)

---

## 2. Partition Layout & Structure

The NAND flash dump consists of an initial bootloader/startcode section followed by a large UBI container holding the root filesystem and system configuration partitions.

```
NAND Flash Layout:
┌─────────────────────────┬──────────────┬──────────────┬────────────────────────┐
│ Partition               │ Start Offset │ Size         │ Description            │
├─────────────────────────┼──────────────┼──────────────┼────────────────────────┤
│ Startcode / Bootloader  │ `0x000000`   │ 2 MB         │ Initial boot, secure   │
│                         │ (0 KB)       │ (2,097,152 B)│ boot verification      │
├─────────────────────────┼──────────────┼──────────────┼────────────────────────┤
│ UBI Filesystem Container│ `0x200000`   │ 510 MB       │ Primary UBI volume containing│
│                         │ (2 MB)       │              │ kernel, rootfs, config │
└─────────────────────────┴──────────────┴──────────────┴────────────────────────┘
```

### 2.1 Bootloader Section (First 2 MB)
- Contains **ARM little-endian boot code**.
- **U-Boot version:** `2020.01` (specifically builds supporting `V500R020C00/V5` and `V500R020C20/V5` firmware branches).
- **Embedded OS:** Linux kernel version `4.4.240`.
- **Certificates:** Contains multiple X.509 certificates used to establish a chain of trust for secure boot.

### 2.2 UBI Container (Starting at `0x200000`)
- **UBI Headers:** Erase count (`UBI#`) and volume layout (`UBI!`) headers are detected starting at offset `0x200000` (2 MB).
- **Filesystem Type:** Formatted with **UBIFS** (UBI Filesystem).
- **Partition Arguments:** `mtdparts=nand0:0x20000(startcode),0x7FE0000(ubifs),-(reserved)`

---

## 3. Security Features & Observations

The firmware on the XT26G04C incorporates modern Huawei hardware-enforced security protocols:

1. **Secure Boot Chain of Trust:**
   - Bootloader verification starting from ROM.
   - Signature checks using root certificates under the **Huawei Root CA**.
   - Signatures checked for kernel, rootfs, and upgrade images.

2. **Flash Encryption:**
   - Support for block-level or filesystem-level encryption (crypt keys and initialization vectors stored/managed by hardware).

3. **Chain of Trust Verification:**
   - Multi-stage signature validation prevents loading custom, unsigned kernel images or modified root filesystems via standard boot paths.

---

## 4. Notable Version & Debug Strings

Several notable strings extracted from the dump confirm device identity and system versions:
- **Firmware Versions:** `V500R021C00SPC128B130` and `V500R021C00SPC128B345`.
- **System Kernel:** `Linux version 4.4.240 (gcc version 7.3.0)`.
- **Hardware Drivers:** SPI NAND controller drivers, Flash chip type detection tables.
- **UBIFS Logging:** Diagnostic mount messages, flash bad-block recovery logs.
- **Huawei ONT Identifiers:** Board configuration parameters and operator customizations.
