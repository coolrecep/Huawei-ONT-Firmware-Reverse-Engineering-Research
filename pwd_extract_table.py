#!/usr/bin/env python3
"""
Extract the password lookup table from /bin/ssmp on the router.
We're looking for a 128-byte or 256-byte block in .rodata that contains
the password character set.

Strategy:
1. Connect to router, download /bin/ssmp
2. Search for the lookup table using known entries as anchor
3. Validate against both passwords
"""

import paramiko, time, zlib, struct

HOST     = "192.168.1.1"
USER     = "sUser"
PASSWORD = "EP!99R4HLH9E"

P1   = "EP!99R4HLH9E"
SN1  = "485754437C07DEA5"
P2   = "Y7.15R1TLU6?"

# Known TABLE entries (index = byte >> 1):
KNOWN_TABLE = {
    3:  'R',
    7:  '9',
    19: 'E',
    33: '9',
    36: 'E',
    42: '!',
    43: 'P',
    54: 'L',
    62: '9',
    82: 'H',
    98: 'H',
   111: '4',
}

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

def send_cmd(chan, cmd, timeout=15):
    chan.send(cmd + "\n")
    out = recv_until(chan, ["# "], timeout)
    return out

def connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10,
                   look_for_keys=False, allow_agent=False)
    chan = client.invoke_shell(width=220, height=50)
    time.sleep(2)
    out = recv_until(chan, ["WAP>", "Remove one session", "Enter the ID"], timeout=8)
    if "Remove one session" in out or "Enter the ID" in out:
        chan.send("1\n"); time.sleep(2); recv_until(chan, "WAP>", timeout=10)
    chan.send("su\n"); recv_until(chan, ["SU_WAP>"], timeout=8)
    chan.send("shell\n"); recv_until(chan, "# ", timeout=8)
    return client, chan

