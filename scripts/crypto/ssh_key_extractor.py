#!/usr/bin/env python3
"""
SSH-based Router Key Extraction Tool
Uses SSH to extract encryption keys when Telnet is limited
"""

import subprocess
import time
import re
import json
from pathlib import Path

class SSHKeyExtractor:
    def __init__(self, host="192.168.1.1", username="sUser", password="EP!99R4HLH9E"):
        self.host = host
        self.username = username
        self.password = password
        self.results = {
            "connection_info": {},
            "processes": {},
            "memory_analysis": {},
            "keys_found": [],
            "config_data": {}
        }
        
    def run_ssh_command(self, command, timeout=30):
        """Run SSH command with proper escaping"""
        try:
            # Use sshpass for password authentication
            cmd = f"sshpass -p '{self.password}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o ServerAliveInterval=30 {self.username}@{self.host} '{command}'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            return "", str(e), 1
    
    def test_connection(self):
        """Test SSH connection"""
        print("[*] Testing SSH connection...")
        stdout, stderr, code = self.run_ssh_command("echo 'SSH_CONNECTION_TEST'")
        
        if code == 0 and "SSH_CONNECTION_TEST" in stdout:
            print("[+] SSH connection successful!")
            self.results["connection_info"]["ssh"] = "successful"
            return True
        else:
            print(f"[-] SSH connection failed: {stderr}")
            self.results["connection_info"]["ssh"] = f"failed: {stderr}"
            return False
    
    def get_system_info(self):
        """Gather basic system information"""
        print("[*] Gathering system information...")
        
        commands = {
            "uname": "uname -a",
            "processes": "ps aux | head -50",
            "memory": "free -m",
            "mounts": "mount | head -20",
            "version": "cat /proc/version"
        }
        
        for name, cmd in commands.items():
            stdout, stderr, code = self.run_ssh_command(cmd)
            if code == 0 and stdout:
                self.results["processes"][name] = stdout
                print(f"  [+] Got {name}")
    
    def find_crypto_processes(self):
        """Find processes related to cryptography"""
        print("[*] Finding crypto processes...")
        
        crypto_cmd = """
for pid in $(ls /proc | grep -E '^[0-9]+$'); do
    if [ -f "/proc/$pid/cmdline" ]; then
        cmdline=$(cat /proc/$pid/cmdline | tr '\\0' ' ')
        if echo "$cmdline" | grep -qiE 'crypto|cipher|decrypt|encrypt|smp|capi'; then
            echo "PID:$pid:$cmdline"
        fi
    fi
done
"""
        
        stdout, stderr, code = self.run_ssh_command(crypto_cmd)
        if code == 0 and stdout:
            self.results["processes"]["crypto_pids"] = stdout
            pids = [line.split(':')[1] for line in stdout.split('\n') if ':' in line]
            print(f"  [+] Found {len(pids)} crypto processes")
            return pids
        return []
    
    def extract_memory_keys(self, pid):
        """Extract keys from process memory"""
        print(f"[*] Extracting keys from PID {pid}...")
        
        # Get process info
        info_cmd = f"""
echo "=== Process {pid} ==="
cat /proc/{pid}/cmdline 2>/dev/null | tr '\\0' ' '
echo "---"
cat /proc/{pid}/maps 2>/dev/null | grep 'rw-' | head -10
"""
        
        stdout, stderr, code = self.run_ssh_command(info_cmd)
        if code == 0:
            self.results["memory_analysis"][f"info_{pid}"] = stdout
            
            # Try to dump memory from key regions
            dump_cmd = f"""
if [ -r /proc/{pid}/mem ]; then
    echo "Memory readable, dumping..."
    # Try different offsets where keys might be
    for offset in 0x1000 0x10000 0x100000 0x1000000; do
        echo "Dumping from offset $offset..."
        dd if=/proc/{pid}/mem bs=1 skip=$((offset)) count=2048 2>/dev/null | strings -n 16 | head -5
        echo "---"
    done
else
    echo "Memory not readable"
fi
"""
            
            dump_stdout, dump_stderr, dump_code = self.run_ssh_command(dump_cmd, timeout=60)
            if dump_code == 0:
                self.results["memory_analysis"][f"dump_{pid}"] = dump_stdout
                
                # Search for keys in dump
                keys = self.find_keys_in_text(dump_stdout)
                for key in keys:
                    self.results["keys_found"].append({
                        "pid": pid,
                        "key": key,
                        "method": "memory_dump"
                    })
                    print(f"      [+] Potential key: {key[:50]}...")
    
    def find_keys_in_text(self, text):
        """Find potential encryption keys in text"""
        keys = []
        
        patterns = [
            r'[A-Fa-f0-9]{32}',  # 128-bit hex key
            r'[A-Fa-f0-9]{48}',  # 192-bit hex key
            r'[A-Fa-f0-9]{64}',  # 256-bit hex key
            r'[A-Za-z0-9+/]{32}={0,2}',  # Base64 key
            r'[A-Za-z0-9+/]{44}={0,2}',  # Longer Base64 key
            r'key[=:]\s*[A-Fa-f0-9A-Za-z+/=]{16,}',  # key: value
            r'password[=:]\s*[A-Fa-f0-9A-Za-z+/=]{16,}',  # password: value
            r'secret[=:]\s*[A-Fa-f0-9A-Za-z+/=]{16,}',  # secret: value
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) >= 16:  # Minimum key length
                    keys.append(match)
        
        return list(set(keys))  # Remove duplicates
    
    def trigger_crypto_operations(self):
        """Trigger cryptographic operations and capture keys"""
        print("[*] Triggering crypto operations...")
        
        trigger_script = '''
# Create crypto trigger program
cat > /tmp/crypto_trigger.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>

// Mock missing symbols
int HW_Mobilemng_SetTaskSource() { return 0; }
int SRV_COMM_GetNewExportType() { return 0; }
void* SRV_COMM_GetExportValue() { return NULL; }
void* CAPI_SMP_GetWanInterfaceStatus() { return NULL; }

int main() {
    void *handle;
    int (*decrypt_func)(const char*, char*);
    char output[1024];
    
    printf("=== Starting Crypto Operations ===\\n");
    
    // Test with various inputs to trigger key generation
    const char* test_inputs[] = {
        "admin",
        "superonline", 
        "password",
        "test123",
        "huawei",
        "default",
        "root",
        "telecomadmin",
        "123456",
        "config"
    };
    
    // Test primary function
    handle = dlopen("/lib/libhw_smp_capi.so", RTLD_LAZY);
    if (handle) {
        decrypt_func = dlsym(handle, "CAPI_SMP_DecryptCipherText");
        if (decrypt_func) {
            printf("Testing CAPI_SMP_DecryptCipherText...\\n");
            for (int i = 0; i < 10; i++) {
                memset(output, 0, sizeof(output));
                int result = decrypt_func(test_inputs[i], output);
                printf("Input: %-15s -> Result: %d, Output: '%s'\\n", 
                       test_inputs[i], result, output);
            }
        }
        dlclose(handle);
    }
    
    // Test fallback function
    handle = dlopen("/lib/libl3_base_api.so", RTLD_LAZY);
    if (handle) {
        decrypt_func = dlsym(handle, "WAN_IF_DecryptPPPoEPassWord");
        if (decrypt_func) {
            printf("\\nTesting WAN_IF_DecryptPPPoEPassWord...\\n");
            for (int i = 0; i < 5; i++) {
                memset(output, 0, sizeof(output));
                int result = decrypt_func(test_inputs[i], output);
                printf("Input: %-15s -> Result: %d, Output: '%s'\\n", 
                       test_inputs[i], result, output);
            }
        }
        dlclose(handle);
    }
    
    printf("=== Crypto Operations Complete ===\\n");
    return 0;
}
EOF

# Compile and run
gcc -o /tmp/crypto_trigger /tmp/crypto_trigger.c -ldl 2>/dev/null
if [ -f /tmp/crypto_trigger ]; then
    echo "Crypto trigger compiled successfully"
    /tmp/crypto_trigger &
    TRIGGER_PID=$!
    echo "Trigger PID: $TRIGGER_PID"
    
    # Wait for crypto operations
    sleep 5
    
    # Try to dump memory while running
    if [ -r /proc/$TRIGGER_PID/mem ]; then
        echo "Dumping crypto process memory..."
        dd if=/proc/$TRIGGER_PID/mem bs=4096 count=100 2>/dev/null | strings -n 32 > /tmp/crypto_keys.txt
        echo "Keys saved to /tmp/crypto_keys.txt"
        
        # Show potential keys
        echo "Potential keys found:"
        grep -E '[A-Fa-f0-9]{32}|[A-Za-z0-9+/]{32}=' /tmp/crypto_keys.txt | head -10
    fi
    
    kill $TRIGGER_PID 2>/dev/null
    rm -f /tmp/crypto_trigger /tmp/crypto_trigger.c /tmp/crypto_keys.txt
else
    echo "Failed to compile crypto trigger"
fi
'''
        
        stdout, stderr, code = self.run_ssh_command(trigger_script, timeout=120)
        if code == 0:
            self.results["memory_analysis"]["crypto_trigger"] = stdout
            print("  [+] Crypto trigger executed")
            
            # Look for keys in output
            keys = self.find_keys_in_text(stdout)
            for key in keys:
                self.results["keys_found"].append({
                    "source": "crypto_trigger",
                    "key": key
                })
    
    def extract_config_passwords(self):
        """Extract passwords from configuration files"""
        print("[*] Extracting configuration passwords...")
        
        config_commands = {
            "uci_config": "uci show 2>/dev/null | grep -i password | head -20",
            "wireless_config": "find /etc -name '*wireless*' -exec cat {} \\; 2>/dev/null | head -100",
            "hostapd_config": "find /tmp -name '*hostapd*' -exec cat {} \\; 2>/dev/null | head -50",
            "config_files": "find /etc -name '*.conf' -exec grep -l 'password\\|psk\\|key' {} \\; 2>/dev/null | head -10",
            "env_vars": "env | grep -iE 'password|key|secret' | head -20"
        }
        
        for name, cmd in config_commands.items():
            stdout, stderr, code = self.run_ssh_command(cmd)
            if code == 0 and stdout:
                self.results["config_data"][name] = stdout
                print(f"  [+] Got {name}")
                
                # Look for keys in config
                keys = self.find_keys_in_text(stdout)
                for key in keys:
                    self.results["keys_found"].append({
                        "source": f"config_{name}",
                        "key": key
                    })
    
    def check_busybox_availability(self):
        """Check if busybox is available or can be installed"""
        print("[*] Checking tool availability...")
        
        tools_check = {
            "busybox": "which busybox",
            "strings": "which strings", 
            "hexdump": "which hexdump",
            "dd": "which dd",
            "gcc": "which gcc"
        }
        
        available_tools = {}
        for tool, cmd in tools_check.items():
            stdout, stderr, code = self.run_ssh_command(cmd)
            if code == 0 and stdout and "not found" not in stdout:
                available_tools[tool] = True
                print(f"  [+] {tool}: Available")
            else:
                available_tools[tool] = False
                print(f"  [-] {tool}: Not available")
        
        self.results["connection_info"]["available_tools"] = available_tools
        
        if not available_tools.get("busybox"):
            print("  [*] busybox not available - you can install via USB")
            print("      1. Download busybox binary")
            print("      2. Copy to USB drive") 
            print("      3. Insert USB into router")
            print("      4. Mount: mount /dev/sda1 /mnt")
            print("      5. Copy: cp /mnt/busybox /tmp/")
            print("      6. Execute: chmod +x /tmp/busybox")
    
    def save_results(self):
        """Save extraction results"""
        output_dir = Path("/home/recep/Masaüstü/Firmware/ssh_extraction")
        output_dir.mkdir(exist_ok=True)
        
        # Save JSON results
        with open(output_dir / "ssh_key_extraction.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        # Save text results
        with open(output_dir / "ssh_extraction_summary.txt", "w") as f:
            f.write("=== SSH Router Key Extraction Summary ===\n")
            f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Host: {self.host}\n")
            f.write(f"User: {self.username}\n\n")
            
            f.write("=== Connection Info ===\n")
            for key, value in self.results["connection_info"].items():
                f.write(f"{key}: {value}\n")
            
            f.write(f"\n=== Keys Found ({len(self.results['keys_found'])}) ===\n")
            for i, key_info in enumerate(self.results["keys_found"], 1):
                f.write(f"{i}. {key_info}\n")
            
            f.write(f"\n=== Crypto Processes ===\n")
            if "crypto_pids" in self.results["processes"]:
                f.write(self.results["processes"]["crypto_pids"])
            
            f.write(f"\n=== Available Tools ===\n")
            if "available_tools" in self.results["connection_info"]:
                for tool, available in self.results["connection_info"]["available_tools"].items():
                    status = "Available" if available else "Not Available"
                    f.write(f"{tool}: {status}\n")
        
        print(f"\n[+] Results saved to: {output_dir}")
        print(f"    - JSON: ssh_key_extraction.json")
        print(f"    - Summary: ssh_extraction_summary.txt")
        
        # Print summary
        print(f"\n=== SSH EXTRACTION SUMMARY ===")
        print(f"Keys found: {len(self.results['keys_found'])}")
        print(f"Processes analyzed: {len([k for k in self.results['memory_analysis'].keys() if 'info_' in k])}")
        print(f"Config files analyzed: {len(self.results['config_data'])}")
        
        if self.results["keys_found"]:
            print(f"\n=== KEYS FOUND ===")
            for i, key_info in enumerate(self.results["keys_found"][:10], 1):
                print(f"{i}. {key_info['key'][:100]}...")
    
    def run_extraction(self):
        """Run complete SSH key extraction"""
        print("=== SSH Router Key Extraction ===")
        
        if not self.test_connection():
            return False
        
        self.get_system_info()
        self.check_busybox_availability()
        
        crypto_pids = self.find_crypto_processes()
        for pid in crypto_pids[:5]:  # Limit to first 5
            self.extract_memory_keys(pid)
        
        self.trigger_crypto_operations()
        self.extract_config_passwords()
        self.save_results()
        
        return True

if __name__ == "__main__":
    extractor = SSHKeyExtractor()
    extractor.run_extraction()
