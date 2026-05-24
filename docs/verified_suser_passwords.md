# Verified sUser CLI Passwords & Extraction Methodologies

Through reverse engineering of multiple Huawei ONT NAND flash dumps, three active superuser (`sUser`) CLI passwords have been successfully extracted and verified.

---

## 1. Verified Passwords Registry

The following table lists the active devices, their ISP bases, recovered passwords, and where they were stored in the flash dump:

| Device Model | ISP Base / Operator | Verified CLI Password | Storage Location / Signature |
|:---|:---|:---|:---|
| **HG8245X6** | Superonline (Turkcell) | `KP!4RYV=K34T` | `hw_ctree.xml` (LZO literal) |
| **HG8245X6** (Older) | Superonline (Turkcell) | `EP!99R4HLH9E` | Derived via Serial Number KDF (detailed in reports) |
| **EG8145V5** | Turkcell | `U3YELC4J#X39` | Standalone `CMEI` configuration metadata file |

---

## 2. Extraction Methodologies & Workflows

Different firmware versions and hardware configurations store the CLI credentials in distinct formats. Two main extraction paths were identified and implemented:

### 2.1 Whole-File Regex Search (LZO Compressed XMLs)
- **Target:** `HG8245X6 (Superonline)`
- **Password Location:** Nested inside the `hw_ctree.xml` configuration tree as an XML attribute value (`password="..."`).
- **Mechanism:**
  - The configuration file is stored in an LZO-compressed format on the flash partition.
  - A whole-file regex search is executed across the uncompressed config structure to locate key user configuration nodes:
    ```regex
    password="([A-Za-z0-9=!#$@_?]{8,16})"
    ```
  - This successfully extracts the active CLI credential `KP!4RYV=K34T`.

### 2.2 Standalone CMEI File Parsing (Inode Scan)
- **Target:** `EG8145V5 (Turkcell)` (using the `XT26G04C` SPI-NAND chip).
- **Password Location:** Stored as a **plain-text 12-byte string** inside a standalone `CMEI` configuration metadata file located adjacent to the encrypted configuration file on the flash partition.
- **Mechanism:**
  - Rather than being embedded inside the encrypted `hw_ctree` stream, the credential resides in the outer filesystem as a standalone 12-byte metadata file.
  - An **inode scanner** searches the raw block partition for 12-byte files with intact CRC checksums.
  - This successfully extracts the Turkcell CLI credential `U3YELC4J#X39`.
