#!/usr/bin/env python3
"""
BREAKTHROUGH: K=1 (byte >> 1) produces a CONFLICT-FREE mapping!
  shifted = [b >> 1 for b in ext1]
  shifted: [36, 43, 42, 33, 62, 3, 111, 82, 54, 98, 7, 19]
  password: E   P   !   9  9   R  4    H   L   H   9  E

So the formula is: char = ALPHA[ byte >> 1 ]
where the alphabet/lookup is indexed by (byte // 2).

byte >> 1 ranges: 0..127 (since bytes are 0..255)
So we need a 128-entry lookup table.

Let's reconstruct the table and validate with P2.
"""

import zlib, struct

P1  = "EP!99R4HLH9E"
SN1 = "485754437C07DEA5"
P2  = "Y7.15R1TLU6?"

sn1_bytes = bytes.fromhex(SN1)
crc1      = zlib.crc32(sn1_bytes) & 0xFFFFFFFF
ext1      = list(sn1_bytes) + list(struct.pack('>I', crc1))

# Shifted values (byte >> 1):
shifted1 = [b >> 1 for b in ext1]
print("=== Algorithm: char = TABLE[byte >> 1] ===\n")
print(f"SN1   : {SN1}")
print(f"CRC32 : {hex(crc1)}")
print(f"Bytes : {[hex(b) for b in ext1]}")
print(f">>1   : {shifted1}")
print(f"P1    : {list(P1)}")

# Build 128-entry lookup table
TABLE = ['?'] * 128
for s, c in zip(shifted1, P1):
    TABLE[s] = c

print("\nKnown TABLE entries (index = byte >> 1):")
for i, c in enumerate(TABLE):
    if c != '?':
        print(f"  TABLE[{i:3d}] = '{c}'   (bytes {i*2} and {i*2+1} = {hex(i*2)} and {hex(i*2+1)})")

# ── Validate: use the partial table to predict P2 ────────────────────────────
print(f"\n=== Predicting from P2's known positions ===")
# For P2[5]='R': SN2[5] >> 1 must be in TABLE entries with value 'R'
r_indices = [i for i, c in enumerate(TABLE) if c == 'R']
l_indices = [i for i, c in enumerate(TABLE) if c == 'L']
print(f"  'R' at TABLE indices: {r_indices}  → SN2[5] ∈ {[i*2 for i in r_indices] + [i*2+1 for i in r_indices]}")
print(f"  'L' at TABLE indices: {l_indices}  → CRC2[0] ∈ {[i*2 for i in l_indices] + [i*2+1 for i in l_indices]}")

# SN1[5] = 0x07 = 7 → 7>>1 = 3 → TABLE[3] = 'R' ✓
print(f"\n  SN1[5]=0x07, 7>>1=3, TABLE[3]='R' ✓")
print(f"  CRC1[0]=0x6C=108, 108>>1=54, TABLE[54]='L' ✓")

# ── Now try to determine SN2 from P2 ─────────────────────────────────────────
print(f"\n=== Inferring SN2 from P2 ===")
print(f"P2: {P2}")

# P2[5]='R' → SN2[5] >> 1 = 3 → SN2[5] ∈ {6, 7}
# SN1[5]=7 and SN2[5] must be 6 or 7
print(f"P2[5]='R': SN2[5] ∈ {{6, 7}}")
# P2[8]='L' → CRC2[0] >> 1 = 54 → CRC2[0] ∈ {108, 109}
print(f"P2[8]='L': CRC2[0] ∈ {{108, 109}}")

# For each char in P2 that IS in our table, find the index and thus the bytes:
print(f"\nChar constraints from P2:")
for i, c in enumerate(P2):
    matching = [j for j, t in enumerate(TABLE) if t == c]
    if matching:
        possible_bytes = [v for j in matching for v in [j*2, j*2+1]]
        print(f"  P2[{i}]='{c}': TABLE indices={matching} → ext2[{i}] ∈ {possible_bytes}")
    else:
        print(f"  P2[{i}]='{c}': NEW char (not yet in table) → gives us a new TABLE entry")

# ── Fill in more table entries from P2 ────────────────────────────────────────
# For positions where P2 char is NOT yet in table, we need to know ext2[i] >> 1
# We don't know ext2 directly, but we know:
# ext2 = SN2(8 bytes) + CRC32(SN2)(4 bytes)
# SN2 likely starts with HWTC = 48 57 54 43

