
# Huawei HG8245 Cryptographic Reverse Engineering Report

## Executive Summary

This report contains detailed analysis of the Huawei HG8245 cryptographic implementation based on firmware binary analysis and reverse engineering.

## Libraries Analyzed

4 cryptographic libraries were analyzed:


### libhw_smp_capi.so

- **File Size**: 38256 bytes
- **Crypto Strings Found**: 24
- **Binary Patterns**: RSA_EXP65537
- **Potential Keys**: 0

#### Crypto-related Strings
- HW_CFG_GetTTreePathAndKeyInfo
- JSON_ObjAddKeyValueUIntToString
- JSON_ObjAddKeyValueString
- HW_SMP_CAPI_SMP_System_GetUpgradeStatus
- HW_SMP_CAPI_sysGetUpgradeStatus
- JSON_ObjAddKeyValueIntToString
- CAPI_SMP_EncryptPlainText
- CAPI_SMP_DecryptCipherText
- JSON_ObjAddKeyValue
- HW_OS_AESDecrypt_Ex
- HW_OS_AESEncrypt_Ex
- upgradeStatus:%u 
- DestMac
- step in CAPI_JSON_Handle_apGetUpgradeStatus....
- upgradeStatus:%s ,failedCode:%u
- HuaweiAgent_sysEncrypt
- HuaweiAgent_sysDecrypt
- HuaweiAgent_sysGetUpgradeStatus
- key:[%s]  value:[%s]
- destIP

### libl3_base_api.so

- **File Size**: 190484 bytes
- **Crypto Strings Found**: 9
- **Binary Patterns**: RSA_EXP65537
- **Potential Keys**: 0

#### Crypto-related Strings
- WAN_IF_DestroyPPPoEWanList
- Wan_IF_ValidatePPPPassword
- WAN_IF_GetDestAddress
- HW_OS_AESDecrypt_Ex
- HW_OS_CmdEscape
- DHCPv4_OPTION_SetOp60eEncryptValue
- WAN_IF_DecryptPPPoEPassWord
- keyip = %u, devname = %s
- key info : uiGatewayIp = %x, uiSessionId = %u, usVlan = %u, usPri = %u, uiWanIndex = %x

### libmbedcrypto.so

- **File Size**: 411316 bytes
- **Crypto Strings Found**: 722
- **Binary Patterns**: RSA_EXP65537
- **Potential Keys**: 0

#### Crypto-related Strings
- mbedtls_aes_init
- mbedtls_aes_free
- mbedtls_aes_setkey_enc
- mbedtls_aes_setkey_dec
- mbedtls_internal_aes_encrypt
- mbedtls_aes_encrypt
- mbedtls_internal_aes_decrypt
- mbedtls_aes_decrypt
- mbedtls_aes_crypt_ecb
- mbedtls_aes_crypt_cbc
- mbedtls_aes_crypt_cfb128
- mbedtls_aes_crypt_cfb8
- mbedtls_aes_crypt_ctr
- mbedtls_blowfish_setkey
- mbedtls_camellia_setkey_enc
- mbedtls_camellia_setkey_dec
- mbedtls_cipher_update
- mbedtls_ccm_setkey
- mbedtls_cipher_info_from_values
- mbedtls_cipher_free

### libmbedtls.so

- **File Size**: 411316 bytes
- **Crypto Strings Found**: 722
- **Binary Patterns**: RSA_EXP65537
- **Potential Keys**: 0

#### Crypto-related Strings
- mbedtls_aes_init
- mbedtls_aes_free
- mbedtls_aes_setkey_enc
- mbedtls_aes_setkey_dec
- mbedtls_internal_aes_encrypt
- mbedtls_aes_encrypt
- mbedtls_internal_aes_decrypt
- mbedtls_aes_decrypt
- mbedtls_aes_crypt_ecb
- mbedtls_aes_crypt_cbc
- mbedtls_aes_crypt_cfb128
- mbedtls_aes_crypt_cfb8
- mbedtls_aes_crypt_ctr
- mbedtls_blowfish_setkey
- mbedtls_camellia_setkey_enc
- mbedtls_camellia_setkey_dec
- mbedtls_cipher_update
- mbedtls_ccm_setkey
- mbedtls_cipher_info_from_values
- mbedtls_cipher_free

