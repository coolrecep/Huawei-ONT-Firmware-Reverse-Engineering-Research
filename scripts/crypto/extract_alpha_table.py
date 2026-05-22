#!/usr/bin/env python3
"""
Connect to router SSH, run a scan on /bin/ssmp to find the 32-byte ALPHA table.

Known ALPHA entries (index = (byte>>1) % 32):
  [1]=9, [2]=H, [3]=R, [4]=E, [7]=9, [10]=!, [11]=P,
  [15]=4, [18]=H, [19]=E, [22]=L, [30]=9

We look for any 32-byte window in /bin/ssmp where these positions hold.
"""

import paramiko, time, zlib, struct

HOST     = "192.168.1.1"
USER     = "sUser"
PASSWORD = "EP!99R4HLH9E"

# Confirmed partial ALPHA table (as ASCII values):
CHECKS_32 = [
    (1, 57),   # '9'
    (2, 72),   # 'H'
    (3, 82),   # 'R'
    (4, 69),   # 'E'
    (7, 57),   # '9'
    (10, 33),  # '!'
    (11, 80),  # 'P'
    (15, 52),  # '4'
    (18, 72),  # 'H'
    (19, 69),  # 'E'
    (22, 76),  # 'L'
    (30, 57),  # '9'
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

def send_cmd(chan, cmd, timeout=20, marker="# "):
    chan.send(cmd + "\n")
    return recv_until(chan, [marker, "WAP>", "SU_WAP>"], timeout)

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
    print("[+] Shell ready\n")
    return client, chan

def main():
    print("=" * 62)
    print("  Extracting 32-byte ALPHA table from /bin/ssmp")
    print("=" * 62)

    client, chan = connect()

    # ── 0. Confirm correct ssmp binary ───────────────────────────────────
    print("[*] Checking /bin/ssmp...")
    out = send_cmd(chan, "ls -la /bin/ssmp && md5sum /bin/ssmp 2>&1")
    print(out.strip().split('\n')[-2] if '\n' in out else out.strip()[-200:])

    # ── 1. Try Python3 scan on-device ────────────────────────────────────
    # The scanner looks for any 32-byte aligned window in ssmp that matches
    # our 12 known ALPHA entries.
    print("\n[*] Uploading scanner script to /tmp/scan_alpha.py ...")

    scanner = r"""
import sys
checks = [(1,57),(2,72),(3,82),(4,69),(7,57),(10,33),(11,80),
          (15,52),(18,72),(19,69),(22,76),(30,57)]
data = open('/bin/ssmp','rb').read()
print(f'ssmp size: {len(data)} bytes')
best_score = 0
best_off = -1
results = []
for offset in range(len(data)-32):
    b = data[offset:offset+32]
    score = sum(1 for idx,val in checks if b[idx]==val)
    if score > best_score:
        best_score = score
        best_off = offset
    if score >= 8:
        results.append((score, offset, bytes(b)))
if results:
    for score, offset, b in sorted(results, reverse=True)[:5]:
        print(f'SCORE {score}/12 at offset {offset} (0x{offset:x}):')
        print('  hex: ' + ' '.join(f'{x:02x}' for x in b))
        print('  asc: ' + ''.join(chr(x) if 32<=x<127 else '.' for x in b))
else:
    print(f'Best score: {best_score}/12 at offset {best_off} (0x{best_off:x})')
    b = data[best_off:best_off+32]
    print('  hex: ' + ' '.join(f'{x:02x}' for x in b))
    print('  asc: ' + ''.join(chr(x) if 32<=x<127 else '.' for x in b))
print('SCAN_DONE')
""".strip()

    # Upload via heredoc
    chan.send("cat > /tmp/scan_alpha.py << 'PYEOF'\n")
    time.sleep(0.3)
    for line in scanner.split('\n'):
        chan.send(line + "\n")
        time.sleep(0.05)
    chan.send("PYEOF\n")
    out = recv_until(chan, "# ", timeout=10)
    print(f"  Upload: {'OK' if 'PYEOF' not in out or '#' in out else 'check'}")

    print("\n[*] Running scanner (this may take 30-60 seconds)...")
    chan.send("python3 /tmp/scan_alpha.py 2>&1\n")
    out = recv_until(chan, ["SCAN_DONE", "# "], timeout=120)
    print(out.strip()[-2000:])

    # ── 2. If python3 not found, use shell-based scan ─────────────────────
    if "not found" in out or "No such" in out:
        print("\n[*] Python3 not found, trying shell-based approach...")
        
        # Use od to dump hex and search
        chan.send("od -An -tx1 /bin/ssmp > /tmp/ssmp_od.txt 2>&1 && echo OD_OK\n")
        out = recv_until(chan, ["OD_OK", "# "], timeout=30)
        print(f"  od dump: {'OK' if 'OD_OK' in out else out.strip()[-100:]}")

        # Parse with awk: look for consecutive bytes matching our pattern
        # This is approximated in shell
        awk_script = r"""
awk '{for(i=1;i<=NF;i++) printf "%s ", $i} END {printf "\n"}' /tmp/ssmp_od.txt \
| tr ' ' '\n' | grep -v '^$' > /tmp/ssmp_bytes.txt
wc -l /tmp/ssmp_bytes.txt
""".strip()
        out = send_cmd(chan, awk_script.replace('\n', '; '), timeout=30)
        print(f"  Bytes extracted: {out.strip()[-100:]}")

    # ── 3. Download ssmp binary via base64 ───────────────────────────────
    print("\n[*] Downloading /bin/ssmp via base64...")
    chan.send("wc -c /bin/ssmp\n")
    out = recv_until(chan, "# ", timeout=5)
    size_line = [l for l in out.split('\n') if '/bin/ssmp' in l]
    ssmp_size = 0
    if size_line:
        try: ssmp_size = int(size_line[0].strip().split()[0])
        except: pass
    print(f"  ssmp size on router: {ssmp_size} bytes")

    if ssmp_size > 0 and ssmp_size < 5_000_000:
        print(f"  [*] Base64 encoding /bin/ssmp (may take a moment)...")
        chan.send("base64 /bin/ssmp > /tmp/ssmp.b64 2>&1 && wc -c /tmp/ssmp.b64\n")
        out = recv_until(chan, "# ", timeout=60)
        b64_size = 0
        for l in out.split('\n'):
            if '/tmp/ssmp.b64' in l:
                try: b64_size = int(l.strip().split()[0])
                except: pass
        print(f"  Base64 size: {b64_size}")

        if b64_size > 0:
            print(f"  [*] Reading base64 data in chunks...")
            # Read chunks
            chunk_size = 60000  # chars per chunk
            b64_data = ""
            offset = 0
            while offset < b64_size:
                cmd = f"dd if=/tmp/ssmp.b64 bs=1 skip={offset} count={chunk_size} 2>/dev/null"
                chan.send(cmd + "\n")
                out = recv_until(chan, "# ", timeout=30)
                # Extract b64 chars (filter out command echo and prompt)
                chunk = ""
                for line in out.split('\n'):
                    line = line.strip().replace('\r', '')
                    if line and 'dd ' not in line and '# ' not in line and 'WAP' not in line:
                        # Filter to valid base64 chars
                        chunk += ''.join(c for c in line if c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
                b64_data += chunk
                offset += chunk_size
                print(f"    Read {len(b64_data)} base64 chars so far...")
                if len(b64_data) >= b64_size * 0.95:
                    break

            if b64_data:
                import base64
                # Pad if needed
                padding = 4 - len(b64_data) % 4
                if padding != 4: b64_data += '=' * padding
                try:
                    ssmp_data = base64.b64decode(b64_data)
                    print(f"  [+] Downloaded ssmp: {len(ssmp_data)} bytes")
                    
                    # Save locally
                    with open('/tmp/ssmp_router.bin', 'wb') as f:
                        f.write(ssmp_data)
                    print(f"  [+] Saved to /tmp/ssmp_router.bin")
                    
                    # Now scan the downloaded binary
                    print("\n[*] Scanning downloaded binary for 32-byte ALPHA table...")
                    best_score = 0
                    best_off = -1
                    for offset in range(len(ssmp_data) - 32):
                        b = ssmp_data[offset:offset+32]
                        score = sum(1 for idx, val in CHECKS_32 if b[idx] == val)
                        if score > best_score:
                            best_score = score
                            best_off = offset
                        if score >= 9:
                            print(f"  [+] HIGH SCORE {score}/12 at offset {offset} (0x{offset:x}):")
                            asc = ''.join(chr(x) if 32<=x<127 else '.' for x in b)
                            hex_s = ' '.join(f'{x:02x}' for x in b)
                            print(f"    HEX: {hex_s}")
                            print(f"    ASC: {asc}")
                    
                    print(f"\n  Best: {best_score}/12 at offset {best_off} (0x{best_off:x})")
                    if best_off >= 0:
                        b = ssmp_data[best_off:best_off+32]
                        print(f"  HEX: {' '.join(f'{x:02x}' for x in b)}")
                        print(f"  ASC: {''.join(chr(x) if 32<=x<127 else '.' for x in b)}")
                        print(f"  LIST: {list(b)}")
                except Exception as e:
                    print(f"  [-] Base64 decode error: {e}")
    
    # ── 4. Alternative: scan using strings output ─────────────────────────
    print("\n[*] Searching for strings in /bin/ssmp that contain password chars:")
    out = send_cmd(chan, r"cat /bin/ssmp | tr -cd '\11\12\15\40-\176' | grep -oE '.{20,40}' | grep -E '[!.?][0-9][0-9][A-Z0-9]{3,}' | head -20", timeout=20)
    print(out.strip()[-500:])

    # ── 5. Search for specific byte sequences near 'sUser' string ────────
    print("\n[*] Finding 'sUser' offset and nearby data in ssmp:")
    chan.send("python3 -c \"\ndata=open('/bin/ssmp','rb').read()\nidx=data.find(b'sUser')\nprint(f'sUser at offset {idx}')\nif idx>0:\n    # look at 256 bytes before and after\n    region = data[max(0,idx-512):idx+512]\n    print('region hex (sUser-512 to sUser+512):')\n    for i in range(0,len(region),16):\n        row=region[i:i+16]\n        h=' '.join(f'{b:02x}' for b in row)\n        a=''.join(chr(b) if 32<=b<127 else '.' for b in row)\n        print(f'  {i:4d}: {h}  {a}')\n\" 2>&1 | head -80\n")
    out = recv_until(chan, "# ", timeout=30)
    print(out.strip()[-3000:])

    client.close()
    print("\n[*] Done.")

if __name__ == "__main__":
    main()
