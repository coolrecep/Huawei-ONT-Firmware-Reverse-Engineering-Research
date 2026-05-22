#!/usr/bin/env python3
"""
Huawei HG8245 Cryptographic Function Extractor
Extracts and analyzes encryption/decryption functions from firmware libraries
"""

import os
import sys
import subprocess
import struct
import json
from pathlib import Path

class CryptoExtractor:
    def __init__(self, firmware_path="/home/recep/Masaüstü/Firmware"):
        self.firmware_path = Path(firmware_path)
        self.libraries_path = self.firmware_path / "squashfs-root-recovered/lib"
        self.results = {
            "libraries": [],
            "crypto_functions": [],
            "encrypted_strings": [],
            "analysis": {}
        }
        
    def find_crypto_libraries(self):
        """Find libraries that might contain cryptographic functions"""
        print("[*] Searching for cryptographic libraries...")
        
        crypto_patterns = [
            "crypto", "cipher", "decrypt", "encrypt", "aes", "des", "rsa", 
            "sha", "md5", "hash", "ssl", "tls", "smp", "capi", "wan", "pppoe"
        ]
        
        for lib_file in self.libraries_path.glob("*.so"):
            lib_name = lib_file.name.lower()
            if any(pattern in lib_name for pattern in crypto_patterns):
                print(f"[+] Found crypto library: {lib_name}")
                self.results["libraries"].append(str(lib_file))
                
    def analyze_library_functions(self, lib_path):
        """Analyze a library for cryptographic functions"""
        print(f"[*] Analyzing {lib_path}...")
        
        try:
            # Get all symbols
            result = subprocess.run(
                ["objdump", "-T", str(lib_path)], 
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                functions = []
                for line in result.stdout.split('\n'):
                    if 'FUNC' in line and any(keyword in line.upper() for keyword in 
                        ['DECRYPT', 'ENCRYPT', 'CIPHER', 'CRYPTO', 'HASH', 'DIGEST']):
                        functions.append(line.strip())
                
                if functions:
                    self.results["crypto_functions"].extend([
                        {"library": str(lib_path), "function": func} 
                        for func in functions
                    ])
                    print(f"[+] Found {len(functions)} crypto functions in {lib_path.name}")
                    
        except Exception as e:
            print(f"[-] Error analyzing {lib_path}: {e}")
            
    def find_encrypted_strings(self):
        """Search for potentially encrypted strings in firmware"""
        print("[*] Searching for encrypted strings...")
        
        # Common patterns for encrypted data
        patterns = [
            b'\\$[0-9a-zA-Z]+\\$[0-9a-zA-Z/\\.]+',  # Unix password hashes
            b'[A-Za-z0-9+/]{20,}={0,2}',             # Base64 strings
            b'[0-9a-fA-F]{32,}',                    # Hex strings
        ]
        
        # Search in main squashfs and extracted files
        search_paths = [
            self.firmware_path / "main_rootfs.squashfs",
            self.firmware_path / "squashfs-root-recovered"
        ]
        
        for search_path in search_paths:
            if search_path.exists():
                if search_path.is_file():
                    self._search_file_for_encrypted(search_path, patterns)
                else:
                    for file_path in search_path.rglob("*"):
                        if file_path.is_file() and file_path.stat().st_size < 1024*1024:  # < 1MB
                            self._search_file_for_encrypted(file_path, patterns)
                            
    def _search_file_for_encrypted(self, file_path, patterns):
        """Search a single file for encrypted patterns"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
                
            for i, pattern in enumerate(patterns):
                import re
                matches = re.findall(pattern, data)
                if matches:
                    self.results["encrypted_strings"].extend([
                        {"file": str(file_path), "pattern": i, "match": match.decode('ascii', errors='ignore')}
                        for match in matches[:10]  # Limit matches per file
                    ])
                    
        except Exception:
            pass  # Skip files that can't be read as binary
            
    def test_decryption_functions(self):
        """Test the known decryption functions"""
        print("[*] Testing decryption functions...")
        
        # Test strings that might be encrypted passwords
        test_strings = [
            "admin", "root", "superonline", "telecomadmin", "password",
            "123456", "admin123", "huawei", "default"
        ]
        
        libraries_to_test = [
            self.libraries_path / "libhw_smp_capi.so",
            self.libraries_path / "libl3_base_api.so"
        ]
        
        for lib_path in libraries_to_test:
            if lib_path.exists():
                self._test_library_decryption(lib_path, test_strings)
                
    def _test_library_decryption(self, lib_path, test_strings):
        """Test decryption with a specific library"""
        print(f"[*] Testing {lib_path.name}...")
        
        # Compile test program
        test_c = """
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>

int main(int argc, char **argv) {
    if (argc != 3) {
        printf("Usage: %s <library> <string>\\n", argv[0]);
        return 1;
    }
    
    void *handle = dlopen(argv[1], RTLD_LAZY | RTLD_GLOBAL);
    if (!handle) {
        printf("dlopen failed: %s\\n", dlerror());
        return 1;
    }
    
    // Try both functions
    typedef int (*decrypt_func_t)(const char *in, char *out);
    
    decrypt_func_t func1 = (decrypt_func_t)dlsym(handle, "CAPI_SMP_DecryptCipherText");
    decrypt_func_t func2 = (decrypt_func_t)dlsym(handle, "WAN_IF_DecryptPPPoEPassWord");
    
    char out[1024] = {0};
    int result = -1;
    
    if (func1) {
        result = func1(argv[2], out);
        printf("CAPI_SMP_DecryptCipherText: result=%d, output='%s'\\n", result, out);
    }
    
    if (func2) {
        memset(out, 0, sizeof(out));
        result = func2(argv[2], out);
        printf("WAN_IF_DecryptPPPoEPassWord: result=%d, output='%s'\\n", result, out);
    }
    
    if (!func1 && !func2) {
        printf("No decryption functions found\\n");
    }
    
    dlclose(handle);
    return 0;
}
"""
        
        # Write and compile test program
        test_file = self.firmware_path / "test_decrypt.c"
        test_bin = self.firmware_path / "test_decrypt"
        
        with open(test_file, 'w') as f:
            f.write(test_c)
            
        try:
            # Compile for ARM (since this is ARM firmware)
            subprocess.run([
                "gcc", "-o", str(test_bin), str(test_file), "-ldl"
            ], check=True, capture_output=True)
            
            # Test with each string
            for test_str in test_strings:
                try:
                    result = subprocess.run([
                        str(test_bin), str(lib_path), test_str
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.stdout and "result=0" in result.stdout:
                        print(f"[+] Potential success with '{test_str}': {result.stdout.strip()}")
                        
                except subprocess.TimeoutExpired:
                    continue
                    
        except subprocess.CalledProcessError as e:
            print(f"[-] Failed to compile test program: {e}")
            
        # Cleanup
        for f in [test_file, test_bin]:
            if f.exists():
                f.unlink()
                
    def analyze_crypto_algorithms(self):
        """Analyze the cryptographic algorithms used"""
        print("[*] Analyzing cryptographic algorithms...")
        
        # Look for algorithm identifiers in libraries
        crypto_keywords = {
            "AES": ["aes", "AES", "Rijndael"],
            "DES": ["des", "DES", "3DES", "TripleDES"],
            "RSA": ["rsa", "RSA"],
            "SHA": ["sha", "SHA", "SHA1", "SHA256", "SHA512"],
            "MD5": ["md5", "MD5"],
            "Base64": ["base64", "Base64", "B64"],
            "XOR": ["xor", "XOR"],
            "LZMA": ["lzma", "LZMA"],
            "Custom": ["huawei", "HW", "custom", "proprietary"]
        }
        
        for lib_path in self.libraries_path.glob("*.so"):
            try:
                with open(lib_path, 'rb') as f:
                    data = f.read()
                    
                lib_algorithms = {}
                for algo, keywords in crypto_keywords.items():
                    count = sum(data.lower().count(keyword.lower().encode()) for keyword in keywords)
                    if count > 0:
                        lib_algorithms[algo] = count
                        
                if lib_algorithms:
                    self.results["analysis"][str(lib_path)] = lib_algorithms
                    print(f"[+] {lib_path.name}: {lib_algorithms}")
                    
            except Exception:
                continue
                
    def connect_to_router(self):
        """Attempt to connect to router and extract information"""
        print("[*] Attempting to connect to router at 192.168.1.1...")
        
        try:
            import requests
            import warnings
            warnings.filterwarnings('ignore')
            
            # Try basic HTTP connection
            response = requests.get("http://192.168.1.1", timeout=10, verify=False)
            print(f"[+] Router responded with status: {response.status_code}")
            
            # Look for interesting headers or content
            headers = dict(response.headers)
            content = response.text
            
            router_info = {
                "status_code": response.status_code,
                "headers": headers,
                "server": headers.get("Server", "Unknown"),
                "content_length": len(content)
            }
            
            # Look for model info, firmware version, etc.
            if "HG8245" in content:
                router_info["model"] = "HG8245"
            if "firmware" in content.lower():
                router_info["firmware_mentioned"] = True
                
            self.results["router_info"] = router_info
            print(f"[+] Router info: {router_info}")
            
        except Exception as e:
            print(f"[-] Could not connect to router: {e}")
            
    def generate_report(self):
        """Generate a comprehensive report"""
        report_file = self.firmware_path / "crypto_analysis_report.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        print(f"\\n[*] Report saved to: {report_file}")
        
        # Print summary
        print("\\n=== CRYPTOGRAPHIC ANALYSIS SUMMARY ===")
        print(f"Libraries found: {len(self.results['libraries'])}")
        print(f"Crypto functions: {len(self.results['crypto_functions'])}")
        print(f"Encrypted strings: {len(self.results['encrypted_strings'])}")
        print(f"Algorithms detected: {len(self.results['analysis'])}")
        
        if self.results["crypto_functions"]:
            print("\\n=== CRYPTO FUNCTIONS ===")
            for func in self.results["crypto_functions"][:10]:  # Show first 10
                print(f"  {func['library'].split('/')[-1]}: {func['function']}")
                
    def run_full_analysis(self):
        """Run the complete cryptographic analysis"""
        print("=== Huawei HG8245 Cryptographic Analysis ===")
        
        self.find_crypto_libraries()
        self.analyze_crypto_algorithms()
        self.find_encrypted_strings()
        self.test_decryption_functions()
        self.connect_to_router()
        self.generate_report()

if __name__ == "__main__":
    extractor = CryptoExtractor()
    extractor.run_full_analysis()