print(f"\n=== If SN2 starts with HWTC (48 57 54 43) ===")
HWTC = [0x48, 0x57, 0x54, 0x43]
for i, b in enumerate(HWTC):
    idx = b >> 1
    predicted = TABLE[idx]
    print(f"  SN2[{i}]={hex(b)}, {b}>>1={idx}, TABLE[{idx}]='{predicted}'  (P2[{i}]='{P2[i]}')")
    if predicted != '?' and predicted != P2[i]:
        print(f"    → MISMATCH! SN2 does NOT start with HWTC byte {i}={hex(b)}")
    elif predicted == '?':
        print(f"    → Unknown: P2[{i}]='{P2[i]}' tells us TABLE[{idx}]='{P2[i]}'")
    elif predicted == P2[i]:
        print(f"    → Match ✓")

# ── Try to determine what SN2[0..3] bytes produce 'Y','7','.','1' ─────────────
print(f"\n=== What bytes produce P2[0..3] = 'Y', '7', '.', '1'? ===")
for target_char in ['Y', '7', '.', '1']:
    # These are NEW chars, so we learn TABLE[b>>1] = char for those bytes
    print(f"  '{target_char}': must be at some TABLE[k] that's currently '?'")
    unknown_indices = [k for k, t in enumerate(TABLE) if t == '?']
    print(f"    Possible TABLE indices (unknown): {unknown_indices[:10]}...")
    print(f"    Possible byte values: {[k*2 for k in unknown_indices[:5]] + [k*2+1 for k in unknown_indices[:5]]}")

# ── Try known Huawei SN prefixes ─────────────────────────────────────────────
print(f"\n=== Trying other common Huawei SN prefixes ===")
# Common prefixes seen in ONT SNs:
prefixes = {
    'HWTC': bytes([0x48, 0x57, 0x54, 0x43]),
    'HWTD': bytes([0x48, 0x57, 0x54, 0x44]),
    'HWTQ': bytes([0x48, 0x57, 0x54, 0x51]),
    'HWTK': bytes([0x48, 0x57, 0x54, 0x4B]),
    'HW0A': bytes([0x48, 0x57, 0x30, 0x41]),
    # Different vendor IDs
    'ZTEG': bytes([0x5A, 0x54, 0x45, 0x47]),
    'ALCL': bytes([0x41, 0x4C, 0x43, 0x4C]),
}

print("If P2 chars are known from TABLE, we can check prefix compatibility:")
for name, prefix in prefixes.items():
    chars = []
    ok = True
    for b in prefix:
        idx = b >> 1
        c = TABLE[idx]
        chars.append(c)
    print(f"  {name}: bytes={[hex(b) for b in prefix]} → chars={''.join(chars)} (P2[:4]={P2[:4]})")
    if ''.join(c for c in chars if c != '?') and \
       any(c != '?' and c != p for c, p in zip(chars, P2)):
        print(f"    → INCOMPATIBLE (known chars don't match P2)")
    elif all(c == '?' for c in chars):
        print(f"    → Possible (all unknown chars)")
    elif all(c == p or c == '?' for c, p in zip(chars, P2)):
        print(f"    → COMPATIBLE ✓")

print("\n=== Summary of Algorithm ===")
print("""
ALGORITHM: sUser Password = bytes_to_chars(SN + CRC32(SN))

Step 1: Take the 8-byte GPON Serial Number (SN)
Step 2: Compute CRC32 of SN → 4 bytes (big-endian)
Step 3: Concatenate: extended = SN[0..7] + CRC32[0..3]  (12 bytes)
Step 4: For each byte b in extended:
          password_char = TABLE[b >> 1]  (or equivalently TABLE[b // 2])

Where TABLE is a 128-entry lookup table hardcoded in /bin/ssmp.

Known TABLE entries (12 discovered from our device):
  TABLE[3]   = 'R'    (bytes 6,7)
  TABLE[7]   = '9'    (bytes 14,15)
  TABLE[19]  = 'E'    (bytes 38,39)
  TABLE[33]  = '9'    (bytes 66,67)
  TABLE[36]  = 'E'    (bytes 72,73)
  TABLE[42]  = '!'    (bytes 84,85)
  TABLE[43]  = 'P'    (bytes 86,87)
  TABLE[54]  = 'L'    (bytes 108,109)
  TABLE[62]  = '9'    (bytes 124,125)
  TABLE[82]  = 'H'    (bytes 164,165)
  TABLE[98]  = 'H'    (bytes 196,197)
  TABLE[111] = '4'    (bytes 222,223)

To get the FULL TABLE, extract it from /bin/ssmp binary.
Look for a 128-byte or 256-byte data block in the .rodata section.
""")
