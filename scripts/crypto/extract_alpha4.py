#!/usr/bin/env python3
"""
Final approach: Two separate SSH connections.
Connection 1 (interactive shell): navigate to shell
Connection 2 (exec): run the binary download command

The key insight: the router binary IS the same as the local one 
(same MD5 = 6acedaab0570d66a00dbc1e593460154, size = 358092).

So we can use the LOCAL binary directly, but search differently.
The issue is: our search checks exact 32-byte alignment.
The table might be at an ODD offset OR might use a different index formula.

Let me re-examine our formula and try more flexible searches.
"""

import paramiko, time, struct, zlib, hashlib

HOST     = "192.168.1.1"
USER     = "sUser"
PASSWORD = "EP!99R4HLH9E"

P1   = "EP!99R4HLH9E"
SN1  = "485754437C07DEA5"
P2   = "Y7.15R1TLU6?"

# ── Re-verify: is the local binary the same as the router binary? ─────────────
local_path = '/home/recep/Masaüstü/Firmware/squashfs-root-recovered/bin/ssmp'
with open(local_path, 'rb') as f:
    local_data = f.read()

local_md5 = hashlib.md5(local_data).hexdigest()
router_md5 = "6acedaab0570d66a00dbc1e593460154"  # from router ls output
print(f"Local  MD5: {local_md5}")
print(f"Router MD5: {router_md5}")
print(f"Same binary: {local_md5 == router_md5}")
print(f"Local size: {len(local_data)}")
print()

# ── Since same binary: scan locally but more thoroughly ─────────────────────
print("=" * 62)
print("  Scanning local ssmp binary more thoroughly")
print("=" * 62)

CHECKS_32 = [
    (1,57),(2,72),(3,82),(4,69),(7,57),(10,33),(11,80),
    (15,52),(18,72),(19,69),(22,76),(30,57)
]

# The issue might be:
# 1. The table is NOT contiguous (has gaps)
# 2. The formula is slightly different 
# 3. The binary is the SAME but table is dynamically built at runtime

# Let's try ALL possible formula variants on the local binary:
sn1 = bytes.fromhex(SN1)
crc1 = zlib.crc32(sn1) & 0xFFFFFFFF
ext1 = list(sn1) + list(struct.pack('>I', crc1))

print(f"SN_ext bytes: {ext1}")
print(f"Target P1:    {list(P1)}")
print()

# ── Variant 1: table[byte % N] (different N values) ─────────────────────────
print("Testing all 'ALPHA[byte % N]' variants in binary:")
for N in range(8, 256, 1):
    indices = [b % N for b in ext1]
    slot_to_char = {}
    conflict = False
    for idx, c in zip(indices, P1):
        if idx in slot_to_char and slot_to_char[idx] != c:
            conflict = True; break
        slot_to_char[idx] = c
    if conflict: continue
    
    # Check: is there an N-byte sequence in the binary that matches?
    max_idx = max(indices)
    table_size = max_idx + 1
    
    checks_n = [(idx, ord(c)) for idx, c in slot_to_char.items()]
    
    best_score = 0
    for offset in range(len(local_data) - table_size):
        b = local_data[offset:offset + table_size]
        score = sum(1 for idx, val in checks_n if idx < len(b) and b[idx] == val)
        if score > best_score:
            best_score = score
        if score == len(checks_n):
            print(f"\n  *** MATCH! N={N}, table at offset {offset} (0x{offset:x}) ***")
            print(f"      Table bytes (first {table_size}): {list(b[:table_size])}")
            print(f"      ASCII: {''.join(chr(x) if 32<=x<127 else '.' for x in b[:table_size])}")
            # Full verification
            result = ''.join(chr(b[byte % N]) if 32 <= b[byte % N] < 127 else '?' for byte in ext1)
            print(f"      P1 result: {result}")
            break
    
    if best_score >= len(checks_n) - 1:  # close match
        print(f"  N={N}: {best_score}/{len(checks_n)} at some offset")

