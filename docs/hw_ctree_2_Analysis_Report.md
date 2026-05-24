# Analysis of `hw_ctree_2.xml` Configuration File

This report documents the analysis and cryptographic recovery results for `hw_ctree_2.xml`, a decrypted configuration file from a Huawei ONT device. The password hashes inside have been decrypted using our standalone `huawei_xml_cfg_tool.py` script.

---

## 1. File Details
- **File Name:** `hw_ctree_2.xml`
- **File Size:** 198 KB (198,349 bytes)
- **Format:** Uncompressed XML configuration tree
- **ISP Base:** Superonline (same base/operator customization, but containing device-unique credentials and pins)

---

## 2. Decrypted Credentials & Cryptographic Material

Using the Mode 2 ($2...$) base-93 AES-256-CBC decryption logic implemented in our offline tool, the following credentials were successfully recovered:

### 🔑 2.1 WiFi & WPS Credentials
- **WPS Device Password (DevicePassword Instance 1):**
  - Ciphertext: `$2]HfXD^QP|FNi0tX&apos;$O-<~bHFX;mua4<N~T(fT`40$`
  - Plaintext: `18786736` (8-digit WPS Pin)
- **DevicePassword Instance 2:**
  - Ciphertext: `$2)xubPszT_Tx_.{)bfw,-*7&T;3_us9>NA(PZ,h!,$`
  - Plaintext: `52960536`
- **DevicePassword Instance 3:**
  - Ciphertext: `$2,J@%/`LqXO=8^@4^7EZXfh5zRe~ZP6T^D^J`xKl=$`
  - Plaintext: `50466061`

### 🔑 2.2 SIP VoIP & TR-069 Credentials
- **SIP VoIP AuthPassword:**
  - Instance 1: `$2#=H.&km(jB%0QtBBW0FS$m=UB=hZrR"i7$8`=jhE$` $\rightarrow$ `1233211231`
  - Instance 2: `$2J<aHI>HKJKa[zYO9UysB0Ipo3V7D&WEmf^I*."2S$` $\rightarrow$ `1233211232`
- **TR-069 Connection Request Password:**
  - Ciphertext: `$2_l\x,w-7aJ|jZj*tZZOCwA91<v}M.R*42f&@x~"<$`
  - Plaintext: `superonlineacs`
- **TR-069 SIP Password:**
  - Ciphertext: `$2u&{j1bq@y12+bK%cIB8&=!g4>SLIP:bCRCIKQ!_Q$`
  - Plaintext: `superonlineacs`
- **PPPoE Internet Password:**
  - Ciphertext: `$2x'-%E9|'DG;]*aHU_1s*/&OI1qcor7Y<]pA"^3b,$`
  - Plaintext: `fiber`

### 🔑 2.3 User Panel & Admin Hashes
- **Admin Password (admin):**
  - Ciphertext: `$2.HAL-3pWp4[oPz<4z)&*-ExLA0E`6&`CGd#CoA)@',h4QxtRPK=`W/RO&QG.ibCN)}MKpO$0_DEQMI/9^)N;#B2uO>3kuB;ij[B/$`
  - Plaintext: `9feded21ec5437f68036ac6e4f967c4feaddfcb55fcbaf5ecbdfc62871695e2f` (SHA-256 hash of the password)
- **LocalAdminPassword:**
  - Ciphertext: `$27|Z(:8r609b2&%>3u"C-h!48=Jp=uWE"`T<qoii.>y^/PrlTIEttycJ-9p-=naPL8Nx|&DEvD#U<*LzHqPNq'F/u'OiyV@UKbj~D$`
  - Plaintext: `5561a600322789ea670bb3137c1f89c8d18542fe1f2af433baa944306292223b` (SHA-256 hash)
- **CLI superuser password (sUser):**
  - Ciphertext: `$2h\'1#Q#\E#e[0.~4KfmDa<2uEfZKo/X#NjLpL09,v\\}(3)UmKKg}CJqwlb)Sd[f>c@ZAUi^\,K6P;I/fBP_R)$YdV@[UnTaQZX"$`
  - Plaintext: `b0911f86533536d67b4e37addedf9eb31de30404ff6edb423d51ea5f689f949c` (SHA-256 hash)
- **LocalUserPassword:**
  - Ciphertext: `$2#R#iB$}yH!]\<^E7l^dGrK(,22)F]F-lmtD}c.}V*]VmE;M&MBNw=]W|*!@RKVNi.Yu$@>IpkXJs,&):5PP;2zsWM*"\ITP8M-(I$`
  - Plaintext: `9feded21ec5437f68036ac6e4f967c4feaddfcb55fcbaf5ecbdfc62871695e2f` (SHA-256 hash)
- **X_HW_Password (Default / Remote Access):**
  - Ciphertext: `$29|e8FPFwe7tdEPDw'zRU4`R&&<FDF5w5~,'(&(%Kgt;$`
  - Plaintext: `Changeme_123`
- **FactoryPassword:**
  - Ciphertext: `$2,(*V%F/Lv6H>O>.{fUWW!SId&P&D)!eCL5A!K'8#$`
  - Plaintext: `superonline`

---

## 3. Comparison with `hw_ctree.xml`

While both configuration trees are derived from similar ONT firmware installations (Superonline customization), they differ in key device-specific values:

| Parameter | `hw_ctree.xml` | `hw_ctree_2.xml` | Notes |
|:---|:---|:---|:---|
| **WPS Pin** | `82188306` | `18786736` | Device-specific |
| **CLI sUser Password** | `EP!99R4HLH9E` | `b0911f86...` (SHA-256) | `hw_ctree` uses raw text CLI credentials; `hw_ctree_2` hashes it |
| **Admin Panel Hash** | `53ca572a...` | `9feded21...` | Unique SHA-256 hashes |
| **X_HW_Password** | *Not present* | `Changeme_123` | Default firmware fallback parameter present in `hw_ctree_2` |
| **Tokens Prefix** | `9016BA52756F...` | `14EB086A31D4...` | Unique device GUID prefixes |
