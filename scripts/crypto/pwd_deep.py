#!/usr/bin/env python3
"""
Deep dive: Find the exact alphabet mapping from SN+CRC32 bytes to password.

Key insight from phase 1:
  SN1 + CRC32(SN1) = 12 bytes
  Password has 12 chars
  → Each byte maps to exactly ONE character via some alphabet/transform

Our 12 bytes: 48 57 54 43 7C 07 DE A5 6C C5 0F 27
Our password: E  P  !  9  9  R  4  H  L  H  9  E

If byte→char is LOOKUP[byte % N], find N and LOOKUP.
"""

import hashlib, zlib, struct, itertools

P1   = "EP!99R4HLH9E"
SN1  = "485754437C07DEA5"
P2   = "Y7.15R1TLU6?"

sn1_bytes = bytes.fromhex(SN1)
crc1      = zlib.crc32(sn1_bytes) & 0xFFFFFFFF
ext1      = list(sn1_bytes) + list(struct.pack('>I', crc1))
print(f"SN1+CRC32 bytes: {[hex(b) for b in ext1]}")
print(f"Password  chars: {list(P1)}")
print()

# ── Build byte→char mapping ──────────────────────────────────────────────────
mapping = {}
for i, (b, c) in enumerate(zip(ext1, P1)):
    if b in mapping and mapping[b] != c:
        print(f"CONFLICT at pos {i}: byte {hex(b)} mapped to both '{mapping[b]}' and '{c}'")
    mapping[b] = c
print("Byte → Char mapping (SN1+CRC32):")
for b, c in sorted(mapping.items()):
    print(f"  {hex(b):>4} ({b:3d}) → '{c}'  (ASCII {ord(c)})")

# Check conflicts
print()
byte_vals = ext1
char_vals = [ord(c) for c in P1]
print("Looking for arithmetic relationship  byte_val OP offset → char_ASCII:")
for i, (b, c_ascii) in enumerate(zip(byte_vals, char_vals)):
    diff   = c_ascii - b
    ratio  = c_ascii / b if b != 0 else None
    xorval = b ^ c_ascii
    print(f"  pos{i:2d}: byte={b:3d}({hex(b)}) char='{P1[i]}'({c_ascii:3d})  "
          f"diff={diff:4d}  XOR={xorval:3d}({hex(xorval)})")

# ── Check for a fixed XOR key pattern ────────────────────────────────────────
print("\nXOR key bytes:", [b ^ ord(c) for b, c in zip(ext1, P1)])
print("XOR key hex:  ", [hex(b ^ ord(c)) for b, c in zip(ext1, P1)])

# ── Hypothesis: alphabet table indexed by (byte % N) ─────────────────────────
print("\n─── Searching for modular alphabet ───")
# We know: 
#   ext1[5]=0x07=7  → 'R'(82)
#   ext1[8]=0x6C=108 → 'L'(76)
# For BOTH passwords to have the same char at pos 5 and 8,
# the OTHER SN's extended bytes at pos 5,8 must map to the same chars.
# This means either:
#   (a) The SN2_ext bytes at pos5,8 are IDENTICAL to SN1_ext
#   (b) Different bytes, but (byte2 % N) == (byte1 % N), producing same char

# Let's try approach (b): find N where this is consistent
# ext1[5]=7 → 'R' (index R in alphabet)
# ext1[8]=108 → 'L' (index L in alphabet)
# We need an alphabet where ALPHA[7 % N] = 'R' and ALPHA[108 % N] = 'L'

print("Attempting to reconstruct alphabet from known byte→char pairs...")
# All known pairs from password 1:
pairs = list(zip(ext1, P1))
print(f"Known (byte, char) pairs: {[(b, c) for b, c in pairs]}")

# Check if the mapping is consistent (no two same bytes → different chars)
byte_to_char = {}
conflict = False
for b, c in pairs:
    if b in byte_to_char and byte_to_char[b] != c:
        print(f"  CONFLICT: byte {b} → '{byte_to_char[b]}' AND '{c}'")
        conflict = True
    byte_to_char[b] = c
if not conflict:
    print("  No conflicts! Mapping is consistent for P1.")

# ── Try: char = ALPHA[ byte % len(ALPHA) ] ────────────────────────────────────
# Build candidate alphabets and test
# We need ALPHA such that for all (b, c) in pairs: ALPHA[b % len(ALPHA)] == c
# and positions where both passwords agree (pos5=R, pos8=L):
# ext1[5]=7, ext1[8]=108
# If ext2[5] and ext2[8] are unknown, we need:
#   ALPHA[7 % N] = 'R'  and  ALPHA[108 % N] = 'L'