def search_table_in_binary():
    """Search for the character lookup table in /bin/ssmp."""
    print("=" * 60)
    print("Extracting password lookup table from /bin/ssmp")
    print("=" * 60)
    
    client, chan = connect()
    print("[+] Connected\n")
    
    # First: look for the known chars in binary data near 'EP!99R4HLH9E'
    # The table might be nearby in .rodata
    # Known chars we've seen: ! # 4 9 E H L P R
    # TABLE values we know:
    # INDEX 3  → 'R'  (0x52)
    # INDEX 7  → '9'  (0x39)
    # INDEX 19 → 'E'  (0x45)
    # INDEX 33 → '9'  
    # INDEX 36 → 'E'
    # INDEX 42 → '!'  (0x21)
    # INDEX 43 → 'P'  (0x50)
    # INDEX 54 → 'L'  (0x4C)
    # INDEX 62 → '9'
    # INDEX 82 → 'H'  (0x48)
    # INDEX 98 → 'H'
    # INDEX 111 → '4' (0x34)
    
    print("[*] Method 1: Search for known table byte sequence in ssmp binary")
    # The partial table bytes at known indices:
    # If table is 128 bytes: look for a pattern that matches at those positions
    # KEY PATTERN: table[42]='!' table[43]='P' → bytes at offset 42,43 = 0x21, 0x50
    # That's "!P" which is a 2-byte pattern at consecutive positions
    print("Searching for '!P' pattern (table[42]='!' table[43]='P') in /bin/ssmp:")
    send_cmd(chan, "od -c /bin/ssmp 2>/dev/null | head -5", timeout=5)
    
    # Search via grep for the byte sequence
    send_cmd(chan, "grep -c '' /bin/ssmp 2>&1 | head -1")  # just check if readable
    
    # Use xxd or od to find the table
    print("\n[*] Searching for pattern 0x21 0x50 (excl-P adjacent in table):")
    chan.send("xxd /bin/ssmp 2>/dev/null | grep '2150' | head -20\n")
    out = recv_until(chan, "# ", timeout=15)
    lines = [l for l in out.strip().split('\n') if '2150' in l and '#' not in l]
    for l in lines[:10]:
        print(f"  {l.strip()}")

    # Alternative: search with awk for the sequence
    print("\n[*] Searching for extended pattern around known table values:")
    # TABLE bytes we know (at known positions in a 128-byte block):
    # pos 3=0x52, pos 7=0x39, pos 19=0x45, pos 33=0x39, pos 36=0x45,
    # pos 42=0x21, pos 43=0x50, pos 54=0x4C, pos 62=0x39, pos 82=0x48
    # Look for: 0x52 at offset+3, 0x39 at offset+7 relative to block start
    
    # Method: dump binary and scan in Python on router? No python.
    # Use od/xxd and scan
    
    print("\n[*] Dumping /bin/ssmp .rodata section (looking for char tables):")
    # Look for readable char blocks that contain our known chars
    # The table should have consecutive ASCII printable chars at known positions
    
    # Try: find 128-byte blocks where position 42=0x21, 43=0x50
    cmd = r"""
offset=0
found=0
while [ $offset -lt $(wc -c < /bin/ssmp) ] && [ $found -eq 0 ]; do
    b42=$(dd if=/bin/ssmp bs=1 skip=$((offset+42)) count=1 2>/dev/null | od -An -tx1 | tr -d ' ')
    b43=$(dd if=/bin/ssmp bs=1 skip=$((offset+43)) count=1 2>/dev/null | od -An -tx1 | tr -d ' ')
    if [ "$b42" = "21" ] && [ "$b43" = "50" ]; then
        echo "Found at offset $offset!"
        dd if=/bin/ssmp bs=1 skip=$offset count=128 2>/dev/null | od -An -tx1
        found=1
    fi
    offset=$((offset+1))
done
echo "Scan complete"
""".strip()
    print("  (This scan may take a while...)")
    # That's too slow. Use a smarter approach.
    
    # Better: use xxd to get hex, then parse in shell
    print("\n[*] Using xxd + awk to find the table:")
    chan.send("xxd -p /bin/ssmp 2>/dev/null | tr -d '\\n' > /tmp/ssmp_hex.txt && wc -c /tmp/ssmp_hex.txt\n")
    out = recv_until(chan, "# ", timeout=30)
    print(f"  xxd output: {out.strip()[-100:]}")
    
    # Search for "2150" (0x21 0x50 = "!P") at positions 42,43 of a 128-byte block
    print("\n[*] Searching for 2150 followed by known chars:")
    # In hex string, 128 bytes = 256 hex chars
    # Position 42 in block = offset 84 in hex string
    # Position 43 = offset 86 in hex string
    # Pattern at pos 42-43: "2150"
    # Relative to block start: search for offset where hex[84:88]=="2150"
    cmd2 = r"""
python3 -c "
import sys
data = open('/tmp/ssmp_hex.txt').read().strip()
# Search for '2150' (bytes 0x21, 0x50)
i = 0
while i < len(data)-4:
    pos = data.find('2150', i)
    if pos < 0: break
    # pos in hex string → byte offset
    byte_off = pos // 2
    # if this is byte offset 42 within a 128-byte block:
    block_off = byte_off - 42
    if block_off >= 0 and block_off % 4 == 0:  # aligned
        # Extract 128 bytes at block_off
        hex_block = data[block_off*2 : (block_off+128)*2]
        if len(hex_block) == 256:
            block = bytes.fromhex(hex_block)
            # Verify other known positions
            if chr(block[3])=='R' and chr(block[7])=='9' and chr(block[54])=='L':
                print(f'MATCH at byte offset {block_off}!')
                print(f'Table: {[chr(b) if 32<=b<127 else \"?\" for b in block]}')
    i = pos + 2
print('Scan done')
" 2>&1 | head -30
"""
    chan.send(cmd2.strip() + "\n")
    out = recv_until(chan, ["# "], timeout=60)
    lines = out.strip().split('\n')
    for l in lines:
        if 'MATCH' in l or 'Table' in l or 'Scan' in l or 'Error' in l:
            print(f"  {l.strip()}")
    
    # Alternative: try alignment 0, 1, 2, 3
    cmd3 = r"""
python3 -c "
data = open('/tmp/ssmp_hex.txt').read().strip()
raw = bytes.fromhex(data)
# Slide a 128-byte window
for offset in range(len(raw)-128):
    b = raw[offset:offset+128]
    # Check known positions
    if (b[3]==82 and   # 'R'
        b[7]==57 and   # '9'
        b[19]==69 and  # 'E'
        b[42]==33 and  # '!'
        b[43]==80 and  # 'P'
        b[54]==76 and  # 'L'
        b[82]==72):    # 'H'
        print(f'FOUND TABLE at offset {offset}!')
        print(bytes(b))
        print([chr(x) if 32<=x<127 else '.' for x in b])
" 2>&1 | head -10
"""
    chan.send(cmd3.strip() + "\n")
    out = recv_until(chan, ["# "], timeout=120)
    for l in out.strip().split('\n'):
        if 'FOUND' in l or 'offset' in l.lower() or 'Error' in l or 'Table' in l:
            print(f"  {l.strip()}")
    
    client.close()
    print("\n[*] Done")

if __name__ == "__main__":
    search_table_in_binary()
    
    # Also: verify the algorithm with P2 new chars:
    print("\n=== Using P2 to expand the TABLE ===")
    print("P2 chars at positions where we already know the TABLE entry:")
    sn1 = bytes.fromhex(SN1)
    crc = zlib.crc32(sn1) & 0xFFFFFFFF
    ext = list(sn1) + list(struct.pack('>I', crc))
    
    print(f"\nFull P1 derivation:")
    for i, (b, c) in enumerate(zip(ext, P1)):
        idx = b >> 1
        print(f"  byte={b:3d}(0x{b:02X}) >> 1 = {idx:3d} → TABLE[{idx}]='{c}' ✓")
    
    print(f"\nP2 tells us:")
    print("  P2[5]='R' → SN2[5] must have SN2[5]>>1 = 3 → SN2[5] ∈ {6,7}")
    print("  P2[8]='L' → CRC2[0]>>1 = 54 → CRC2[0] ∈ {108,109}")
    print("  All other P2 chars are NEW → fill in more TABLE entries once we know SN2")
