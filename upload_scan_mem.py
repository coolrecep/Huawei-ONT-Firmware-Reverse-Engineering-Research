#!/usr/bin/env python3
import os
import subprocess
import paramiko
import time
import base64

HOST     = "192.168.1.1"
USER     = "sUser"
PASSWORD = "EP!99R4HLH9E"

def recv_until(chan, markers, timeout=15):
    if isinstance(markers, str): markers = [markers]
    buf = b""
    start = time.time()
    while time.time() - start < timeout:
        if chan.recv_ready():
            buf += chan.recv(8192)
            decoded = buf.decode('utf-8', errors='replace')
            for m in markers:
                if m in decoded: return decoded
        elif chan.exit_status_ready(): break
        time.sleep(0.1)
    return buf.decode('utf-8', errors='replace')

def run(chan, cmd, timeout=20):
    chan.send(cmd + "\n")
    return recv_until(chan, "# ", timeout)

def main():
    print("[*] Compiling memory scan hook for ARM (32-bit musl)...")
    cmd = "/home/recep/Masaüstü/Firmware/arm-linux-musleabi-cross/bin/arm-linux-musleabi-gcc -shared -fPIC -o /home/recep/Masaüstü/Firmware/scan_mem_hook.so /home/recep/Masaüstü/Firmware/scan_mem_hook.c"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Compile failed: {res.stderr}")
        return

    with open("/home/recep/Masaüstü/Firmware/scan_mem_hook.so", "rb") as f:
        so_data = f.read()
    b64_so = base64.b64encode(so_data).decode('utf-8')
    
    print(f"[*] Compiled size: {len(so_data)} bytes. Connecting via SSH...")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=15,
                   look_for_keys=False, allow_agent=False)
    chan = client.invoke_shell(width=220, height=50)
    time.sleep(2)
    out = recv_until(chan, ["WAP>", "Remove one session", "Enter the ID"], timeout=8)
    if "Remove one session" in out or "Enter the ID" in out:
        chan.send("1\n"); time.sleep(2); recv_until(chan, "WAP>", timeout=10)
    chan.send("su\n");    recv_until(chan, ["SU_WAP>"], timeout=8)
    chan.send("shell\n"); recv_until(chan, "# ", timeout=8)
    
    print("[*] Uploading hook library via base64...")
    run(chan, "cat << 'EOF' > /tmp/hook.b64")
    chunk_size = 500
    for i in range(0, len(b64_so), chunk_size):
        chan.send(b64_so[i:i+chunk_size] + "\n")
        time.sleep(0.05)
    run(chan, "EOF")
    
    # We will use awk to decode it since base64 applet is missing
    print("[*] Decoding base64 using awk...")
    awk_decoder = r"""
awk 'BEGIN {
    b64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    for (i=0; i<64; i++) {
        val[substr(b64, i+1, 1)] = i
    }
}
{
    len = length($0)
    for (i=1; i<=len; i+=4) {
        c1 = substr($0, i, 1); c2 = substr($0, i+1, 1)
        c3 = substr($0, i+2, 1); c4 = substr($0, i+3, 1)
        if (c1 == "=") break
        v1 = val[c1]; v2 = val[c2]
        v3 = (c3 == "=") ? 0 : val[c3]
        v4 = (c4 == "=") ? 0 : val[c4]
        
        b1 = lshift(v1, 2) + rshift(v2, 4)
        b2 = lshift(and(v2, 15), 4) + rshift(v3, 2)
        b3 = lshift(and(v3, 3), 6) + v4
        
        printf "%c", b1
        if (c3 != "=") printf "%c", b2
        if (c4 != "=") printf "%c", b3
    }
}' /tmp/hook.b64 > /tmp/scan_mem_hook.so
"""
    run(chan, awk_decoder)

    out = run(chan, "ls -la /tmp/scan_mem_hook.so")
    print(f"[*] Uploaded library:\n{out.strip()[-200:]}")
    
    # Wait, we want to scan the memory of `ssmp` itself, right?
    # Because if the table is built dynamically, it is built inside the `ssmp` process memory.
    # If we run `ls` with LD_PRELOAD, we are only scanning the memory of `ls`!
    # And `ls` does NOT build the ALPHA table.
    
    # How do we scan `ssmp` memory?
    # Option 1: Create a standalone C program to read /proc/1650/mem.
    # Option 2: Preload into `ssmp` by killing and restarting it (too risky, might drop connection).
    # Option 3: Compile a statically linked standalone C program to read /proc/<pid>/mem!
    # Since we need to read /proc/1650/mem, and we are srv_clid, wait, `srv_clid` CANNOT read `/proc/1650/mem`!
    
    print("[*] We cannot scan ssmp memory from srv_clid.")
    print("[*] To scan it, we must compile a setuid-like tool, or inject it using WAP CLI.")
    
    client.close()

if __name__ == "__main__":
    main()
