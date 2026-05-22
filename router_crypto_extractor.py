#!/usr/bin/env python3
"""
Advanced Huawei HG8245 Router Cryptographic Reverse Engineering Tool
Connects to router via SSH/Telnet to extract live encryption keys and algorithms
"""

import paramiko
import telnetlib
import socket
import time
import re
import json
import sys
from pathlib import Path

class RouterCryptoExtractor:
    def __init__(self, host="192.168.1.1", username="sUser", password="EP!99R4HLH9E"):
        self.host = host
        self.username = username
        self.password = password
        self.ssh_client = None
        self.telnet_client = None
        self.results = {
            "connection_info": {},
            "crypto_keys": [],
            "algorithms": [],
            "config_files": {},
            "memory_dumps": {},
            "live_tests": {}
        }
        
    def connect_ssh(self):
        """Connect to router via SSH"""
        print(f"[*] Attempting SSH connection to {self.host}...")
        
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(self.host, username=self.username, password=self.password, timeout=10)
            
            print("[+] SSH connection successful!")
            self.results["connection_info"]["ssh"] = "successful"
            return True
            
        except Exception as e:
            print(f"[-] SSH connection failed: {e}")
            self.results["connection_info"]["ssh"] = f"failed: {e}"
            return False
            
    def connect_telnet(self):
        """Connect to router via Telnet"""
        print(f"[*] Attempting Telnet connection to {self.host}...")
        
        try:
            self.telnet_client = telnetlib.Telnet(self.host, timeout=10)
            
            # Wait for login prompt
            self.telnet_client.read_until(b"login: ", timeout=5)
            self.telnet_client.write(self.username.encode('ascii') + b"\n")
            
            # Wait for password prompt
            self.telnet_client.read_until(b"Password: ", timeout=5)
            self.telnet_client.write(self.password.encode('ascii') + b"\n")
            
            # Check if login successful
            response = self.telnet_client.read_some()
            if b"#" in response or b"$" in response:
                print("[+] Telnet connection successful!")
                self.results["connection_info"]["telnet"] = "successful"
                return True
            else:
                print("[-] Telnet login failed")
                return False
                
        except Exception as e:
            print(f"[-] Telnet connection failed: {e}")
            self.results["connection_info"]["telnet"] = f"failed: {e}"
            return False
            
    def execute_ssh_command(self, command, timeout=30):
        """Execute command via SSH and return output"""
        if not self.ssh_client:
            return None
            
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=timeout)
            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')
            return {"output": output, "error": error, "exit_code": stdout.channel.recv_exit_status()}
        except Exception as e:
            print(f"[-] SSH command failed: {e}")
            return None
            
    def execute_telnet_command(self, command, timeout=10):
        """Execute command via Telnet and return output"""
        if not self.telnet_client:
            return None
            
        try:
            self.telnet_client.write(command.encode('ascii') + b"\n")
            time.sleep(2)
            response = self.telnet_client.read_very_eager().decode('utf-8', errors='ignore')
            return {"output": response, "error": None}
        except Exception as e:
            print(f"[-] Telnet command failed: {e}")
            return None
            
    def get_system_info(self):
        """Gather basic system information"""
        print("[*] Gathering system information...")
        
        commands = {
            "uname": "uname -a",
            "ps": "ps aux",
            "mount": "mount",
            "df": "df -h",
            "free": "free -m",
            "lsof": "lsof -i",
            "netstat": "netstat -tlnp",
            "dmesg": "dmesg | tail -50"
        }
        
        for name, cmd in commands.items():
            result = self.execute_ssh_command(cmd)
            if result and result["output"]:
                self.results["config_files"][f"system_{name}"] = result["output"]
                print(f"  [+] Got {name}")
                
    def find_crypto_processes(self):
        """Find processes related to cryptography"""
        print("[*] Finding cryptographic processes...")
        
        crypto_commands = [
            "ps aux | grep -i crypto",
            "ps aux | grep -i cipher", 
            "ps aux | grep -i decrypt",
            "ps aux | grep -i encrypt",
            "ps aux | grep -i smp",
            "ps aux | grep -i capi",
            "find /proc -name exe -exec grep -l 'crypto\\|cipher\\|decrypt' {} \\; 2>/dev/null | head -20"
        ]
        
        for cmd in crypto_commands:
            result = self.execute_ssh_command(cmd)
            if result and result["output"]:
                self.results["crypto_keys"].append({"type": "process", "data": result["output"], "command": cmd})
                print(f"  [+] Found crypto processes")
                
    def dump_config_files(self):
        """Dump configuration files that may contain crypto keys"""
        print("[*] Dumping configuration files...")
        
        config_paths = [
            "/etc/config/*",
            "/etc/passwd",
            "/etc/shadow", 
            "/etc/ssl/*",
            "/etc/certificates/*",
            "/tmp/config*",
            "/var/config/*",
            "/mnt/config/*",
            "/proc/version",
            "/proc/cmdline"
        ]
        
        for path in config_paths:
            cmd = f"cat {path} 2>/dev/null || ls -la {path} 2>/dev/null || echo 'File not found'"
            result = self.execute_ssh_command(cmd)
            if result and result["output"] and "not found" not in result["output"]:
                self.results["config_files"][f"config_{path.replace('/', '_').replace('*', 'all')}"] = result["output"]
                print(f"  [+] Dumped {path}")
                
    def search_memory_for_keys(self):
        """Search process memory for encryption keys"""
        print("[*] Searching memory for encryption keys...")
        
        # Find PIDs of crypto-related processes
        find_pids = """
        for pid in $(ls /proc | grep -E '^[0-9]+$'); do
            if [ -f "/proc/$pid/cmdline" ]; then
                cmdline=$(cat /proc/$pid/cmdline | tr '\\0' ' ')
                if echo "$cmdline" | grep -qiE 'crypto|cipher|decrypt|encrypt|smp|capi'; then
                    echo "$pid:$cmdline"
                fi
            fi
        done
        """
        
        result = self.execute_ssh_command(find_pids)
        if result and result["output"]:
            processes = result["output"].strip().split('\n')
            
            for proc in processes:
                if ':' in proc:
                    pid, name = proc.split(':', 1)
                    print(f"  [*] Analyzing PID {pid}: {name}")
                    
                    # Dump memory maps
                    maps_cmd = f"cat /proc/{pid}/maps 2>/dev/null | head -20"
                    maps_result = self.execute_ssh_command(maps_cmd)
                    
                    if maps_result and maps_result["output"]:
                        self.results["memory_dumps"][f"maps_{pid}"] = maps_result["output"]
                        
                    # Search memory for key patterns
                    memory_search = f"""
                    grep -a -E '[A-Za-z0-9+/]{{32,}}=' "/proc/{pid}/mem" 2>/dev/null | head -10 || echo "No base64 keys found"
                    grep -a -E '[0-9a-fA-F]{{32,}}' "/proc/{pid}/mem" 2>/dev/null | head -10 || echo "No hex keys found"
                    """
                    
                    mem_result = self.execute_ssh_command(memory_search)
                    if mem_result and mem_result["output"]:
                        self.results["memory_dumps"][f"memory_{pid}"] = mem_result["output"]
                        
    def analyze_libraries_on_router(self):
        """Analyze cryptographic libraries directly on the router"""
        print("[*] Analyzing libraries on router...")
        
        lib_commands = [
            "find /lib /usr/lib -name '*crypto*' -o -name '*cipher*' -o -name '*smp*' -o -name '*capi*' 2>/dev/null",
            "strings /lib/libhw_smp_capi.so 2>/dev/null | grep -iE 'key|password|secret|decrypt' | head -20",
            "strings /lib/libl3_base_api.so 2>/dev/null | grep -iE 'key|password|secret|decrypt' | head -20",
            "ldd /bin/sh 2>/dev/null | head -10",
            "find / -name '*.so' -exec strings {} \\; 2>/dev/null | grep -iE 'AES|DES|RSA|SHA|MD5' | head -50"
        ]
        
        for cmd in lib_commands:
            result = self.execute_ssh_command(cmd)
            if result and result["output"]:
                self.results["algorithms"].append({"command": cmd, "output": result["output"]})
                print(f"  [+] Library analysis completed")
                
    def test_live_decryption(self):
        """Test live decryption functions on the router"""
        print("[*] Testing live decryption functions...")
        
        # Create test script to run on router
        test_script = """
cat > /tmp/test_crypto.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>

int main() {
    void *handle;
    int (*decrypt_func)(const char*, char*);
    char output[1024];
    
    // Test primary library
    handle = dlopen("/lib/libhw_smp_capi.so", RTLD_LAZY);
    if (handle) {
        decrypt_func = dlsym(handle, "CAPI_SMP_DecryptCipherText");
        if (decrypt_func) {
            int result = decrypt_func("test", output);
            printf("CAPI_SMP_DecryptCipherText test: result=%d, output=%s\\n", result, output);
        }
        dlclose(handle);
    }
    
    // Test fallback library  
    handle = dlopen("/lib/libl3_base_api.so", RTLD_LAZY);
    if (handle) {
        decrypt_func = dlsym(handle, "WAN_IF_DecryptPPPoEPassWord");
        if (decrypt_func) {
            int result = decrypt_func("test", output);
            printf("WAN_IF_DecryptPPPoEPassWord test: result=%d, output=%s\\n", result, output);
        }
        dlclose(handle);
    }
    
    return 0;
}
EOF

gcc -o /tmp/test_crypto /tmp/test_crypto.c -ldl 2>/dev/null && /tmp/test_crypto
rm -f /tmp/test_crypto.c /tmp/test_crypto
"""
        
        result = self.execute_ssh_command(test_script)
        if result and result["output"]:
            self.results["live_tests"]["decryption_test"] = result["output"]
            print(f"  [+] Live decryption test completed")
            
    def extract_wifi_passwords(self):
        """Extract WiFi passwords and encryption keys"""
        print("[*] Extracting WiFi passwords...")
        
        wifi_commands = [
            "iwconfig 2>/dev/null || echo 'iwconfig not available'",
            "cat /etc/config/wireless 2>/dev/null || find /etc -name '*wireless*' -exec cat {} \\; 2>/dev/null",
            "cat /tmp/hostapd.conf 2>/dev/null || find /tmp -name '*hostapd*' -exec cat {} \\; 2>/dev/null",
            "ps aux | grep -i hostapd",
            "find / -name '*.conf' -exec grep -l 'wpa\\|psk\\|key' {} \\; 2>/dev/null | head -10"
        ]
        
        for cmd in wifi_commands:
            result = self.execute_ssh_command(cmd)
            if result and result["output"]:
                self.results["config_files"][f"wifi_{cmd.split()[0].replace('/', '_')}"] = result["output"]
                print(f"  [+] WiFi config extracted")
                
    def dump_nand_flash(self):
        """Attempt to dump NAND flash partitions"""
        print("[*] Attempting NAND flash dump...")
        
        nand_commands = [
            "cat /proc/mtd",
            "cat /proc/partitions", 
            "ls -la /dev/mtd* 2>/dev/null",
            "dd if=/dev/mtd0 of=/tmp/mtd0_dump.bin bs=1M count=1 2>/dev/null && echo 'MTD0 dumped' || echo 'MTD0 dump failed'",
            "hexdump -C /dev/mtd0 2>/dev/null | head -20 || echo 'Cannot read MTD0 directly'"
        ]
        
        for cmd in nand_commands:
            result = self.execute_ssh_command(cmd)
            if result and result["output"]:
                self.results["memory_dumps"][f"nand_{cmd.split()[0].replace('/', '_')}"] = result["output"]
                print(f"  [+] NAND info gathered")
                
    def analyze_running_config(self):
        """Analyze running configuration for crypto settings"""
        print("[*] Analyzing running configuration...")
        
        config_commands = [
            "uci show 2>/dev/null || echo 'UCI not available'",
            "cat /etc/config/* 2>/dev/null | head -100",
            "env | grep -iE 'key|pass|crypto|cipher'",
            "set 2>/dev/null | grep -iE 'key|pass|crypto|cipher'"
        ]
        
        for cmd in config_commands:
            result = self.execute_ssh_command(cmd)
            if result and result["output"]:
                self.results["config_files"][f"running_{cmd.split()[0].replace('/', '_')}"] = result["output"]
                print(f"  [+] Running config analyzed")
                
    def run_full_extraction(self):
        """Run complete cryptographic extraction"""
        print("=== Huawei HG8245 Router Cryptographic Extraction ===")
        
        # Try SSH first, then Telnet as fallback
        if not self.connect_ssh():
            if not self.connect_telnet():
                print("[-] Both SSH and Telnet connections failed")
                return False
                
        # Run all extraction modules
        self.get_system_info()
        self.find_crypto_processes()
        self.dump_config_files()
        self.search_memory_for_keys()
        self.analyze_libraries_on_router()
        self.test_live_decryption()
        self.extract_wifi_passwords()
        self.dump_nand_flash()
        self.analyze_running_config()
        
        # Save results
        self.save_results()
        
        # Cleanup connections
        if self.ssh_client:
            self.ssh_client.close()
        if self.telnet_client:
            self.telnet_client.close()
            
        return True
        
    def save_results(self):
        """Save extraction results to files"""
        output_dir = Path("/home/recep/Masaüstü/Firmware/router_extraction")
        output_dir.mkdir(exist_ok=True)
        
        # Save JSON results
        with open(output_dir / "crypto_extraction_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
            
        # Save individual config files
        config_dir = output_dir / "configs"
        config_dir.mkdir(exist_ok=True)
        
        for name, content in self.results["config_files"].items():
            with open(config_dir / f"{name}.txt", "w") as f:
                f.write(content)
                
        # Save memory dumps
        memory_dir = output_dir / "memory"
        memory_dir.mkdir(exist_ok=True)
        
        for name, content in self.results["memory_dumps"].items():
            with open(memory_dir / f"{name}.txt", "w") as f:
                f.write(content)
                
        print(f"\n[*] Results saved to: {output_dir}")
        print(f"    - JSON: crypto_extraction_results.json")
        print(f"    - Configs: configs/")
        print(f"    - Memory: memory/")
        
        # Print summary
        print(f"\n=== EXTRACTION SUMMARY ===")
        print(f"Config files extracted: {len(self.results['config_files'])}")
        print(f"Memory dumps: {len(self.results['memory_dumps'])}")
        print(f"Algorithm findings: {len(self.results['algorithms'])}")
        print(f"Live tests: {len(self.results['live_tests'])}")

if __name__ == "__main__":
    extractor = RouterCryptoExtractor()
    extractor.run_full_extraction()