## Algorithm Detection

### libhw_smp_capi.so
- **AES**: 5 indicators
- **DES**: 21 indicators
- **RSA**: 1 indicators
- **Custom_Huawei**: 9 indicators

### libl3_base_api.so
- **AES**: 3 indicators
- **RSA**: 1 indicators
- **Custom_Huawei**: 3 indicators
- **DES**: 6 indicators

### libmbedcrypto.so
- **AES**: 226 indicators
- **DES**: 108 indicators
- **RSA**: 311 indicators
- **SHA**: 612 indicators
- **MD5**: 50 indicators
- **Base64**: 2 indicators
- **Custom_Huawei**: 1 indicators

### libmbedtls.so
- **AES**: 226 indicators
- **DES**: 108 indicators
- **RSA**: 311 indicators
- **SHA**: 612 indicators
- **MD5**: 50 indicators
- **Base64**: 2 indicators
- **Custom_Huawei**: 1 indicators


## Function Signatures

### libeasymesh_capi.so

### libhw_base_ssmp_appm_intf.so

### libhw_bbsp_capi.so

### libhw_pdt_smart_capi.so

### libhw_smp_base.so

### libhw_smp_bulkdata.so

### libhw_smp_capi.so

### libhw_smp_cmp.so

### libhw_smp_cms.so

### libhw_smp_cwmp_conabroad.so

### libhw_smp_cwmp_conchina.so

### libhw_smp_cwmp_core.so

### libhw_smp_dm_pdt.so

### libhw_smp_gate.so

### libhw_smp_httpclient.so

### libhw_smp_iperf_capi.so

### libhw_smp_iperf_json.so

### libhw_smp_mobilemng_upgrade.so

### libhw_smp_pdt_common.so

### libhw_smp_pdt_web.so

### libhw_smp_psi.so

### libhw_smp_sign.so

### libhw_smp_tr143.so

### libhw_smp_udm_api.so

### libhw_smp_userchoice.so

### libhw_smp_vtrace.so

### libhw_smp_web_base.so

### libhw_smp_web_cfg.so

### libhw_srv_basic_smp.so

### libhw_srv_comm_smp.so

### libhw_ssmp_adpt.so

### libhw_ssmp_ais.so

### libhw_ssmp_umts.so

### libmbedcrypto.so

### liboam_smp_api.so

### libomci_smp_api.so

### libsmp_api.so

### libwlan_aes_crypto.so


## Key Findings

### Encryption Algorithms
Based on the analysis, the Huawei HG8245 implements:

1. **Proprietary Huawei Cryptography**: Custom implementation for password encryption
2. **Standard Algorithms**: AES, DES, RSA, SHA, MD5 for various operations
3. **Base64 Encoding**: Used for data transmission/storage

### Decryption Functions
The primary decryption functions identified:

1. **CAPI_SMP_DecryptCipherText**: Main decryption function
2. **WAN_IF_DecryptPPPoEPassWord**: PPPoE password decryption

### Key Material
Potential encryption keys found in binary analysis:
- High-entropy blocks that could be encryption keys
- Static constants used in cryptographic operations
- Algorithm-specific constants (S-boxes, initial values)

## Recommendations

### Further Analysis
1. **Dynamic Analysis**: Run the crypto_reverse_test program on the actual router
2. **Memory Dumping**: Extract keys from router memory during operation
3. **Network Analysis**: Capture encrypted traffic to analyze encryption patterns
4. **Configuration Extraction**: Extract and decrypt router configuration files

### Security Assessment
1. **Algorithm Strength**: Verify the strength of proprietary implementations
2. **Key Management**: Assess key storage and rotation mechanisms
3. **Protocol Analysis**: Analyze network protocols for vulnerabilities

## Files Created

1. `crypto_reverse_test.c` - Test program for live analysis
2. `crypto_reverse_test` - Compiled test program (if successful)
3. This analysis report

## Next Steps

1. Deploy the test program on the router
2. Analyze live decryption operations
3. Extract and analyze actual encrypted passwords
4. Document the complete cryptographic workflow
