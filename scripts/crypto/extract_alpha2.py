#!/usr/bin/env python3
"""
Approach 2: Use od/dd on device to extract ssmp bytes and scan locally.
Since python3 is not on device, we:
1. Use od -An -tx1 to get hex dump of /bin/ssmp
2. Read it in chunks via SSH
3. Scan locally for the 32-byte ALPHA table
"""

import paramiko, time, struct, zlib

HOST     = "192.168.1.1"
USER     = "sUser"
PASSWORD = "EP!99R4HLH9E"

CHECKS_32 = [
    (1,57),(2,72),(3,82),(4,69),(7,57),(10,33),(11,80),
    (15,52),(18,72),(19,69),(22,76),(30,57)
]

def recv_until(chan, markers, timeout=10):
    if isinstance(markers, str): markers = [markers]
    buf = b""
    start = time.time()
    while time.time() - start < timeout:
        if chan.recv_ready():
            buf += chan.recv(4096)
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
        print("[!] Removing old session...")
        chan.send("1\n"); time.sleep(2); recv_until(chan, "WAP>", timeout=10)
    chan.send("su\n");    recv_until(chan, ["SU_WAP>"], timeout=8)
    chan.send("shell\n"); recv_until(chan, "# ", timeout=8)
    print("[+] Shell ready")
    return client, chan

def run(chan, cmd, timeout=30):
    chan.send(cmd + "\n")
    return recv_until(chan, "# ", timeout)

