# Huawei ONT Firmware — Interoperability & Diagnostic Research

> **Scope:** Firmware architecture analysis of a Huawei ONT (Optical Network Terminal) running **Dopra Linux / VRP V500R022C10**. This research documents the device's filesystem structure, partition layout, boot chain, cryptographic configuration format, and configuration management — conducted on personally owned hardware for interoperability and right-to-repair purposes.

---

## Legal Framework

This research is conducted under:

- **EU Directive 2009/24/EC** — Permits decompilation and analysis for interoperability purposes
- **DMCA § 1201(f)** — Interoperability exception for reverse engineering
- **Right to Repair** — Device owners' right to diagnose, maintain, and configure their own equipment

All copyrighted firmware images, proprietary binaries, and third-party tools have been removed from this repository. Only original research scripts, architectural documentation, and analysis reports are retained.

---

## Table of Contents

- [Device Overview](#device-overview)
- [Firmware Architecture](#firmware-architecture)
- [NAND Flash Layout](#nand-flash-layout)
- [Boot Chain](#boot-chain)
- [System Services & User Model](#system-services--user-model)
- [Configuration Cryptography](#configuration-cryptography)
- [Repository Structure](#repository-structure)
- [Tools & Scripts](#tools--scripts)
- [Key Architectural Findings](#key-architectural-findings)
- [Responsible Disclosure](#responsible-disclosure)

---

## Device Overview

| Field | Value |
|-------|-------|
| **Manufacturer** | Huawei Technologies Co., Ltd. |
| **OS** | Dopra Linux (VRP platform) |
| **Kernel** | Linux 4.4.240 (ARM, GCC 7.3.0) |
| **Architecture** | ARM (dual-core SMP) |
| **Flash Type** | SPI-NAND, 512 MB |
| **RAM** | 494 MB (visible to Linux) |
| **Rootfs** | SquashFS (read-only) |
| **Persistent Storage** | JFFS2 at `/mnt/jffs2/` |
| **Bootloader** | U-Boot with A/B rotation |
| **PON Support** | GPON + EPON (dual-mode) |

---

## Firmware Architecture

### Firmware Signing

Firmware images are signed with Huawei X.509 certificates:

```
Issuer:  Huawei Code Signing Certificate Authority
CA Root: Huawei Root CA
```

### HWNP Binary Format

Huawei firmware packages use a proprietary binary format:

```
Offset   Size   Field
0x00      4     Magic: "HWNP"
0x06      2     CRC / package length
0x08      8     Timestamp / serial
0x18      4     Header version (0x01)
0x20    ~192    Product ID list (pipe-separated, null-padded)
0x130     4     Payload data length
0x134    ~48    Target URI on device
[data]          Payload (XML, binary, or signed firmware blob)
[sig]           Huawei X.509 PKCS#7 signature
```

---

## NAND Flash Layout

### SPI-NAND: TC58CVG2S0HRA — 512 MB

```
┌─────────────────┬────────────┬────────────┬──────────────────────────┐
│ Partition       │ Start      │ Size       │ Contents                 │
├─────────────────┼────────────┼────────────┼──────────────────────────┤
│ bootcode (raw)  │ 0x00000000 │ 0x00200000 │ Boot ROM (2 MB)          │
│ ubilayer_v5     │ 0x00200000 │ 0x1FE00000 │ UBI container (510 MB)   │
└─────────────────┴────────────┴────────────┴──────────────────────────┘
```

### UBI Volumes inside `ubilayer_v5`

| Volume | Contents |
|--------|----------|
| vol_0 | U-Boot (copy A) |
| vol_1 | U-Boot (copy B) |
| vol_2 | Kernel (copy A) |
| vol_3 | Kernel (copy B) |
| vol_4 | SquashFS rootfs (primary) |
| vol_5 | SquashFS rootfs (copy B) |
| vol_6 | JFFS2 filesystem (`/mnt/jffs2/`) |
| vol_7 | Flash config (A/B) |

For detailed partition specification comparisons (2K page vs. 4K page NAND variants), see [Flash Configuration Analysis Report](docs/hw_flashcfg_Analysis_Report.md).

---

## Boot Chain

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
    ├── 0.wap_init.sh   — Platform init
    └── 1.sdk_init.sh   — SDK init
              │
              └── ssmp (srv_ssmp) — System service manager
```

---

## System Services & User Model

### Service Architecture

The firmware runs multiple isolated service processes with dedicated UIDs:

| Service | UID | Role |
|---------|-----|------|
| `srv_ssmp` | 3008 | System service manager |
| `srv_clid` | 3030 | CLI daemon (write access to `/mnt/jffs2/`) |
| `srv_kmc` | 3020 | Key management (KMC store access) |
| `srv_web` | 3004 | Web interface |
| `cfg_cwmp` | 3007 | TR-069 CWMP agent |
| `cfg_cli` | 3010 | CLI configuration |

### KMC Architecture

The device uses a hardware-backed Key Management Center:

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
KMC hardware chip (encryption/decryption oracle)
```

Cryptographic keys are protected by dedicated hardware. Software-only extraction is not feasible.

### Network Services

| Port | Protocol | Service |
|------|----------|---------|
| 22 | TCP | SSH (Dropbear) |
| 53 | TCP/UDP | DNS |
| 80 | TCP | HTTP web interface |
| 443 | TCP | HTTPS web interface |
| 37225 | TCP | Internal IPC (loopback) |

---

## Configuration Cryptography

Huawei ONT devices store configuration in encrypted XML files (`hw_ctree.xml.enc`). This section documents the cryptographic format for interoperability purposes — enabling device owners to read and manage their own device configuration.

### Encryption Format

| Offset | Size | Description |
|--------|------|-------------|
| 0 | 4 | Magic Header (`01 00 00 00`) |
| 4 | 4 | Custom CRC-32 (chunked, polynomial `0x04C11DB7`) |
| 8 | 16 | Cryptographic Salt / IV |
| 24 | N×16 | AES-256-CBC Encrypted Ciphertext (GZIP payload) |
| 24+N×16 | 32 | HMAC-SHA256 Signature |

### Key Derivation

The AES-256 key is derived from the 16-byte salt via iterative SHA-256 (8192 iterations) — a PBKDF construction. The derivation uses a fixed internal salt string.

### Password Storage Modes

Configuration passwords are stored in three formats:
- **Mode 1** (`$1...$`) — AES-256-ECB with block-dynamic key derivation (legacy)
- **Mode 2** (`$2...$`) — AES-256-CBC (modern passwords, Wi-Fi keys, tokens)
- **Mode 3** (8-char seed) — Custom MD5-based daily superuser challenge

For detailed cryptographic analysis, see [Config Cryptography Analysis Report](docs/huaweiXML_CFG_Analysis_Report.md).

### Python Interoperability Tool

A standalone Python 3 tool (`scripts/crypto/huawei_xml_cfg_tool.py`) replicates the configuration encrypt/decrypt functionality, allowing device owners to read and manage their own configuration without executing untrusted vendor binaries.

```bash
# Decrypt your device's configuration file
python3 scripts/crypto/huawei_xml_cfg_tool.py decrypt-cfg hw_ctree.xml.enc output.xml

# Re-encrypt a modified configuration
python3 scripts/crypto/huawei_xml_cfg_tool.py encrypt-cfg modified.xml output.enc
```

---

## Repository Structure

```
├── README.md                              # Research overview (this file)
├── scripts/
│   ├── extraction/                        # NAND flash analysis & SquashFS extraction tools
│   │   ├── find_hsqs_vol4.py              # Locate SquashFS signatures in NAND dump
│   │   ├── extract_sq.py                  # Extract SquashFS images
│   │   ├── extract_ubi.py                 # UBI volume extraction
│   │   ├── list_ubi_volumes.py            # List UBI volume structure
│   │   ├── scan_dump.py                   # Raw dump scanning
│   │   ├── huawei_nand_cleaner.py         # NAND OOB data cleaner
│   │   └── ...                            # Additional analysis utilities
│   └── crypto/
│       └── huawei_xml_cfg_tool.py         # Config encrypt/decrypt interoperability tool
├── docs/
│   ├── huaweiXML_CFG_Analysis_Report.md   # Configuration cryptography analysis
│   ├── hw_flashcfg_Analysis_Report.md     # Flash partition layout comparison
│   └── huawei_xt26g04c_dump9_Analysis_Report.md  # NAND flash dump analysis
└── .gitignore
```

### Removed Content

The following categories of content have been removed from this repository in compliance with applicable copyright and trade secret law:

- **Firmware images** — All `.bin`, `.squashfs`, and NAND dump files (copyrighted Huawei material)
- **Proprietary tools** — Third-party Windows executables (ONT management, TFTP, identity editors)
- **Configuration files** — Decrypted XML configuration trees (`hw_ctree.xml`)
- **Extracted libraries** — Shared object files from firmware rootfs
- **Cryptographic material** — KMC stores, private keys, certificates
- **ISP provisioning data** — Operator-specific configurations and rebranding toolkits
- **Credential material** — All plaintext passwords, ACS credentials, and default login combinations
- **Raw shell transcripts** — Live device session logs containing sensitive operational data

---

## Tools & Scripts

### Extraction Scripts (`scripts/extraction/`)

Python utilities for analyzing raw NAND flash dumps:

| Script | Purpose |
|--------|---------|
| `find_hsqs_vol4.py` | Locate SquashFS magic bytes in raw dump |
| `extract_sq.py` | Extract SquashFS images from identified offsets |
| `extract_ubi.py` | Extract UBI volumes from raw NAND |
| `list_ubi_volumes.py` | Enumerate UBI volume table |
| `scan_dump.py` | General-purpose dump scanner |
| `huawei_nand_cleaner.py` | Remove OOB data from raw NAND dumps |
| `inspect_layout.py` | Inspect partition layout strings |
| `scan_alignment.py` | Check block alignment in dump |

### Cryptographic Tool (`scripts/crypto/`)

| Script | Purpose |
|--------|---------|
| `huawei_xml_cfg_tool.py` | Decrypt/encrypt configuration files and password hashes (interoperability) |

### External Tools Used

| Tool | Purpose |
|------|---------|
| `sasquatch` | SquashFS extraction (Huawei LZMA variant) |
| `binwalk` | Firmware signature scanning |
| Python 3 | Custom analysis scripts |
| Ghidra | Binary decompilation |

---

## Key Architectural Findings

| # | Finding | Category |
|---|---------|----------|
| 1 | KMC hardware-backed encryption protects device keys via dedicated chip | Security Architecture |
| 2 | A/B rotation scheme for boot, kernel, and rootfs partitions | Reliability |
| 3 | SquashFS rootfs is read-only — all persistence via JFFS2 | Architecture |
| 4 | Configuration files use AES-256-CBC with PBKDF key derivation | Cryptography |
| 5 | Firmware signing uses Huawei X.509 certificate chain | Code Signing |
| 6 | Flash layout differs between 2K and 4K page NAND variants | Hardware Variants |
| 7 | Service isolation via dedicated UIDs with restricted group permissions | Access Control |
| 8 | OSBC flash protocol uses UDP unicast with 252-byte fixed packets | Protocol |

---

## Responsible Disclosure

This research was conducted on personally owned hardware. All findings relate to architectural documentation and interoperability analysis.

- No credentials, vendor secrets, or exploit payloads are distributed in this repository
- Firmware and copyrighted material have been removed
- The configuration cryptography tool is provided for device owners to manage their own equipment
- Architectural findings are documented at a level appropriate for interoperability research

Security-sensitive findings identified during this research were handled through appropriate disclosure channels.

---

*Research conducted for interoperability and diagnostic purposes on owned hardware, in accordance with EU Directive 2009/24/EC and DMCA § 1201(f).*
