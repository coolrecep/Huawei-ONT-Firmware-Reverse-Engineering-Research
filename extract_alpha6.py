#!/usr/bin/env python3
"""
Direct approach: 
- strings /bin/ssmp returned NOTHING (permission or BusyBox issue)
- od gave only 23 bytes (BusyBox od issue with binary files)
- Let's try: cp ssmp to /tmp first, then use hexdump/od on the copy
- Also try: /proc/self/fd approach
- Also: read from the squashfs mount directly
"""

import paramiko, time, struct, zlib

HOST     = "192.168.1.1"
USER     = "sUser"
PASSWORD = "EP!99R4HLH9E"

P1   = "EP!99R4HLH9E"
SN1  = "485754437C07DEA5"

CHECKS_32 = [
    (1,57),(2,72),(3,82),(4,69),(7,57),(10,33),(11,80),
    (15,52),(18,72),(19,69),(22,76),(30,57)
]

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

def connect():
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
    return client, chan

def run(chan, cmd, timeout=20):
    chan.send(cmd + "\n")
    return recv_until(chan, "# ", timeout)

def main():
    print("=" * 62)
    print("  Binary Read Diagnostics + ALPHA Table Hunt")
    print("=" * 62)

    client, chan = connect()
    print("[+] Shell ready\n")

    # ── Diagnostic: can we read the binary at all? ─────────────────────────
    print("[*] Diagnostic: reading /bin/ssmp...")
    out = run(chan, "ls -la /bin/ssmp /proc/$$/exe 2>&1")
    print(out.strip()[-300:])

    # ── Try reading binary via dd ─────────────────────────────────────────
    print("\n[*] dd test (read first 16 bytes of ssmp):")
    out = run(chan, "dd if=/bin/ssmp bs=16 count=1 2>/dev/null | od -An -tx1")
    print(out.strip()[-200:])

    # ── Try cat | od ──────────────────────────────────────────────────────
    print("\n[*] cat /bin/ssmp | od (first 32 bytes):")
    out = run(chan, "dd if=/bin/ssmp bs=1 count=32 2>/dev/null | od -An -tx1")
    print(out.strip()[-200:])
    
    # ── Try copying to /tmp ───────────────────────────────────────────────
    print("\n[*] cp /bin/ssmp /tmp/ssmp_copy && ls -la /tmp/ssmp_copy:")
    out = run(chan, "cp /bin/ssmp /tmp/ssmp_copy 2>&1 && ls -la /tmp/ssmp_copy && echo CP_OK", timeout=30)
    print(out.strip()[-200:])
    
    if "CP_OK" in out:
        print("\n[*] Reading /tmp/ssmp_copy...")
        out = run(chan, "dd if=/tmp/ssmp_copy bs=1 count=32 2>/dev/null | od -An -tx1")
        print(out.strip()[-200:])
        
        # ── Read the rodata section of the copy ──────────────────────────
        # .rodata starts at file offset 0x46f04 = 290564
        rodata_offset = 290564
        rodata_size = 39504
        
        print(f"\n[*] Reading .rodata section from copy (offset={rodata_offset}, size={rodata_size})...")
        # Read in chunks and extract hex
        
        # First: get total size
        out = run(chan, "wc -c /tmp/ssmp_copy")
        print(f"  ssmp size: {out.strip()[-100:]}")
        
        # Read rodata as hex
        print(f"\n[*] Hex dumping .rodata ({rodata_size} bytes at offset {rodata_offset})...")
        cmd = f"dd if=/tmp/ssmp_copy bs=1 skip={rodata_offset} count={rodata_size} 2>/dev/null | od -An -tx1"
        chan.send(cmd + "\n")
        
        hex_output = ""
        print("  Reading hex data...")
        for _ in range(60):  # up to 60 seconds
            if chan.recv_ready():
                chunk = chan.recv(8192).decode('utf-8', errors='replace')
                hex_output += chunk
                if "# " in chunk[-20:]:
                    break
            else:
                time.sleep(1)
        
        print(f"  Got {len(hex_output)} chars of hex output")
        
        # Parse hex tokens
        hex_tokens = []
        for line in hex_output.split('\n'):
            line = line.strip().replace('\r', '')
            if line and 'dd if=' not in line and 'WAP' not in line and '#' not in line:
                tokens = line.split()
                hex_tokens.extend([t for t in tokens if len(t)==2 and 
                                  all(c in '0123456789abcdefABCDEF' for c in t)])
        
        print(f"  Valid hex tokens: {len(hex_tokens)}")
        
        if len(hex_tokens) > 100:
            rodata_bytes = bytes([int(t,16) for t in hex_tokens])
            print(f"  Parsed {len(rodata_bytes)} bytes of .rodata")
            
            with open('/tmp/ssmp_rodata.bin', 'wb') as f:
                f.write(rodata_bytes)
            print("  Saved to /tmp/ssmp_rodata.bin")
            
            # Scan for 32-byte table
            print("\n[*] Scanning .rodata for 32-byte ALPHA table...")
            best_score = 0
            best_off = -1
            for offset in range(len(rodata_bytes) - 32):
                b = rodata_bytes[offset:offset+32]
                score = sum(1 for idx, val in CHECKS_32 if b[idx] == val)
                if score > best_score:
                    best_score = score
                    best_off = offset
                if score >= 8:
                    asc = ''.join(chr(x) if 32<=x<127 else '.' for x in b)
                    hex_s = ' '.join(f'{x:02x}' for x in b)
                    print(f"\n  *** SCORE {score}/12 at .rodata+{offset} ***")
                    print(f"  HEX: {hex_s}")
                    print(f"  ASC: {asc}")
            
            print(f"\n  Best: {best_score}/12 at .rodata+{best_off}")
            if best_off >= 0:
                b = rodata_bytes[best_off:best_off+32]
                print(f"  HEX: {' '.join(f'{x:02x}' for x in b)}")
                print(f"  ASC: {''.join(chr(x) if 32<=x<127 else '.' for x in b)}")
        else:
            print("  [!] Not enough hex data")
    
    # ── Alternative: Use awk to find specific byte patterns ───────────────
    print("\n[*] Searching for the 4-byte anchor '9HRE' in ssmp via awk...")
    # 9=0x39, H=0x48, R=0x52, E=0x45
    # od output format: "39 48 52 45" (at consecutive positions 1,2,3,4)
    # Since od gives 16 bytes per line, the sequence could span line boundaries
    # Simpler: look for the hexdump line containing "39 48 52 45"
    
    out = run(chan, "dd if=/bin/ssmp bs=1 2>/dev/null | od -An -tx1 | grep '39 48 52 45' | head -5", timeout=30)
    print(out.strip()[-300:])

    # ── Get more (SN→password) pairs to fill in the table ─────────────────
    print("\n[*] Getting boardinfo to check for alternate SN...")
    for cmd in [
        "grep -r 'SerialNumber\\|serialnum\\|SN\\|gpon_sn' /etc/ 2>/dev/null | grep -v Binary | head -10",
        "cat /proc/mtd 2>/dev/null | head -10",
        "cat /proc/partitions 2>/dev/null | head -10",
    ]:
        out = run(chan, cmd, timeout=10)
        lines = [l.strip() for l in out.split('\n') if l.strip() and '#' not in l and 'grep' not in l]
        if lines:
            print(f"  {cmd[:30]}:")
            for l in lines[:5]:
                print(f"    {l}")

    # ── Get device SN from WAP CLI for verification ───────────────────────
    print("\n[*] Getting SN via WAP CLI...")
    run(chan, "exit")
    recv_until(chan, "SU_WAP>", timeout=5)
    chan.send("display sn\n")
    out = recv_until(chan, "SU_WAP>", timeout=8)
    print(out.strip()[-200:])
    
    chan.send("display boardinfo\n")
    out = recv_until(chan, ["SU_WAP>", "success"], timeout=15)
    print(out.strip()[-1000:])

    client.close()
    print("\n[*] Done.")

if __name__ == "__main__":
    main()
