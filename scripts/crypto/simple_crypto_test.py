#!/usr/bin/env python3
import os
import subprocess
import sys

def test_crypto_functions():
    """Test the known crypto libraries directly"""
    firmware_path = "/home/recep/Masaüstü/Firmware"
    lib_path = f"{firmware_path}/squashfs-root-recovered/lib"
    
    print("=== Testing Huawei Crypto Functions ===")
    
    # Test libraries
    libs_to_test = [
        f"{lib_path}/libhw_smp_capi.so",
        f"{lib_path}/libl3_base_api.so"
    ]
    
    for lib in libs_to_test:
        if os.path.exists(lib):
            print(f"\n[*] Testing library: {os.path.basename(lib)}")
            
            # Check if library has the functions
            try:
                result = subprocess.run(["nm", "-D", lib], capture_output=True, text=True)
                if result.returncode == 0:
                    functions = [line.strip() for line in result.stdout.split('\n') 
                               if 'FUNC' in line and ('decrypt' in line.lower() or 'encrypt' in line.lower())]
                    if functions:
                        print(f"[+] Found crypto functions:")
                        for func in functions:
                            print(f"    {func}")
                    else:
                        print("[-] No obvious crypto functions found with nm")
                        
                # Try objdump as fallback
                result = subprocess.run(["objdump", "-T", lib], capture_output=True, text=True)
                if result.returncode == 0:
                    all_funcs = [line.strip() for line in result.stdout.split('\n') if 'FUNC' in line]
                    crypto_funcs = [f for f in all_funcs if any(kw in f.upper() for kw in ['DECRYPT', 'ENCRYPT', 'CIPHER', 'CRYPTO'])]
                    if crypto_funcs:
                        print(f"[+] Found with objdump:")
                        for func in crypto_funcs[:5]:  # Limit output
                            print(f"    {func}")
                            
            except Exception as e:
                print(f"[-] Error analyzing {lib}: {e}")
        else:
            print(f"[-] Library not found: {lib}")

def test_router_connection():
    """Test connection to router"""
    print("\n=== Testing Router Connection ===")
    try:
        import urllib.request
        import ssl
        
        context = ssl._create_unverified_context()
        response = urllib.request.urlopen("http://192.168.1.1", timeout=10, context=context)
        print(f"[+] Router responded! Status: {response.getcode()}")
        print(f"[+] Server: {response.headers.get('Server', 'Unknown')}")
        print(f"[+] Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        
        # Read first 1KB of content
        content = response.read(1024).decode('utf-8', errors='ignore')
        if 'HG8245' in content:
            print("[+] Confirmed HG8245 router!")
        if 'login' in content.lower():
            print("[+] Login page detected")
            
    except Exception as e:
        print(f"[-] Could not connect to router: {e}")

def find_encrypted_passwords():
    """Search for encrypted passwords in config files"""
    print("\n=== Searching for Encrypted Passwords ===")
    
    search_paths = [
        "/home/recep/Masaüstü/Firmware/squashfs-root-recovered/etc",
        "/home/recep/Masaüstü/Firmware/squashfs-root-recovered/config",
        "/home/recep/Masaüstü/Firmware/nand_extracted"
    ]
    
    for path in search_paths:
        if os.path.exists(path):
            print(f"[*] Searching in: {path}")
            try:
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.endswith(('.conf', '.cfg', '.txt', '.xml', '.bin')):
                            filepath = os.path.join(root, file)
                            try:
                                with open(filepath, 'rb') as f:
                                    content = f.read(4096)  # Read first 4KB
                                    
                                # Look for password-like patterns
                                import re
                                patterns = [
                                    rb'password[=:]\s*([^\s\n]+)',
                                    rb'passwd[=:]\s*([^\s\n]+)',
                                    rb'admin[=:]\s*([^\s\n]+)',
                                    rb'\$[0-9a-zA-Z]+\$[0-9a-zA-Z/\.]+',
                                    rb'[A-Za-z0-9+/]{20,}={0,2}'
                                ]
                                
                                for pattern in patterns:
                                    matches = re.findall(pattern, content, re.IGNORECASE)
                                    if matches:
                                        print(f"  [+] Found in {file}: {matches[:3]}")
                                        break
                                        
                            except Exception:
                                continue
            except Exception as e:
                print(f"[-] Error searching {path}: {e}")

if __name__ == "__main__":
    test_crypto_functions()
    test_router_connection()
    find_encrypted_passwords()
    print("\n=== Analysis Complete ===")
