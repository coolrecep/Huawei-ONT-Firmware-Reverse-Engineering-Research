#!/usr/bin/env python3
"""
FINAL: Both hexdump -C and busybox base64 WORK!
Use busybox base64 to download the full ssmp binary,
then scan locally for the 32-byte ALPHA table.

Strategy:
1. base64 encode the ssmp .rodata section (or full binary) on the device
2. Read the output over SSH in chunks
3. Decode and scan locally
"""

import paramiko, time, struct, zlib, base64

HOST     = "192.168.1.1"
USER     = "sUser"
PASSWORD = "EP!99R4HLH9E"

P1   = "EP!99R4HLH9E"
SN1  = "485754437C07DEA5"

CHECKS_32 = [
    (1,57),(2,72),(3,82),(4,69),(7,57),(10,33),(11,80),
    (15,52),(18,72),(19,69),(22,76),(30,57)
]

def recv_until(chan, markers, timeout=30):
    if isinstance(markers, str): markers = [markers]
    buf = b""
    start = time.time()
    while time.time() - start < timeout:
        if chan.recv_ready():
            buf += chan.recv(16384)
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

def scan_for_table(data):
    """Scan binary data for 32-byte ALPHA table."""
    best_score = 0
    best_off = -1
    results = []
    
    for offset in range(len(data) - 32):
        b = data[offset:offset+32]
        score = sum(1 for idx, val in CHECKS_32 if b[idx] == val)
        if score > best_score:
            best_score = score
            best_off = offset
        if score >= 7:
            results.append((score, offset, bytes(b)))
    
    return best_score, best_off, results

def verify_table(alpha_bytes):
    """Verify the 32-byte table against P1."""
    sn = bytes.fromhex(SN1)
    crc = zlib.crc32(sn) & 0xFFFFFFFF
    ext = list(sn) + list(struct.pack('>I', crc))
    result = ''.join(chr(alpha_bytes[(b>>1)%32]) if 32<=alpha_bytes[(b>>1)%32]<127 else '?' 
                     for b in ext)
    return result, result == P1

