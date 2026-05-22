#!/usr/bin/env python3
"""
The '9HRE' (39 48 52 45) sequence is NOT in .rodata!
This means either:
1. The formula is WRONG (not a lookup table at all)
2. The table is in a different section
3. The data is encoded/encrypted differently

Key insight from hexdump test: hexdump -C works but pattern not found.
Let me try:
a) Search ALL sections of the binary for this pattern
b) Re-examine the formula completely
c) Consider that the local binary might not be the same FIRMWARE
   even though MD5 matches the router's reported size

CRUCIAL RE-EXAMINATION:
We assumed formula is ALPHA[(byte>>1)%32].
But the conflict-free mapping might have been coincidental!
Let me verify more carefully.

The bytes and expected chars:
72→E, 87→P, 84→!, 67→9, 124→9, 7→R, 222→4, 165→H, 108→L, 197→H, 15→9, 39→E

For byte>>1: 36→E, 43→P, 42→!, 33→9, 62→9, 3→R, 111→4, 82→H, 54→L, 98→H, 7→9, 19→E
For (>>1)%32: 4→E, 11→P, 10→!, 1→9, 30→9, 3→R, 15→4, 18→H, 22→L, 2→H, 7→9, 19→E

These are CONFLICT-FREE, but the actual TABLE doesn't exist as a contiguous block!

ALTERNATIVE: The password is generated character by character using some MATHEMATICAL formula.
Let me try brute-forcing: what function f(byte) → char_ascii for all 12 known pairs?
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

def local_exhaustive_search():
    """Exhaustively search the local binary for the ALPHA table with all formula variants."""
    local_data = open('/home/recep/Masaüstü/Firmware/squashfs-root-recovered/bin/ssmp', 'rb').read()
    
    sn1 = bytes.fromhex(SN1)
    crc1 = zlib.crc32(sn1) & 0xFFFFFFFF
    ext1 = list(sn1) + list(struct.pack('>I', crc1))
    
    print("=== EXHAUSTIVE LOCAL BINARY SEARCH ===\n")
    print(f"Binary size: {len(local_data)} bytes")
    print(f"SN_ext: {[hex(b) for b in ext1]}")
    print(f"P1: {P1}\n")
    
    # For each possible table formula, check if the table exists in the binary
    # Formula: char = BINARY[table_offset + f(byte)]
    # where f(byte) can be various functions
    
    pairs = [(b, ord(c)) for b, c in zip(ext1, P1)]
    
    # Key constraint: for 'H' appearing at bytes 165 and 197:
    # f(165) and f(197) must map to the SAME index in the table
    # For '9' at bytes 67, 124, 15:
    # f(67)=f(124)=f(15) must all map to same index
    # For 'E' at bytes 72, 39:
    # f(72)=f(39) must map to same index
    
    # What functions f make all these equal?
    # f(165) == f(197): difference = 32 = 2^5
    # f(67) == f(124): difference = 57 (prime)
    # f(67) == f(15): difference = 52 = 4*13
    # f(72) == f(39): difference = 33 = 3*11
    
    # For f(x) = x >> K:
    # 165>>K == 197>>K when they differ only in bits 0..K-1
    # 165 = 10100101, 197 = 11000101
    # XOR = 01100000 = 96 = 2^5 * 3
    # So 165>>K == 197>>K iff K >= 6 (since bits 5 and 6 differ)
    # K=6: 165>>6 = 2, 197>>6 = 3 → NOT EQUAL
    # K=7: 165>>7 = 1, 197>>7 = 1 → EQUAL! But 72>>7=0, 87>>7=0...
    # K=7 means ALL bytes >> 7 gives only 0 or 1 → only 2 distinct chars
    # That can't produce 8 unique chars.
    
    # Wait: 165>>K == 197>>K requires XOR(165,197) < 2^K
    # XOR(165,197) = 96 = 0b01100000 → requires K >= 7 (since bit 6 is set)
    # But K=7 maps to 2 values maximum. Not useful.
    
    # For f(x) = x % M:
    # 165%M == 197%M iff M | 32 → M ∈ {1,2,4,8,16,32}
    # 67%M == 124%M iff M | 57 → M ∈ {1,3,19,57}
    # 67%M == 15%M iff M | 52 → M ∈ {1,2,4,13,26,52}
    # 72%M == 39%M iff M | 33 → M ∈ {1,3,11,33}
    # Common M for all: M | GCD(32,57,52,33)
    # GCD(32,57) = 1 (57=3*19, 32=2^5, no common factors)
    # GCD = 1 → only M=1 works, which means all bytes map to same index → useless!
    
    print("Mathematical analysis:")
    import math
    diffs_H = [abs(165-197)]  # 32
    diffs_9 = [abs(67-124), abs(67-15), abs(124-15)]  # 57, 52, 109
    diffs_E = [abs(72-39)]  # 33
    
    all_diffs = diffs_H + diffs_9 + diffs_E
    print(f"  Diff pairs: H:{diffs_H}, 9:{diffs_9}, E:{diffs_E}")
    
    g = diffs_H[0]
    for d in all_diffs[1:]:
        g = math.gcd(g, d)
    print(f"  GCD of all diffs: {g}")
    print(f"  → For modular formula (byte%M), M must divide {g}")
    print(f"  → Only M=1 divides 1, meaning NO modular formula works!")
    print()
    print("CONCLUSION: The password generation does NOT use a simple modular/shift lookup table!")
    print("The formula must be more complex.")
    print()
    
    # ── Try: maybe the formula uses TWO steps ────────────────────────────
    # Step 1: byte → intermediate value
    # Step 2: intermediate value → char via lookup
    # 
    # OR: The password is generated from a completely different input
    # that we haven't considered yet.
    
    # ── Observation: both H=72 and H=72 means the char ASCII equals the byte value!
    # H(72) → 72, and 72 = 0x48 = 'H'!!! 
    print("EUREKA moment check:")
    for b, c_ascii in pairs:
        print(f"  byte={b}({hex(b)}) → char={chr(c_ascii)}({c_ascii}/{hex(c_ascii)})  same? {b==c_ascii}")
    
    # Check: do any byte values equal their char values?
    # 165 → H(72): 165 ≠ 72 ✗
    # 72 → E(69): 72 ≠ 69 ✗
    # 7 → R(82): 7 ≠ 82 ✗
    
    # ── Try: XOR of consecutive bytes ────────────────────────────────────
    print("\nXOR of consecutive ext bytes vs char:")
    for i in range(len(ext1)-1):
        xor_val = ext1[i] ^ ext1[i+1]
        c = P1[i]
        print(f"  ext[{i}]({hex(ext1[i])}) XOR ext[{i+1}]({hex(ext1[i+1])}) = {hex(xor_val)} vs '{c}'({hex(ord(c))})")

local_exhaustive_search()

print("\n" + "="*62)
print("  On-device: Search ALL binary sections for pattern")
print("="*62)

def main():
    client, chan = connect()
    print("[+] Connected\n")

    # Search ALL sections via hexdump, not just .rodata
    print("[*] Searching for '39 48 52 45' (9HRE) in FULL binary via hexdump...")
    
    # Use hexdump on the full file - but that will be huge output
    # Instead: search for the specific pattern
    
    # hexdump -C shows: "OFFSET  xx xx xx xx ... |ASCII|"
    # We need to find rows where the 4 specific bytes appear consecutively
    
    # Strategy: extract only .text section (code) - maybe table is there
    TEXT_OFF  = 0       # .text usually starts at beginning 
    TEXT_SIZE = 290564  # everything before .rodata
    
    # Extract .text section
    cmd = f"dd if=/tmp/ss bs=1 count={TEXT_SIZE} 2>/dev/null > /tmp/text_sec.bin && wc -c /tmp/text_sec.bin"
    out = run(chan, cmd, timeout=30)
    print(f"  .text section: {out.strip()[-100:]}")
    
    # Search for pattern
    cmd2 = "hexdump -C /tmp/text_sec.bin | grep '39 48 52 45' | head -10"
    out2 = run(chan, cmd2, timeout=30)
    print(f"  Pattern in .text: {out2.strip()[-300:]}")
    
    # Search for '39 48 52' (9HR)
    cmd3 = "hexdump -C /tmp/text_sec.bin | grep '39 48 52' | head -5"
    out3 = run(chan, cmd3, timeout=30)
    print(f"  Partial '9HR' in .text: {out3.strip()[-300:]}")
    
    # Search for JUST the byte 0x52 (R) in the context of a table
    # At position 3 of every 32 bytes, we should find 0x52
    # This means we're looking for a structure that repeats with R at position 3
    
    # ── Alternative: try to run ssmp directly with a known SN ────────────
    print("\n[*] Trying to call ssmp password generation directly...")
    # Check if ssmp has any command-line interface
    out = run(chan, "/bin/ssmp --help 2>&1 | head -10", timeout=5)
    print(f"  ssmp --help: {out.strip()[-200:]}")
    
    out = run(chan, "/bin/ssmp 2>&1 | head -5", timeout=5)
    print(f"  ssmp (no args): {out.strip()[-100:]}")
    
    # ── Check if there's a utility to get sUser password ─────────────────
    print("\n[*] Looking for password utilities...")
    for util in ["/bin/passwd_gen", "/bin/getpasswd", "/usr/bin/passwd_gen",
                 "/etc/wap/passwd_gen", "/bin/userpasswd"]:
        out = run(chan, f"ls -la {util} 2>/dev/null && echo EXISTS")
        if "EXISTS" in out:
            print(f"  FOUND: {util}")
            out2 = run(chan, f"{util} --help 2>&1 | head -5")
            print(f"  {out2.strip()[-100:]}")
    
    # ── Get multiple SN→password pairs by reading ctree ──────────────────
    print("\n[*] Reading ctree for device info...")
    out = run(chan, "cat /var/HW_ctree.xml 2>/dev/null | grep -E 'sUser|Password|SerialNumber' | head -10", timeout=10)
    print(out.strip()[-500:])

    # ── Check WAP CLI for current sUser password ──────────────────────────
    print("\n[*] Using WAP CLI to verify password correlation...")
    run(chan, "exit")
    recv_until(chan, "SU_WAP>", timeout=5)
    
    # Try to display user info
    chan.send("display user all\n")
    out = recv_until(chan, "SU_WAP>", timeout=8)
    print(out.strip()[-300:])
    
    chan.send("display user sUser\n")
    out = recv_until(chan, "SU_WAP>", timeout=8)
    print(out.strip()[-300:])

    client.close()

if __name__ == "__main__":
    local_exhaustive_search()
    main()