def main():
    print("=" * 62)
    print("  Extract 32-byte ALPHA via od dump + local scan")
    print("=" * 62)

    client, chan = connect()

    # ── Step 1: Get file size ─────────────────────────────────────────────
    print("\n[*] Getting ssmp size...")
    out = run(chan, "ls -la /bin/ssmp")
    print(out.strip()[-200:])
    
    # Alternative size detection
    out = run(chan, "stat /bin/ssmp 2>&1 | head -5")
    print(out.strip()[-200:])

    # ── Step 2: Convert to base64 using busybox utilities ─────────────────
    # Try uuencode if available (often in busybox)
    print("\n[*] Checking available encoding tools...")
    for tool in ["base64", "uuencode", "xxd", "hexdump", "od"]:
        out = run(chan, f"which {tool} 2>/dev/null || echo NO_{tool.upper()}")
        result = [l.strip() for l in out.split('\n') if tool in l.lower() or 'NO_' in l]
        if result:
            print(f"  {tool}: {result[0]}")

    # ── Step 3: Use od to dump binary as octal/hex ───────────────────────
    print("\n[*] Dumping /bin/ssmp via od -An -tx1 to /tmp/ssmp.hex ...")
    run(chan, "od -An -tx1 /bin/ssmp > /tmp/ssmp.hex 2>&1; echo DONE", timeout=60)
    out = run(chan, "wc -c /tmp/ssmp.hex")
    print(f"  Hex dump size: {out.strip()[-100:]}")
    
    # ── Step 4: Read hex dump via dd chunks ──────────────────────────────
    print("\n[*] Reading hex dump in chunks...")
    
    # Get total size first
    out = run(chan, "wc -c /tmp/ssmp.hex 2>&1")
    hex_size = 0
    for l in out.split('\n'):
        parts = l.strip().split()
        if parts and parts[0].isdigit():
            hex_size = int(parts[0])
            break
    print(f"  Hex file size: {hex_size} chars")

    if hex_size == 0:
        print("  [!] od dump failed or file empty, trying alternative...")
        # Try: copy ssmp to /tmp first (bypass read permission issue?)
        run(chan, "cp /bin/ssmp /tmp/ssmp_copy 2>&1 && echo CP_OK")
        out = run(chan, "wc -c /tmp/ssmp_copy 2>&1")
        print(f"  Copy: {out.strip()[-100:]}")
        run(chan, "od -An -tx1 /tmp/ssmp_copy > /tmp/ssmp.hex 2>&1; wc -c /tmp/ssmp.hex")
        out = run(chan, "wc -c /tmp/ssmp.hex")
        for l in out.split('\n'):
            parts = l.strip().split()
            if parts and parts[0].isdigit():
                hex_size = int(parts[0])
                break
        print(f"  After copy, hex size: {hex_size}")

    if hex_size == 0:
        print("  [!] Cannot read ssmp binary. Trying direct memory approach...")
        # Try reading from /proc/ssmp/exe (PID 1650)
        out = run(chan, "ls -la /proc/1650/exe 2>&1")
        print(f"  ssmp exe link: {out.strip()[-100:]}")
        out = run(chan, "od -An -tx1 /proc/1650/exe 2>&1 | head -5")
        print(f"  proc exe: {out.strip()[-200:]}")
        return

    # ── Step 5: Read hex dump in chunks via the terminal ─────────────────
    CHUNK = 3000   # hex chars per read
    hex_data_full = ""
    pos = 0
    print(f"\n[*] Reading {hex_size} hex chars in chunks of {CHUNK}...")
    
    while pos < hex_size:
        cmd = f"dd if=/tmp/ssmp.hex bs=1 skip={pos} count={CHUNK} 2>/dev/null"
        chan.send(cmd + "\n")
        time.sleep(0.5)
        # Collect until we see the shell prompt
        buf = b""
        start = time.time()
        while time.time() - start < 10:
            if chan.recv_ready():
                buf += chan.recv(4096)
                if b"# " in buf[-20:]:
                    break
            else:
                time.sleep(0.1)
        
        raw = buf.decode('utf-8', errors='replace')
        # Filter: keep only hex chars (0-9 a-f space newline)
        hex_chunk = ""
        for line in raw.split('\n'):
            line = line.strip().replace('\r', '')
            # Skip the command echo and the prompt
            if 'dd if=' in line or 'WAP' in line or '# ' in line:
                continue
            # Keep hex chars
            hex_chunk += ''.join(c for c in line if c in '0123456789abcdefABCDEF \t\n')
        
        hex_data_full += hex_chunk
        pos += CHUNK
        
        # Progress
        if pos % 30000 == 0 or pos >= hex_size:
            print(f"  Read {pos}/{hex_size} chars, collected {len(hex_data_full)} hex chars")

    print(f"\n[+] Total hex chars collected: {len(hex_data_full)}")

    # ── Step 6: Parse hex dump to bytes ──────────────────────────────────
    print("[*] Parsing hex to bytes...")
    hex_tokens = hex_data_full.split()
    hex_tokens = [t for t in hex_tokens if len(t) == 2 and all(c in '0123456789abcdefABCDEF' for c in t)]
    print(f"  Valid hex tokens: {len(hex_tokens)}")
    
    try:
        binary_data = bytes([int(t, 16) for t in hex_tokens])
        print(f"  Binary size reconstructed: {len(binary_data)} bytes")
        
        # Save it
        with open('/tmp/ssmp_router.bin', 'wb') as f:
            f.write(binary_data)
        print("  Saved to /tmp/ssmp_router.bin")

    except Exception as e:
        print(f"  [!] Parse error: {e}")
        # Try with fallback
        binary_data = b""

    # ── Step 7: Scan the reconstructed binary ─────────────────────────────
    if binary_data and len(binary_data) > 1000:
        print(f"\n[*] Scanning {len(binary_data)} bytes for 32-byte ALPHA table...")
        best_score = 0
        best_off = -1
        
        for offset in range(len(binary_data) - 32):
            b = binary_data[offset:offset+32]
            score = sum(1 for idx, val in CHECKS_32 if b[idx] == val)
            if score > best_score:
                best_score = score
                best_off = offset
            if score >= 9:
                asc = ''.join(chr(x) if 32<=x<127 else '.' for x in b)
                hex_s = ' '.join(f'{x:02x}' for x in b)
                print(f"\n  [+] SCORE {score}/12 at offset {offset} (0x{offset:x}):")
                print(f"      HEX: {hex_s}")
                print(f"      ASC: {asc}")
                print(f"      LIST: {list(b)}")
        
        print(f"\n  Best score: {best_score}/12 at offset {best_off} (0x{best_off:x})")
        if best_off >= 0:
            b = binary_data[best_off:best_off+32]
            hex_s = ' '.join(f'{x:02x}' for x in b)
            asc = ''.join(chr(x) if 32<=x<127 else '.' for x in b)
            print(f"  HEX: {hex_s}")
            print(f"  ASC: {asc}")
    else:
        print("\n[!] Binary too small or empty, cannot scan.")

    client.close()
    print("\n[*] Done.")

if __name__ == "__main__":
    main()
