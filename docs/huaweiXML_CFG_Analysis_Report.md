# Huawei ONT Config Cryptography Analysis Report (`huaweiXML_CFG.exe`)

This report provides a detailed cryptographic analysis of `huaweiXML_CFG.exe` (found in `R23R24/华为配置加解密工具.exe`), which is used to encrypt/decrypt Huawei ONT XML configurations and decrypt stored password hashes. The findings detailed here were retrieved via Ghidra-based decompilation and verified using our standalone Python implementation.

---

## 1. Configuration File Format & Structure

Encrypted configuration files (e.g., `hw_ctree.xml.enc` or router `.cfg` backups) follow a structured binary layout consisting of a header, salt, ciphertext, and HMAC signature.

### Layout Overview
| Offset (Bytes) | Size (Bytes) | Description |
| :--- | :--- | :--- |
| `0` | `4` | Magic Header (`01 00 00 00`) |
| `4` | `4` | Custom CRC-32 (Little-Endian) of the GZIP-compressed payload |
| `8` | `16` | Cryptographic Salt / Initialization Vector (IV) |
| `24` | `N * 16` | AES-256-CBC Encrypted Ciphertext (GZIP compressed payload + zero-padding) |
| `24 + Ciphertext` | `32` (or less) | HMAC-SHA256 Signature (derived key over ciphertext) |

*Note: For some `.cfg` files, a 32-byte router header precedes the above magic header, which is skipped by our tool dynamically.*

### 1.1 Custom Chunked CRC-32
The 4-byte CRC-32 in the header is calculated using a standard MSB-first polynomial `0x04C11DB7`. However, it uses a custom chunked algorithm:
1. The GZIP payload is processed in chunks of **1024 bytes**.
2. For each chunk, the CRC-32 is updated byte-by-byte.
3. At the end of **every** chunk, **4 zero bytes** are flushed through the CRC logic to finalise that block.

### 1.2 Key Derivation Function (PBKDF)
The 256-bit AES key is derived dynamically from the 16-byte salt via an iterative SHA-256 algorithm:
- **Base Material:** `salt` concatenated with `16 zero bytes` (32 bytes total).
- **Salt String:** `b"hex:13395537D2730554A176799F6D56A239"` (36 bytes total).
- **Process:** The hash function executes `8192` iterations:
  $$\text{Key}_{i} = \text{SHA256}(\text{Key}_{i-1} \,\|\, \text{Salt String})$$
  Where $\text{Key}_{0} = \text{salt} \,\|\, \text{0x00}^{16}$. The final 32-byte hash is the AES key.

### 1.3 Padding Scheme
The GZIP payload size is stored implicitly in the salt. The lower 4 bits of the GZIP payload size are embedded into the last byte of the salt during encryption:
$$\text{salt}[15] = (\text{raw\_salt}[15] \ \& \ \text{0xf0}) \ | \ (\text{gzip\_len} \ \& \ \text{0x0f})$$
During decryption, the padding is trimmed from the last decrypted AES block:
$$\text{bytes\_to\_trim} = 16 - (\text{salt}[15] \ \& \ \text{0x0f})$$
This allows the program to reconstruct the exact size of the GZIP stream before decompression.

---

## 2. Password Decryption Modes

Huawei configurations store passwords and sensitive parameters in base-93 encoded formats with different prefixes. `huaweiXML_CFG.exe` exposes three decryption modes.

### Base-93 Encoding
Input ciphertexts (excluding prefixes/suffixes) are mapped from printable characters back to integer values in the base-93 space. Character mapping follows:
- The character `~` (ASCII `0x7e`) maps to `0x1e`.
- All other characters map to `ASCII - 0x21`.
- A 20-character block represents four 32-bit little-endian integers (16 bytes).

---

### 2.1 Mode 1 (`$1...$`)
Used for legacy passwords. 
- **Algorithm:** AES-256-ECB.
- **Block Layout:** Processed in blocks of 24 characters.
  - The first 20 characters decode to 16 bytes of ciphertext.
  - The last 4 characters dynamically modify the hardcoded key at positions `11`, `17`, `23`, and `29`.
- **Hardcoded Key Template (`PWD_KEY_MODE1`):**
  `b8 36 3c 9b 77 da ed 4b 9a bb 9f 2f 6d f5 f1 d5 cb 64 97 5d 5d 3b ce e8 82 7f 2f 42 23 5f 92 29`

---

### 2.2 Mode 2 (`$2...$`)
Used for modern passwords, Wi-Fi keys, and tokens.
- **Algorithm:** AES-256-CBC.
- **Block Layout:** Processed in blocks of 20 characters.
  - The final 20-character block is decoded to produce the **Initialization Vector (IV)** (16 bytes).
  - All preceding blocks decode to the ciphertext stream.
- **Hardcoded Key (`PWD_KEY_MODE2`):**
  `6f c6 e3 43 6a 53 b6 31 0d c0 9a 47 54 94 ac 77 4e 7a fb 21 b9 e5 8f c8 e5 8b 56 60 e4 8e 24 98`

---

### 2.3 Mode 3 (`de_su` / Superuser)
Used to generate the daily superuser (`su`) password from an 8-character seed challenge.
1. The 8 characters are mapped:
   - If ASCII code $\le 71$, multiply by 2.
   - If ASCII code $> 71$, divide by 2 (integer division).
2. The MD5 hash of these modified 8 bytes is computed.
3. The first 8 bytes of the MD5 digest are mapped back to ASCII printable characters:
   $$\text{char}_i = (\text{digest}[i] \pmod{90}) + 33$$
   If the mapped character is `?` (ASCII 63), it is replaced by `>` (ASCII 62).
4. The output is a printable 8-character string.

---

## 3. Tool Verification and Capabilities

Our offline utility `scripts/crypto/huawei_xml_cfg_tool.py` implements all of these reverse-engineered components in Python 3.

### Capabilities:
- **XML configuration decryption:** Decrypts any `.enc` configuration file back to standard readable XML.
- **XML configuration encryption:** Recompresses the XML using GZIP, computes the custom chunked CRC-32, performs AES-256-CBC encryption with dynamic PBKDF, and writes a valid HMAC-SHA256 signature.
- **Password decryption:** Auto-detects and decrypts Mode 1, Mode 2, and Mode 3 hashes.

### Decryption Test Runs on Actual `hw_ctree.xml` Data:
- **WPA Wi-Fi Key Decryption (Mode 2):**
  - Ciphertext: `$2,t}i4H/rN%*Ad^@>a#Y7n*ioL)}/a=kb7m$-K8SF$`
  - Plaintext: `82188306` (standard WPS PIN)
- **Superuser CLI password (Mode 2):**
  - Ciphertext: `$2E\c^%:rrwHfV*nC|:4-NV|#LA*#@=I@r.V(IQ-lP$`
  - Plaintext: `EP!99R4HLH9E`
- **TR-069 Connection Request Password (Mode 2):**
  - Ciphertext: `$2^y!%<W-&}QL>H'+bT,{U^AwC:"k-O$WrRk.`u!(Z$`
  - Plaintext: `superonlineacs`
