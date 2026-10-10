# Huawei ONT Flash Partition Configuration Analysis Report

This report provides a comparative analysis of two partition specification XML files extracted from the Huawei ONT firmware:
1. `hw_flashcfg_shaopian.xml` (Standard 2K Page NAND variant)
2. `hw_flashcfg_shaopian_4k.xml` (Modern 4K Page NAND variant)

These XML specifications are utilized by the bootloader and flash tools to map block boundaries, alternate partition rotations (A/B layout), and active volumes.

---

## 1. Comparative Overview

The two layouts target the same overall 512 MB flash size (`0x20000000`) but differ significantly in allocation boundaries to accommodate different NAND page and erase block structures:
- **Standard (2K Page) NAND:** Typically uses **128 KB erase blocks** (page size 2 KB, block size 128 KB).
- **4K Page NAND:** Typically uses **256 KB erase blocks** (page size 4 KB, block size 256 KB).

### Partition Mapping Comparison Table
| Volume / Partition | Standard (2K Page) Size | 4K Page Size | Purpose / Notes |
|:---|:---|:---|:---|
| **`bootcode`** | `0x00100000` (1 MB) | `0x00200000` (2 MB) | Bootloader (U-Boot/Startcode) container |
| **`bootcode:L1boot`** | `0x00020000` (128 KB) | `0x00040000` (256 KB) | Level 1 Boot stage |
| **`bootcode:L2boot`** | `0x00040000` (256 KB) | `0x00040000` (256 KB) | Level 2 Boot (A/B rotation) |
| **`bootcode:eFuse`** | `0x00020000` (128 KB) | `0x00040000` (256 KB) | Security eFuse virtual block |
| **`ubilayer_v5`** | `0x1FF00000` (511 MB) | `0x1EE10000` (~494 MB)| Primary UBI filesystem container |
| **`ubilayer_v5:flash_config`** | `0x0001F000` (124 KB) | `0x0003E000` (248 KB) | Flash config storage (A/B rotation) |
| **`ubilayer_v5:slave_param`** | `0x0001F000` (124 KB) | `0x0003E000` (248 KB) | Secondary parameters (A/B rotation) |
| **`ubilayer_v5:wifi_param`** | `0x0001F000` (124 KB) | `0x0003E000` (248 KB) | Wi-Fi calibration params (A/B rotation)|
| **`ubilayer_v5:allsystem`** | `0x0502A000` (~80 MB) | `0x0502A000` (~80 MB) | Firmware system container (uboot/kernel/rootfs)|

---

## 2. Key Structure & Architecture Differences

### 2.1 Bootloader Size Scaling
On 4K page NAND devices, metadata overhead and bad-block management rules require larger block boundaries. Consequently, the primary `bootcode` partition size scales from **1 MB to 2 MB**, doubling the allocation for `L1boot` and `eFuse` stages.

### 2.2 UBI volume alignments
Within the `ubilayer_v5` UBI container, parameters such as `flash_config`, `slave_param`, and `wifi_param` are mirrored partitions with active rotation (`rotate_flag="1"`).
- In the 2K page configuration, their length is `0x0001F000` (124 KB).
- In the 4K page configuration, their length is `0x0003E000` (248 KB).
This 124 KB / 248 KB sizing represents a single erase block for UBI formatting after subtracting UBI header overhead (1 erase block minus metadata leaves ~124 KB / ~248 KB available for formatting).

### 2.3 `allsystem` Volume Sizing
In both variants, `allsystem` is allocated exactly `0x0502A000` bytes (~80 MB) to hold the firmware images (signature block, u-boot binary, kernel, and SquashFS rootfs). This ensures uniform system partition sizing across hardware revisions.