def main():
    print("=" * 62)
    print("  Downloading ssmp via busybox base64")
    print("=" * 62)

    client, chan = connect()
    print("[+] Shell ready\n")

    # ── Step 1: Ensure /tmp/ss exists ────────────────────────────────────
    out = run(chan, "ls -la /tmp/ss 2>&1 || (cp /bin/ssmp /tmp/ss 2>&1 && ls -la /tmp/ss)")
    print(f"[*] ssmp copy: {out.strip()[-150:]}")

    # ── Step 2: Encode just the .rodata section ───────────────────────────
    # .rodata: file offset 290564, size 39504 bytes
    RODATA_OFF  = 290564
    RODATA_SIZE = 39504
    
    print(f"\n[*] Encoding .rodata section ({RODATA_SIZE} bytes at offset {RODATA_OFF})...")
    
    # Extract .rodata to /tmp/rodata.bin
    cmd = f"dd if=/tmp/ss bs=1 skip={RODATA_OFF} count={RODATA_SIZE} 2>/dev/null > /tmp/rodata.bin && wc -c /tmp/rodata.bin"
    out = run(chan, cmd, timeout=30)
    print(f"  rodata.bin: {out.strip()[-100:]}")
    
    # ── Step 3: Base64 encode rodata ─────────────────────────────────────
    print("\n[*] Base64 encoding .rodata...")
    out = run(chan, "busybox base64 /tmp/rodata.bin > /tmp/rodata.b64 && wc -c /tmp/rodata.b64 && echo B64_DONE", timeout=30)
    print(f"  b64 size: {out.strip()[-150:]}")
    
    if "B64_DONE" not in out:
        print("  [!] base64 failed, trying with cat pipe...")
        out = run(chan, "cat /tmp/rodata.bin | busybox base64 > /tmp/rodata.b64 && wc -c /tmp/rodata.b64 && echo B64_DONE", timeout=30)
        print(f"  b64 size: {out.strip()[-150:]}")

    # Get b64 file size
    out2 = run(chan, "wc -c /tmp/rodata.b64")
    b64_size = 0
    for l in out2.split('\n'):
        parts = l.strip().split()
        if parts and parts[0].isdigit():
            b64_size = int(parts[0]); break
    print(f"  B64 file size: {b64_size}")

    # ── Step 4: Read b64 data via hexdump (which works!) ─────────────────
    # hexdump -C works, but it outputs slow. Better: read the b64 text directly.
    print(f"\n[*] Reading {b64_size} bytes of base64 data via cat...")
    
    # Since base64 output is text (ASCII), we can cat it directly!
    b64_chunks = []
    CHUNK = 10000  # lines per read
    
    # Use head/tail to read in pieces, or just cat it all
    # For a 39504-byte file, base64 = ~52672 chars = manageable
    chan.send("cat /tmp/rodata.b64\n")
    
    b64_data = ""
    sentinel = "END_B64_DATA"
    # Wait for end of output + prompt
    buf = ""
    print("  Collecting base64 data...")
    start = time.time()
    
    while time.time() - start < 120:
        if chan.recv_ready():
            chunk = chan.recv(16384).decode('utf-8', errors='replace')
            buf += chunk
            # Check if we got the prompt back
            if "# " in buf[-100:] or "WAP" in buf[-50:]:
                break
        else:
            time.sleep(0.2)
    
    print(f"  Received {len(buf)} chars")
    
    # Extract valid base64 chars from the output
    # Filter out the command echo (first line) and the prompt (last line)
    lines = buf.split('\n')
    b64_lines = []
    for line in lines:
        line = line.strip().replace('\r', '')
        # Skip command echo and prompt
        if 'cat /tmp' in line or 'WAP(Dopra' in line or '# ' in line:
            continue
        # Keep only lines with valid base64 chars
        clean = ''.join(c for c in line if c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
        if clean:
            b64_lines.append(clean)
    
    b64_string = ''.join(b64_lines)
    print(f"  Valid base64 chars: {len(b64_string)}")
    
    # ── Step 5: Decode and scan ───────────────────────────────────────────
    if len(b64_string) > 1000:
        # Pad
        pad = 4 - (len(b64_string) % 4)
        if pad != 4: b64_string += '=' * pad
        
        try:
            rodata_bytes = base64.b64decode(b64_string)
            print(f"  [+] Decoded {len(rodata_bytes)} bytes of .rodata")
            
            with open('/tmp/ssmp_rodata_router.bin', 'wb') as f:
                f.write(rodata_bytes)
            print("  Saved to /tmp/ssmp_rodata_router.bin")
            
            # Scan for table
            print(f"\n[*] Scanning {len(rodata_bytes)} bytes for 32-byte ALPHA table...")
            best_score, best_off, results = scan_for_table(rodata_bytes)
            
            if results:
                print(f"\n  Results (score >= 7):")
                for score, off, b in sorted(results, reverse=True)[:10]:
                    asc = ''.join(chr(x) if 32<=x<127 else '.' for x in b)
                    hex_s = ' '.join(f'{x:02x}' for x in b)
                    print(f"\n  SCORE {score}/12 at .rodata+{off} (file offset {RODATA_OFF+off}):")
                    print(f"    HEX: {hex_s}")
                    print(f"    ASC: {asc}")
                    
                    if score >= 11:
                        # Try verification
                        result, match = verify_table(b)
                        print(f"    Verification: {result} {'✓ MATCH!' if match else '✗'}")
            else:
                print(f"  Best: {best_score}/12 at offset {best_off}")
                if best_off >= 0:
                    b = rodata_bytes[best_off:best_off+32]
                    print(f"  HEX: {' '.join(f'{x:02x}' for x in b)}")
        
        except Exception as e:
            print(f"  [!] Decode error: {e}")
            print(f"  First 100 chars of b64: {b64_string[:100]}")
    else:
        print(f"  [!] Not enough base64 data ({len(b64_string)} chars)")

    # ── Step 6: Also try hexdump approach for a targeted range ───────────
    print("\n[*] Using hexdump to scan for specific byte patterns...")
    # hexdump -v -e '1/1 "%02x"' shows each byte as 2 hex chars
    # Search for the pattern: positions 1=39, 2=48, 3=52, 4=45
    # i.e., byte sequence: (anything)(39)(48)(52)(45)... at the right offsets
    
    cmd = f"hexdump -v -e '1/1 \"%02x\"' /tmp/rodata.bin | grep -oE '.{{0,8}}3948524.{{0,60}}' | head -5"
    out = run(chan, cmd, timeout=15)
    print(f"  Hexdump pattern search: {out.strip()[-200:]}")
    
    # Also: try direct hexdump with offset search
    # Look for "39 48 52 45" in hexdump -C format
    cmd2 = f"hexdump -C /tmp/rodata.bin | grep -i '39 48 52 45' | head -10"
    out2 = run(chan, cmd2, timeout=15)
    print(f"  Hexdump -C grep: {out2.strip()[-300:]}")

    # ── Step 7: Display specific bytes at our target table offsets ────────
    # If we know the exact 12 byte positions that MUST match,
    # let's verify our hypothesis by reading SPECIFIC bytes from the file
    # using hexdump with skip and count
    
    print("\n[*] Verifying ALPHA formula by checking specific bytes in .rodata...")
    # Our ALPHA formula: ALPHA[(byte>>1)%32] = char
    # For SN byte 0x07 (=7): (7>>1)%32 = 3 → ALPHA[3] should = 'R'(82=0x52)
    # If ALPHA is at some offset X in rodata, then rodata[X+3] = 0x52
    
    # Let's search hexdump for any occurrence of 0x52 at relative position 3
    # i.e., find sequences where 4th byte is 0x52
    # That's too broad. Let's be more specific.
    
    # Check: does hexdump -C show our known pattern?
    # The 12 positions in order: 1,2,3,4,7,10,11,15,18,19,22,30
    # as hex: 39,48,52,45,39,21,50,34,48,45,4C,39
    
    # If the table starts at .rodata[X]:
    # rodata[X+1]=0x39, [X+2]=0x48, [X+3]=0x52, [X+4]=0x45
    # This 4-byte sequence at X+1..X+4: "9HRE"
    print("  Searching for '9HRE' (39 48 52 45) in hexdump output...")
    cmd3 = "hexdump -C /tmp/rodata.bin | grep -A1 -B1 '39 48 52 45' | head -20"
    out3 = run(chan, cmd3, timeout=15)
    print(f"  Result:\n{out3.strip()[-500:]}")

    client.close()
    print("\n[*] Done.")

if __name__ == "__main__":
    main()
