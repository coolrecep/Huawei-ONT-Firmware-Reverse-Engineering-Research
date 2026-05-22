#!/usr/bin/env python3
"""
od is not available. Use busybox alternatives:
- busybox hexdump or xxd
- awk with printf for manual hex conversion
- base64 encoding via busybox

Key: cp succeeded! ssmp_copy is in /tmp as srv_clid-owned.
Size confirmed: 358092 bytes (same as local).

Let's use busybox base64 OR busybox hexdump.
"""

import paramiko, time, struct, zlib, base64, io

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
    print("  hexdump / base64 approach for ssmp binary")
    print("=" * 62)

    client, chan = connect()
    print("[+] Shell ready\n")

    # ── First: make a copy of ssmp ─────────────────────────────────────────
    run(chan, "cp /bin/ssmp /tmp/ss 2>&1 && echo CP_OK")
    out = run(chan, "ls -la /tmp/ss 2>&1")
    print(f"[*] ssmp copy: {out.strip()[-100:]}")

    # ── Check what busybox tools are available ─────────────────────────────
    print("\n[*] Checking busybox applets...")
    out = run(chan, "busybox --list 2>/dev/null | grep -E 'hexdump|base64|xxd|od|xxencode|uuencode' | tr '\\n' ' '")
    print(f"  Available: {out.strip()[-200:]}")

    # ── Try busybox base64 ───────────────────────────────────────────────
    print("\n[*] Trying busybox base64 on ssmp copy...")
    out = run(chan, "busybox base64 /tmp/ss 2>/dev/null | head -5 && echo B64_OK")
    if "B64_OK" in out:
        print("  busybox base64 works!")
    else:
        print(f"  base64 result: {out.strip()[-100:]}")

    # ── Try hexdump ───────────────────────────────────────────────────────
    print("\n[*] Trying hexdump...")
    out = run(chan, "hexdump -C /tmp/ss 2>/dev/null | head -5 && echo HEX_OK")
    if "HEX_OK" in out:
        print("  hexdump -C works!")
    else:
        out = run(chan, "hexdump -v /tmp/ss 2>/dev/null | head -5 && echo HEX_OK")
        if "HEX_OK" in out:
            print("  hexdump -v works!")
        else:
            print(f"  hexdump result: {out.strip()[-100:]}")

    # ── Try the awk trick for hex dump ────────────────────────────────────
    print("\n[*] Trying awk-based hex dump of first 64 bytes...")
    # Use dd to get raw bytes, then use awk to convert each byte to hex
    # This uses the "read raw byte as octal via printf" trick
    awk_hex = r"""dd if=/tmp/ss bs=1 count=64 2>/dev/null | awk 'BEGIN{OFMT="%.0f"} {for(i=1;i<=length($0);i++){printf "%02x ",ord(substr($0,i,1))}; print ""}' """
    # That won't work since awk doesn't have ord(). Try another way:
    # Use od from /usr/sbin or find it elsewhere
    out = run(chan, "find / -name od -type f 2>/dev/null | head -5", timeout=15)
    print(f"  od locations: {out.strip()[-200:]}")
    
    out = run(chan, "find / -name hexdump -type f 2>/dev/null | head -5", timeout=15)
    print(f"  hexdump locations: {out.strip()[-200:]}")
    
    out = run(chan, "find / -name xxd -type f 2>/dev/null | head -5", timeout=15)
    print(f"  xxd locations: {out.strip()[-200:]}")
    
    out = run(chan, "find / -name base64 -type f 2>/dev/null | head -5", timeout=15)
    print(f"  base64 locations: {out.strip()[-200:]}")

    # ── Use printf to hex-dump via shell loop ─────────────────────────────
    print("\n[*] Trying shell-based hex dump (slow but reliable)...")
    # This approach: read specific bytes using dd, then use printf to show hex
    # Read the .rodata section (offset 290564) in 256-byte chunks
    
    # First: test with just 32 bytes at a known location
    cmd = "dd if=/tmp/ss bs=1 skip=290564 count=32 2>/dev/null | cat -v | head -2"
    out = run(chan, cmd, timeout=10)
    print(f"  cat -v test: {out.strip()[-200:]}")

    # ── Use the uuencode approach if available ─────────────────────────────
    print("\n[*] Trying uuencode...")
    out = run(chan, "dd if=/tmp/ss bs=1 skip=290564 count=256 2>/dev/null | uuencode - 2>/dev/null | head -5 && echo UU_OK")
    if "UU_OK" in out or "begin" in out:
        print("  uuencode works!")
        # Get the full .rodata section
    else:
        print(f"  uuencode: {out.strip()[-100:]}")

    # ── BEST APPROACH: Use awk with printf %d for each char ───────────────
    # The trick: pipe binary through 'awk' using gsub on each char
    # BusyBox awk supports printf with decimal/hex conversions
    print("\n[*] Trying awk printf hex conversion...")
    awk_cmd = r"""dd if=/tmp/ss bs=1 skip=290564 count=32 2>/dev/null | while IFS= read -r -d '' -n1 c; do printf '%02x' "'$c"; done; echo"""
    out = run(chan, awk_cmd, timeout=15)
    print(f"  awk hex output: {out.strip()[-200:]}")
    
    # ── Alternative: read using /dev/mem trick via dd ─────────────────────
    # Actually the simplest busybox-compatible approach:
    # Use `cat` and pipe to a hex-encoding program
    
    # Check if nc/netcat is available to exfiltrate binary
    print("\n[*] Checking for nc/netcat...")
    out = run(chan, "which nc netcat ncat 2>/dev/null && echo NC_OK")
    print(f"  nc: {out.strip()[-100:]}")

    # ── Try the while-read loop for hex dump ──────────────────────────────
    print("\n[*] Shell while-read loop hex dump of first 32 bytes of .rodata...")
    # Trick: use IFS= read -n1 and printf '%02X' to get hex
    cmd = """dd if=/tmp/ss bs=1 skip=290564 count=32 2>/dev/null > /tmp/chunk.bin; ls -la /tmp/chunk.bin"""
    out = run(chan, cmd, timeout=10)
    print(f"  chunk.bin: {out.strip()[-100:]}")
    
    # Now hexdump the chunk
    cmd2 = "while IFS= read -r -d '' -n1 c; do printf '%02x' \"'$c\"; done < /tmp/chunk.bin; echo"
    out = run(chan, cmd2, timeout=15)
    hex_output = out.strip().replace('\r', '').replace('\n', '')
    # Filter to hex chars only
    hex_clean = ''.join(c for c in hex_output if c in '0123456789abcdefABCDEF')
    print(f"  Hex output ({len(hex_clean)} chars): {hex_clean}")
    
    if len(hex_clean) >= 32:
        chunk_bytes = bytes([int(hex_clean[i:i+2],16) for i in range(0,len(hex_clean),2) if i+1 < len(hex_clean)])
        print(f"  Bytes ({len(chunk_bytes)}): {list(chunk_bytes[:32])}")
        print(f"  ASCII: {''.join(chr(b) if 32<=b<127 else '.' for b in chunk_bytes[:32])}")
    
    # ── The BIG attempt: read the full rodata via the while loop ──────────
    # This will be VERY slow but accurate
    # rodata: offset=290564, size=39504
    # Let's target just the area where the table might be
    
    # Actually - since we know the local binary is IDENTICAL to the router binary
    # (same MD5), the table MUST be in the local binary.
    # Our search just hasn't been thorough enough.
    
    # Let me try reading the FULL binary from router via shell loop
    # The key: our local binary is identical, so if the table is not found
    # in the local binary via static scan, it's DYNAMICALLY CONSTRUCTED.
    
    print("\n[*] Attempting full binary download via 256-byte chunks...")
    RODATA_OFFSET = 290564
    RODATA_SIZE   = 39504
    
    # Read in 256-byte chunks
    all_hex = ""
    chunk = 256
    
    for skip in range(RODATA_OFFSET, RODATA_OFFSET + min(RODATA_SIZE, 4096), chunk):
        cmd = f"dd if=/tmp/ss bs=1 skip={skip} count={chunk} 2>/dev/null > /tmp/c.bin"
        run(chan, cmd, timeout=10)
        
        cmd2 = r"""while IFS= read -r -d '' -n1 c; do printf '%02x' "'$c"; done < /tmp/c.bin"""
        chan.send(cmd2 + "\n")
        out = recv_until(chan, "# ", timeout=30)
        
        # Extract hex
        hex_part = ''.join(c for c in out if c in '0123456789abcdefABCDEF')
        # Remove the command echo
        if len(hex_part) > 64:
            all_hex += hex_part
        
        if skip == RODATA_OFFSET:
            print(f"  First chunk ({skip}): {len(hex_part)} hex chars")
            if hex_part:
                sample = bytes([int(hex_part[i:i+2],16) for i in range(0,min(32,len(hex_part)),2)])
                print(f"  Sample: {' '.join(f'{b:02x}' for b in sample)}")
                print(f"  ASCII:  {''.join(chr(b) if 32<=b<127 else '.' for b in sample)}")

    print(f"\n[+] Total hex chars: {len(all_hex)}")
    if all_hex:
        binary_chunk = bytes([int(all_hex[i:i+2],16) for i in range(0,len(all_hex)-1,2)])
        print(f"  Binary size: {len(binary_chunk)} bytes")
        
        # Scan for the 32-byte table
        for offset in range(len(binary_chunk)-32):
            b = binary_chunk[offset:offset+32]
            score = sum(1 for idx,val in CHECKS_32 if b[idx]==val)
            if score >= 8:
                print(f"\n  *** SCORE {score}/12 at offset {offset} ***")
                print(f"  HEX: {' '.join(f'{x:02x}' for x in b)}")
                print(f"  ASC: {''.join(chr(x) if 32<=x<127 else '.' for x in b)}")

    client.close()
    print("\n[*] Done.")

if __name__ == "__main__":
    main()
