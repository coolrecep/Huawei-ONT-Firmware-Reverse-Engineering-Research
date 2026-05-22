# Huawei HG8245 Cryptographic Function Extraction Report

## Executive Summary

Based on analysis of the Huawei HG8245 firmware and the provided documentation, I have identified the cryptographic infrastructure and created extraction tools. The firmware uses proprietary Huawei cryptographic functions for password decryption and configuration management.

## Identified Cryptographic Functions

### Primary Decryption Functions

1. **CAPI_SMP_DecryptCipherText**
   - Location: `libhw_smp_capi.so`
   - Purpose: Main decryption function for cipher text
   - Signature: `int CAPI_SMP_DecryptCipherText(const char *in, char *out)`

2. **WAN_IF_DecryptPPPoEPassWord**
   - Location: `libl3_base_api.so` (fallback)
   - Purpose: PPPoE password decryption
   - Signature: `int WAN_IF_DecryptPPPoEPassWord(const char *in, char *out)`

### Library Locations

- **Primary Library**: `squashfs-root-recovered/lib/libhw_smp_capi.so`
- **Fallback Library**: `squashfs-root-recovered/lib/libl3_base_api.so`

## Extraction Tools Created

### 1. decrypt_wrapper.c
A dynamic library wrapper that:
- Loads the target library using `dlopen()`
- Resolves decryption functions
- Provides command-line interface for testing

**Usage**: `./decrypt_wrapper <library> <encrypted_string>`

### 2. hook.c
A constructor-based hook that:
- Automatically runs when library is loaded
- Reads encrypted string from environment variable `PW_TO_DECRYPT`
- Outputs decrypted result

**Usage**: `PW_TO_DECRYPT="encrypted_string" LD_PRELOAD=./hook.so <program>`

### 3. crypto_extractor.py
Comprehensive Python analysis tool that:
- Scans all libraries for cryptographic functions
- Tests decryption capabilities
- Analyzes algorithm usage
- Generates detailed reports

### 4. extract_crypto.sh
Bash-based extraction script that:
- Analyzes libraries using multiple tools
- Tests router connectivity
- Searches for encrypted passwords
- Creates and compiles test programs

## Cryptographic Architecture

### Function Resolution Logic

The decryption system uses a two-tier approach:

1. **Primary**: Attempt `CAPI_SMP_DecryptCipherText`
2. **Fallback**: If primary fails, use `WAN_IF_DecryptPPPoEPassWord`

### Mock Symbol Requirements

The libraries require mock implementations of missing symbols:
- `HW_Mobilemng_SetTaskSource()`
- `SRV_COMM_GetNewExportType()`
- `SRV_COMM_GetExportValue()`
- `CAPI_SMP_GetWanInterfaceStatus()`

## Router Access Information

### Network Configuration
- **IP Address**: 192.168.1.1
- **Default Credentials**: admin/superonline
- **Model**: Huawei HG8245 (ONT-integrated router)

### Access Methods
1. **Web Interface**: HTTP://192.168.1.1
2. **Telnet/SSH**: May be enabled after root access
3. **Firmware Analysis**: Through extracted NAND data

## Usage Instructions

### Basic Decryption Test

```bash
# Compile the wrapper
gcc -o decrypt_wrapper decrypt_wrapper.c -ldl

# Test with primary library
./decrypt_wrapper squashfs-root-recovered/lib/libhw_smp_capi.so "encrypted_string"

# Test with fallback library
./decrypt_wrapper squashfs-root-recovered/lib/libl3_base_api.so "encrypted_string"
```

### Automated Analysis

```bash
# Run comprehensive analysis
python3 crypto_extractor.py

# Or use bash script
./extract_crypto.sh
```

### Hook-based Testing

```bash
# Compile hook
gcc -shared -fPIC -o hook.so hook.c -ldl

# Test with environment variable
PW_TO_DECRYPT="test_string" LD_PRELOAD=./hook.so /bin/echo "test"
```

## Firmware Analysis Context

Based on the provided documentation, extensive firmware analysis has been performed:

### Extracted Components
- **NAND Flash**: Successfully extracted using UBI Reader
- **SquashFS**: Main filesystem identified but with corruption issues
- **Configuration**: Multiple configuration volumes extracted

### Root Access Strategy
The firmware analysis revealed:
1. **Modified SquashFS**: Huawei uses custom LZMA compression
2. **ID Table Issues**: Metadata corruption in filesystem
3. **Configuration Volumes**: Separate encrypted config storage

## Recommendations

### Immediate Actions
1. **Test Decryption**: Use the provided tools with known encrypted strings
2. **Router Connection**: Verify access to 192.168.1.1 with admin/superonline
3. **Config Extraction**: Search configuration volumes for encrypted passwords

### Further Analysis
1. **Reverse Engineering**: Analyze the assembly code in `libhw_smp_capi.so`
2. **Algorithm Identification**: Determine the specific encryption algorithm used
3. **Key Extraction**: Locate encryption keys in the firmware

## Security Considerations

### Identified Vulnerabilities
1. **Weak Default Credentials**: admin/superonline
2. **Proprietary Crypto**: Custom implementation may have weaknesses
3. **Configuration Access**: Encrypted passwords stored in firmware

### Mitigation Recommendations
1. **Change Default Credentials**: Immediately change admin password
2. **Update Firmware**: Check for security updates
3. **Network Isolation**: Restrict management interface access

## Technical Details

### Compilation Requirements
- **GCC**: For C program compilation
- **Python 3**: For analysis scripts
- **Binutils**: objdump, nm for binary analysis
- **Libdl**: Dynamic library loading

### Dependencies
- **libdl.so**: Dynamic linking
- **Standard C Library**: Basic functions
- **ARM Libraries**: For cross-compilation if needed

## Conclusion

The Huawei HG8245 firmware uses a proprietary cryptographic system with two main decryption functions. The extraction tools provided enable testing and analysis of these functions. Further reverse engineering may reveal the specific encryption algorithms and keys used by the system.

The router is accessible at 192.168.1.1 with default credentials, providing an additional avenue for analysis and potential root access acquisition.

## Files Created

1. `decrypt_wrapper.c` - Dynamic library wrapper
2. `hook.c` - Constructor-based hook
3. `crypto_extractor.py` - Python analysis tool
4. `extract_crypto.sh` - Bash extraction script
5. `test_decrypt.c` - Test program (generated by script)
6. `Crypto_Extraction_Report.md` - This report

All tools are ready for immediate use in extracting and analyzing the cryptographic functions from the Huawei HG8245 firmware.
