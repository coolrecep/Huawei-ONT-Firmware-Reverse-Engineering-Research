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

---

## 5. Embedded Flash Partition Map XML Specification

During reverse engineering of the firmware binaries, the following raw XML partition mapping specification was retrieved. This XML defines the precise boundaries, lengths, and alternate rotation configs (A/B partitioning) for both the bootloader/startcode and the `ubilayer_v5` volumes.

### 5.1 Reconstructed Clean XML Specification
Due to a known flash/memory corruption issue affecting `flash_config lengthA`, the corrupted bytes were reconstructed back to `0x0003E000` (matching the `lengthB` property and other param tags):

```xml
<root>
  <option system_pack="1" flash_size="0x20000000" partubi="1"/> 
  <bootcode rotate_flag="0" address0="0" length0="0x00200000" ubiflag ="0"/>
  <bootcode:L1boot  rotate_flag="0" address0="0" length0="0x00040000" ubiflag ="0"/>
  <bootcode:L2boot  rotate_flag="1" addressA="0x00040000" lengthA="0x00040000"  addressB="0x00080000" lengthB="0x00040000" ubiflag ="0"/>
  <bootcode:eFuse   rotate_flag="0" address0="0x000C0000" length0="0x00040000" ubiflag ="0"/>
  <allsystem rotate_flag="1" addressA="0" lengthA="0x0502A000" addressB="0" lengthB="0x0502A000" ubiflag ="0"/>
  <allsystem:signinfo    rotate_flag="0" address0="-1" length0="-1" ubiflag ="0"/>  
  <allsystem:uboot    rotate_flag="0" address0="-1" length0="-1" ubiflag ="0"/>  
  <allsystem:kernel  rotate_flag="0" address0="-1" length0="-1" ubiflag ="0"/> 
  <allsystem:rootfs  rotate_flag="0" address0="-1" length0="-1" ubiflag ="0"/>
  <ubilayer_v5 rotate_flag="0" address0="0" length0="0x14DBC000" ubiflag ="1"/>
  <ubilayer_v5:flash_config rotate_flag="1" addressA="0" lengthA="0x0003E000" addressB="0" lengthB="0x0003E000" ubiflag ="1"/>
  <ubilayer_v5:slave_param rotate_flag="1" addressA="0" lengthA="0x0003E000" addressB="0" lengthB="0x0003E000" ubiflag ="1"/>
  <ubilayer_v5:wifi_param rotate_flag="1" addressA="0" lengthA="0x0003E000" addressB="0" lengthB="0x0003E000" ubiflag ="1"/>
  <ubilayer_v5:keyfile rotate_flag="0" address0="0" length0="0x0022E000" ubiflag ="1"/>
  <ubilayer_v5:file_system rotate_flag="0" address0="0" length0="0x0141A000" ubiflag ="1"/>
  <ubilayer_v5:app_system rotate_flag="0" address0="0" length0="0x1273A000" ubiflag ="1"/>
</root>
```

### 5.2 Raw Extracted XML (with Memory Corruption)
The raw data read from the flash dump contains a corruption signature within `flash_config lengthA`:

```xml
<root>
<option system_pack="1" flash_size="0x20000000" partubi="1"/> 
<bootcode rotate_flag="0" address0="0" length0="0x00200000" ubiflag ="0"/>
<bootcode:L1boot  rotate_flag="0" address0="0" length0="0x00040000" ubiflag ="0"/>
<bootcode:L2boot  rotate_flag="1" addressA="0x00040000" lengthA="0x00040000"  addressB="0x00080000" lengthB="0x00040000" ubiflag ="0"/>
<bootcode:eFuse   rotate_flag="0" address0="0x000C0000" length0="0x00040000" ubiflag ="0"/>
<allsystem rotate_flag="1" addressA="0" lengthA="0x0502A000" addressB="0" lengthB="0x0502A000" ubiflag ="0"/>
<allsystem:signinfo    rotate_flag="0" address0="-1" length0="-1" ubiflag ="0"/>  
<allsystem:uboot    rotate_flag="0" address0="-1" length0="-1" ubiflag ="0"/>  
<allsystem:kernel  rotate_flag="0" address0="-1" length0="-1" ubiflag ="0"/> 
<allsystem:rootfs  rotate_flag="0" address0="-1" length0="-1" ubiflag ="0"/>
<ubilayer_v5 rotate_flag="0" address0="0" length0="0x14DBC000" ubiflag ="1"/>
<ubilayer_v5:flash_config rotate_flag="1" addressA="0" lengthA="0x0003 Ե)G    	.#
+2Co r  1$C     E` ?n + *E000" addressB="0" lengthB="0x0003E000" ubiflag ="1"/>
<ubilayer_v5:slave_param rotate_flag="1" addressA="0" lengthA="0x0003E000" addressB="0" lengthB="0x0003E000" ubiflag ="1"/>
<ubilayer_v5:wifi_param rotate_flag="1" addressA="0" lengthA="0x0003E000" addressB="0" lengthB="0x0003E000" ubiflag ="1"/>
<ubilayer_v5:keyfile rotate_flag="0" address0="0" length0="0x0022E000" ubiflag ="1"/>
<ubilayer_v5:file_system rotate_flag="0" address0="0" length0="0x0141A000" ubiflag ="1"/>
<ubilayer_v5:app_system rotate_flag="0" address0="0" length0="0x1273A000" ubiflag ="1"/>
</root>
```