# ── Variant 2: (byte >> K) % N for various K and N ─────────────────────────
print("\nTesting '(byte >> K) % N' variants:")
for K in range(1, 4):
    for N in [16, 24, 32, 40, 48, 64]:
        indices = [(b >> K) % N for b in ext1]
        slot_to_char = {}
        conflict = False
        for idx, c in zip(indices, P1):
            if idx in slot_to_char and slot_to_char[idx] != c:
                conflict = True; break
            slot_to_char[idx] = c
        if conflict: continue
        
        max_idx = max(indices)
        checks_n = [(idx, ord(c)) for idx, c in slot_to_char.items()]
        
        # Search in binary
        for offset in range(len(local_data) - (max_idx + 1)):
            b = local_data[offset:offset + max_idx + 1]
            score = sum(1 for idx, val in checks_n if idx < len(b) and b[idx] == val)
            if score == len(checks_n):
                print(f"\n  *** MATCH! K={K}, N={N}, offset=0x{offset:x} ***")
                table = local_data[offset:offset+max_idx+1]
                print(f"      Table: {''.join(chr(x) if 32<=x<127 else '.' for x in table)}")
                result = ''.join(chr(table[(byte>>K)%N]) if 32<=table[(byte>>K)%N]<127 else '?' for byte in ext1)
                print(f"      P1: {result}")
                break

# ── Variant 3: Maybe it's NOT a lookup table but a mathematical formula ───────
print("\n=== Testing mathematical formulas ===")
# What if each byte of the SN goes through a specific math op to get an ASCII char?

# Test: char = chr(f(byte)) for various simple f
# For ext1 bytes and P1 chars:
pairs = list(zip(ext1, [ord(c) for c in P1]))
print(f"(byte, char_ascii) pairs: {pairs}")

# Find polynomial/linear relationship
# If char = (a * byte + b) % M for some a, b, M:
from itertools import product as iproduct
print("\nSearching for linear formula: char_ascii = (a*byte + b) % M...")
for M in [95, 96, 126, 127, 64, 128]:
    for a in range(1, 20):
        for b in range(0, M):
            ok = True
            for byte_val, char_ascii in pairs:
                if (a * byte_val + b) % M + 33 != char_ascii:
                    if (a * byte_val + b) % M != char_ascii:
                        ok = False
                        break
            if ok:
                print(f"  MATCH! char = ({a}*byte + {b}) % {M}: test={[(a*bv+b)%M for bv,_ in pairs]}")

# ── Final: maybe the algorithm uses a DIFFERENT key from the SN ──────────────
print("\n=== Alternative: Does the algorithm use a different key? ===")
# From boardinfo, we also have:
# obj.id 0x0007: "028HHFHYM3004875" (16 chars)  
# obj.id 0x0008: "2150084230HYM3000324" (20 chars)
# MAC: 90:16:BA:52:75:6F

other_keys = [
    ("boardinfo_0007", b"028HHFHYM3004875"),
    ("boardinfo_0008", b"2150084230HYM3000324"),
    ("mac", bytes.fromhex("9016BA52756F")),
    ("mac_str", b"90:16:BA:52:75:6F"),
    ("sn_str",  b"485754437C07DEA5"),
    ("sn_lower", b"485754437c07dea5"),
]

for name, key_bytes in other_keys:
    crc = zlib.crc32(key_bytes) & 0xFFFFFFFF
    ext = list(key_bytes[:8]) + list(struct.pack('>I', crc))
    if len(ext) >= 12:
        shifted = [(b>>1)%32 for b in ext[:12]]
        # Check if this mapping is conflict-free
        slot_to_char = {}
        conflict = False
        for slot, c in zip(shifted, P1):
            if slot in slot_to_char and slot_to_char[slot] != c:
                conflict = True; break
            slot_to_char[slot] = c
        status = "CONFLICT" if conflict else f"OK, slots={slot_to_char}"
        print(f"  key={name}: {status[:80]}")