print("\n─── Brute-force alphabet size N ───")
for N in range(10, 100):
    positions = [b % N for b in ext1]
    # Check if any two bytes land on the same position with different chars
    pos_to_char = {}
    ok = True
    for pos, c in zip(positions, P1):
        if pos in pos_to_char and pos_to_char[pos] != c:
            ok = False
            break
        pos_to_char[pos] = c
    if ok:
        # Verify positions for 'R' and 'L'
        r_pos = 7 % N   # ext1[5]=7 → 'R'
        l_pos = 108 % N # ext1[8]=108 → 'L'
        print(f"  N={N:3d}: positions={positions}  R_idx={r_pos}  L_idx={l_pos}  "
              f"chars_at_pos={pos_to_char}")

# ── Try known 40-char Huawei alphabet ─────────────────────────────────────────
print("\n─── Testing known Huawei-style custom alphabets ───")

# Hypothesis: The alphabet is 40 chars and includes uppercase, digits, special
# Let's try all plausible 40-char alphabets that contain the chars we've seen
seen_chars = set(P1 + P2)
# Must include: E,P,!,9,R,4,H,L,Y,7,.,1,5,T,U,6,?
print(f"Chars that must be in alphabet: {''.join(sorted(seen_chars))}")

# Common Huawei special char sets: !@#$%^&*()  or  !.?#@+-
# Let's try specific candidate alphabets
candidate_alphas = [
    # 40 chars
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ!.?@",
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!.?@",
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$",
    # 36 chars
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    # 62 chars
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
    # 64 chars (base64)
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",
    # Custom observed in Huawei research
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef",
]

for alpha in candidate_alphas:
    N = len(alpha)
    result = ''.join(alpha[b % N] for b in ext1)
    match = "✓ MATCH!" if result == P1 else ""
    partial = sum(1 for a, b in zip(result, P1) if a == b)
    if match or partial >= 4:
        print(f"  N={N} alpha='{alpha[:20]}...': {result}  match={partial}/12 {match}")

# ── Try treating the password as a transform of the SN directly ───────────────
print("\n─── Direct SN Transform Test ───")
# What if password chars come from SN nibbles via simple table?
# SN nibbles: 4 8 5 7 5 4 4 3 7 C 0 7 D E A 5  (16 nibbles)
# Password:   E P ! 9 9 R 4 H L H 9 E           (12 chars)
# Group ratio: 16/12 ≈ 1.33 - doesn't divide evenly

# What if we use pairs of nibbles (bytes) but only first 12 bytes of something?
# SN (8 bytes) + HMAC(SN, fixed_key)[0:4] = 12 bytes?
fixed_keys = [b"Huawei", b"HWTC", b"huawei", b"HG8245", b"ONT", b"\x00"*16]
for key in fixed_keys:
    import hmac as hmac_mod
    h = hmac_mod.new(key, sn1_bytes, hashlib.sha256).digest()[:4]
    ext_hmac = list(sn1_bytes) + list(h)
    # Try various alphabets
    for alpha in ["0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ!.?@", 
                   "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!.?@"]:
        N = len(alpha)
        result = ''.join(alpha[b % N] for b in ext_hmac)
        if result == P1:
            print(f"  MATCH! key={key} alpha={alpha}: {result}")
        elif sum(1 for a,b in zip(result,P1) if a==b) >= 6:
            print(f"  CLOSE ({sum(1 for a,b in zip(result,P1) if a==b)}/12) "
                  f"key={key} alpha={alpha[:15]}: {result}")

print("\n─── Testing SN nibble→char via 16-entry table ───")
# SN has 16 nibbles. Password has 12 chars.
# Maybe: take every 4th nibble out of 16? Like positions 0,1,3,5,6,7,9,11,12,13,14,15?
# Or: group nibbles differently
# Try: take 6-bit groups from SN (raw 64-bit integer → 10.67 6-bit groups)
# Supplement with CRC to get 12 groups
sn_int = int(SN1, 16)
crc_int = crc1
combined_int = (sn_int << 32) | crc_int  # 96 bits
print(f"SN+CRC (96 bits): {hex(combined_int)}")

# Extract 12 groups of 6 bits:
groups_6bit = [(combined_int >> (90 - i*6)) & 0x3F for i in range(16)]
print(f"6-bit groups (16): {groups_6bit}")
groups_12 = groups_6bit[:12]
print(f"6-bit groups (12): {groups_12}")

# Test with custom alphabets
for alpha in [
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ!.?@",
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!.?@",
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^",
]:
    result = ''.join(alpha[g % len(alpha)] for g in groups_12)
    match = "✓ MATCH!" if result == P1 else ""
    partial = sum(1 for a, b in zip(result, P1) if a == b)
    if match or partial >= 4:
        print(f"  6bit+alpha({len(alpha)}): {result}  {partial}/12 {match}")
