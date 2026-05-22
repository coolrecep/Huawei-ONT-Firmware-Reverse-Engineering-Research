#!/usr/bin/env python3
"""
New Strategy:
Since the table is NOT in the binary as a static block, it must be:
1. Dynamically built at runtime from scattered data
2. OR the formula uses something other than a lookup table

Let's go back to basics:
- Connect to router via SSH interactive shell
- Read /proc/<ssmp_pid>/mem at the function address to get the runtime table
- OR: use the od approach properly with exec_command (not interactive)
- OR: dump specific memory regions

Key: ssmp PID = 1650, running as UID=3008 (srv_ssmp)
We have shell as srv_clid (UID=3030) which has kmc group access.

Let's try reading /proc/1650/mem for the stack/heap where the table might be built.
"""

import paramiko, time, struct, zlib

HOST     = "192.168.1.1"
USER     = "sUser"
PASSWORD = "EP!99R4HLH9E"

P1   = "EP!99R4HLH9E"
SN1  = "485754437C07DEA5"

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
    print("  Runtime Memory Dump & ALPHA Table Discovery")
    print("=" * 62)

    client, chan = connect()
    print("[+] Shell ready\n")

    # ── Step 1: Get ssmp process maps ─────────────────────────────────────
    print("[*] Getting /proc/1650/maps...")
    out = run(chan, "cat /proc/1650/maps 2>&1 | head -40")
    print(out.strip()[-3000:])

    # ── Step 2: Find .text and .rodata ranges ─────────────────────────────
    print("\n[*] Finding ssmp memory regions...")
    out = run(chan, "cat /proc/1650/maps 2>&1")
    
    # Parse memory regions
    regions = []
    for line in out.split('\n'):
        line = line.strip().replace('\r', '')
        if not line or 'map' in line.lower() or '#' in line: continue
        parts = line.split()
        if len(parts) >= 5 and '-' in parts[0]:
            try:
                start_s, end_s = parts[0].split('-')
                start = int(start_s, 16)
                end = int(end_s, 16)
                perms = parts[1] if len(parts) > 1 else '----'
                name = parts[-1] if len(parts) > 4 else ''
                regions.append((start, end, perms, name))
            except: pass
    
    print(f"\nParsed {len(regions)} memory regions:")
    for start, end, perms, name in regions[:20]:
        print(f"  0x{start:08x}-0x{end:08x} {perms} {name}")

    # ── Step 3: Read .rodata section from process memory ─────────────────
    # Look for read-only executable regions (likely ssmp code+rodata)
    ssmp_regions = [(s,e,p,n) for s,e,p,n in regions if 'ssmp' in n or n == '/bin/ssmp']
    print(f"\nssmp-specific regions: {len(ssmp_regions)}")
    for s,e,p,n in ssmp_regions:
        print(f"  0x{s:08x}-0x{e:08x} {p} {n} (size={e-s})")

    # ── Step 4: Use dd to read specific offsets from /proc/1650/mem ──────
    print("\n[*] Reading rodata from /proc/1650/mem using dd...")
    
    # The ssmp binary's .rodata section starts at offset 0x46f04 in the file
    # If ssmp is loaded at some base address, the virtual address would be:
    # base_addr + 0x46f04 (for non-PIE) or base + offset (for PIE)
    
    # From ELF: .rodata at file offset 0x46f04, virtual addr 0x46f04
    # For non-PIE ARM: typically loaded at a fixed address like 0x8000 or 0x10000
    
    # Let's check the ssmp base address from maps
    ssmp_exec = [(s,e,p,n) for s,e,p,n in regions if 'ssmp' in n and 'r-x' in p]
    if ssmp_exec:
        base_addr = ssmp_exec[0][0]
        print(f"  ssmp .text base: 0x{base_addr:08x}")
        
        # rodata virtual address = base + 0x46f04 (from ELF analysis)
        rodata_vaddr = base_addr + 0x46f04
        print(f"  Expected .rodata vaddr: 0x{rodata_vaddr:08x}")
        
        # Read 256 bytes from rodata area
        # dd if=/proc/1650/mem bs=1 skip=<vaddr> count=256 2>/dev/null | od -An -tx1
        cmd = f"dd if=/proc/1650/mem bs=1 skip={rodata_vaddr} count=512 2>/dev/null | od -An -tx1"
        out = run(chan, cmd, timeout=30)
        print(f"  rodata sample:\n{out.strip()[-1000:]}")

    # ── Step 5: Read ssmp full binary from /proc/1650/exe ─────────────────
    print("\n[*] Reading ssmp via /proc/1650/exe...")
    out = run(chan, "ls -la /proc/1650/exe 2>&1")
    print(out.strip()[-200:])
    
    out = run(chan, "wc -c /proc/1650/exe 2>&1")
    print(f"  exe size: {out.strip()[-100:]}")
    
    # Try od on the exe
    print("\n[*] od dump of /proc/1650/exe (first 200 bytes)...")
    out = run(chan, "od -An -tx1 /proc/1650/exe 2>/dev/null | head -15")
    print(out.strip()[-500:])

    # ── Step 6: Focused search — read bytes at known formula positions ────
    # If SN1 = 485754437C07DEA5 and formula is ALPHA[(byte>>1)%32],
    # then the ALPHA table has entries at specific offsets.
    # Let's try to call the password generation function directly via
    # the 'su' workaround in WAP CLI.
    
    print("\n[*] Testing a different SN via WAP CLI to get more (SN→pwd) pairs...")
    # First: check what functions exist in ssmp via strings
    out = run(chan, "strings /bin/ssmp 2>/dev/null | grep -iE 'password|passwd|crypt|encode|cipher|sUser|getpwd' | head -20", timeout=15)
    print(out.strip()[-500:])

    # ── Step 7: Use awk to search /proc/1650/mem for our table ───────────
    print("\n[*] Searching process memory for ALPHA table pattern...")
    # We know: the byte sequence at the table must contain 
    # at position 1: 0x39 ('9')
    # at position 2: 0x48 ('H')  
    # at position 3: 0x52 ('R')
    # at position 4: 0x45 ('E')
    # This 4-byte sequence at offset 1: 39 48 52 45 ← "9HRE"
    # Search for this in process memory:
    cmd = r"od -An -tx1 /proc/1650/mem 2>/dev/null | grep -c '39 48 52 45'"
    out = run(chan, cmd, timeout=30)
    print(f"  Pattern '9HRE' count in proc mem: {out.strip()[-100:]}")

    cmd2 = r"od -An -tx1 /proc/1650/mem 2>/dev/null | grep '39 48 52 45' | head -5"
    out2 = run(chan, cmd2, timeout=30)
    print(f"  Pattern matches:\n{out2.strip()[-500:]}")

    # ── Step 8: Look for ssmp function that generates password ───────────
    print("\n[*] Looking for password-generation related strings in ssmp...")
    for pattern in ["sUser", "srv_ssmp", "passwd", "ALPHA", "table", "encode", "passwd_gen", "userpass"]:
        out = run(chan, f"strings /bin/ssmp 2>/dev/null | grep -i '{pattern}' | head -5", timeout=10)
        matches = [l.strip() for l in out.split('\n') if pattern.lower() in l.lower() and '#' not in l]
        if matches:
            print(f"  '{pattern}': {matches[:3]}")

    # ── Step 9: Get another SN→password pair if possible ─────────────────
    print("\n[*] Looking for any stored SN data on device...")
    for f in ["/var/ssmpdelaysavectree", "/etc/wap/HW_ctree.xml", "/var/HW_ctree.xml", 
              "/etc/boardinfo", "/proc/sys/kernel/hostname"]:
        out = run(chan, f"cat {f} 2>/dev/null | head -5", timeout=5)
        if out and '#' in out:
            content = [l.strip() for l in out.split('\n') if l.strip() and '#' not in l]
            if content:
                print(f"  {f}:")
                for l in content[:3]:
                    print(f"    {l}")

    # ── Step 10: Read the MAC from board info and check correlation ───────
    print("\n[*] Board serial/MAC info:")
    out = run(chan, "cat /proc/sys/kernel/hostname 2>/dev/null; ifconfig br0 2>/dev/null | head -5")
    print(out.strip()[-500:])

    client.close()
    print("\n[*] Done.")

if __name__ == "__main__":
    main()
