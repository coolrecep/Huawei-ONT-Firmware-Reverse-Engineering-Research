#!/usr/bin/env python3
"""
Phase 3: Reconstruct the N=29 alphabet from P1 and validate/predict P2.
Also try to identify the second router's SN.

N=29 positions for SN1+CRC32:
  byte 72 → pos 14 → 'E'
  byte 87 → pos  0 → 'P'
  byte 84 → pos 26 → '!'
  byte 67 → pos  9 → '9'
  byte124 → pos  8 → '9'
  byte  7 → pos  7 → 'R'
  byte222 → pos 19 → '4'
  byte165 → pos 20 → 'H'   (note: 165%29=20)
  byte108 → pos 21 → 'L'
  byte197 → pos 23 → 'H'   (note: 197%29=23)
  byte 15 → pos 15 → '9'
  byte 39 → pos 10 → 'E'

Partial alphabet (29 slots, partially known):
slot 0  → 'P'
slot 7  → 'R'
slot 8  → '9'
slot 9  → '9'  ← conflict! both 8 and 9 map to '9'? Wait that's OK since two different
                  positions both give '9'. The alphabet slot 8 = '9' and slot 9 = '9'.
slot 10 → 'E'
slot 14 → 'E'  ← conflict? slots 10 and 14 both = 'E'. Also OK, two slots can have same char.
slot 15 → '9'
slot 19 → '4'
slot 20 → 'H'
slot 21 → 'L'
slot 23 → 'H'
slot 26 → '!'
"""

import zlib, struct

P1  = "EP!99R4HLH9E"
SN1 = "485754437C07DEA5"
P2  = "Y7.15R1TLU6?"

sn1_bytes = bytes.fromhex(SN1)
crc1      = zlib.crc32(sn1_bytes) & 0xFFFFFFFF
ext1      = list(sn1_bytes) + list(struct.pack('>I', crc1))

N = 29
positions1 = [b % N for b in ext1]
print(f"N=29 positions for SN1+CRC32: {positions1}")
print(f"Password P1:                   {list(P1)}")

# Build the partial alphabet for N=29
alpha = ['_'] * N  # underscore = unknown
for pos, c in zip(positions1, P1):
    if alpha[pos] != '_' and alpha[pos] != c:
        print(f"CONFLICT: slot {pos} = '{alpha[pos]}' vs '{c}'")
    alpha[pos] = c
print(f"\nPartial N=29 alphabet:")
for i, a in enumerate(alpha):
    print(f"  slot {i:2d} → '{a}'")

# ── Now use P2 to get MORE alphabet entries ─────────────────────────────────
# We need the SN2 (and thus ext2) that produced P2="Y7.15R1TLU6?"
# We know P2[5]='R' → ext2[5] % 29 = 7  (since slot 7 = 'R')
# We know P2[8]='L' → ext2[8] % 29 = 21 (since slot 21 = 'L')
# This is consistent with any byte b where b%29=7 (i.e. b ∈ {7,36,65,94,123,152,...})
# and b%29=21 (i.e. b ∈ {21,50,79,108,137,166,195,224,...})

# From P2, find what positions these chars would be at:
print(f"\n── P2 position analysis (N=29 alphabet) ──")
print(f"P2: {P2}")
print(f"For each char in P2, what slot in the N=29 alphabet?")
for i, c in enumerate(P2):
    # Which slots have this char?
    slots_with_c = [j for j, a in enumerate(alpha) if a == c]
    print(f"  P2[{i}]='{c}': known slots = {slots_with_c}")
    if slots_with_c:
        # The SN2_ext[i] must satisfy SN2_ext[i] % 29 in slots_with_c
        # i.e. SN2_ext[i] % 29 ∈ slots_with_c
        print(f"    → SN2_ext[{i}] % 29 must be one of {slots_with_c}")
        # Possible byte values (0-255):
        possible = [b for b in range(256) if b % N in slots_with_c]
        print(f"    → Possible byte values (0-255): {possible[:15]}...")

# ── Fill in more alphabet slots using P2 ────────────────────────────────────
print(f"\n── Inferring more alphabet slots from P2 ──")
# P2 unique chars not yet in alphabet:
p2_new = set(P2) - set(P1)
print(f"New chars in P2 not in P1: {p2_new}")
# These chars ('Y', '7', '.', '1', '5', 'T', 'U', '6', '?') must occupy
# slots in the N=29 alphabet that aren't yet assigned.
unassigned = [i for i, a in enumerate(alpha) if a == '_']
print(f"Unassigned alphabet slots: {unassigned}")

# From P2, the positions that produce NEW chars tell us which SN2_ext byte
# maps to which slot. But we don't know SN2_ext yet.
# However, if we can guess SN2 format: it should be another Huawei GPON SN
# starting with HWTC = 48 57 54 43

# Hypothesis: SN2 starts with HWTC (same as SN1)
# SN2_bytes[0..3] = 48 57 54 43 (same as SN1)
# So ext2[0..3] ≡ ext1[0..3] (mod 29) → same positions: [14, 0, 26, 9]
# P2[0..3] = 'Y', '7', '.', '1'
# But ext1[0..3] → P1[0..3] = 'E', 'P', '!', '9' via slots [14, 0, 26, 9]
# So if SN2 also starts with HWTC: P2[0..3] should also be 'E', 'P', '!', '9'
# But P2[0..3] = 'Y', '7', '.', '1' -- DIFFERENT!
# → SN2 does NOT start with HWTC! (or CRC changes it)

# Wait: ext = SN (8 bytes) + CRC32 (4 bytes)
# If SN2 starts with HWTC, ext2[0]=72, ext2[1]=87, ext2[2]=84, ext2[3]=67
# → P2[0] should be ALPHA[72%29]=ALPHA[14]='E'
# But P2[0]='Y' ≠ 'E'
# → Either SN2 doesn't start with HWTC, or the hypothesis is wrong.

print("\n── Testing if SN2 starts with HWTC ──")
HWTC = bytes([0x48, 0x57, 0x54, 0x43])
print(f"If SN2 starts with HWTC:")
print(f"  ext2[0]=72 → slot {72%N} → '{alpha[72%N]}' (P2[0]='{P2[0]}')")
print(f"  ext2[1]=87 → slot {87%N} → '{alpha[87%N]}' (P2[1]='{P2[1]}')")
print(f"  ext2[2]=84 → slot {84%N} → '{alpha[84%N]}' (P2[2]='{P2[2]}')")
print(f"  ext2[3]=67 → slot {67%N} → '{alpha[67%N]}' (P2[3]='{P2[3]}')")
# This would only work if slot values match P2 chars

# ── Try alternative: different Huawei OUI prefix ──────────────────────────────
# Some Huawei ONTs have different OUI: e.g. HWTC, HWTI, HWTS, etc.
# Or the SN could start with different bytes
print("\n── Finding SN2 bytes that produce P2 ──")
print("For each P2 position, find possible byte values:")
for i, c in enumerate(P2):
    # What slot must ext2[i] % 29 be?
    target_slots = [j for j, a in enumerate(alpha) if a == c]
    if target_slots:
        possible_bytes = [b for b in range(256) if b % N in target_slots]
    else:
        # c is not yet in alphabet - it could be in any unassigned slot
        possible_bytes = [b for b in range(256) if b % N in unassigned]
        print(f"  P2[{i}]='{c}': NEW char, SN2_ext[{i}] ∈ {possible_bytes[:10]}...")
        continue
    print(f"  P2[{i}]='{c}': SN2_ext[{i}] ∈ {possible_bytes[:12]}... ({len(possible_bytes)} total)")

# ── Try the most likely SN2 structure ─────────────────────────────────────────
# Huawei SN format: [vendor_id: 4 bytes][unique: 4 bytes]
# Known vendor IDs that are 4 hex char pairs:
# HWTC = 48 57 54 43
# ALCS = 41 4C 43 53
# etc.
# OR the SN might be in a different format for this specific router

print("\n── Attempt to reconstruct SN2 from P2 constraints ──")
print("Finding bytes b[0..7] for SN2 (8 bytes) such that (SN2+CRC32) maps to P2")
print("This requires iterating... trying HWTC prefix first")

import zlib

def try_sn2(sn2_bytes):
    """Check if sn2_bytes produces P2 with N=29 alphabet."""
    crc = zlib.crc32(sn2_bytes) & 0xFFFFFFFF
    ext = list(sn2_bytes) + list(struct.pack('>I', crc))
    result = []
    for b in ext:
        slot = b % N
        if slot < len(alpha):
            result.append(alpha[slot])
        else:
            result.append('?')
    return ''.join(result)

# Check if any standard prefix works
for prefix_name, prefix_bytes in [
    ("HWTC", bytes([0x48, 0x57, 0x54, 0x43])),
    ("HW",   bytes([0x48, 0x57, 0x00, 0x00])),
    ("ALCS", bytes([0x41, 0x4C, 0x43, 0x53])),
]:
    # For the first 4 bytes of SN2 = prefix_bytes,
    # check what ext2[0..3] % 29 gives us
    slots_prefix = [b % N for b in prefix_bytes]
    chars_prefix = [alpha[s] for s in slots_prefix]
    print(f"  Prefix {prefix_name}: slots={slots_prefix} → chars={''.join(chars_prefix)} (P2[:4]={P2[:4]})")

# ── The key insight: P2 may have 'R' at pos5 from a DIFFERENT mechanism ───────
print("\n── Alternative: 'R' and 'L' at fixed positions may come from")
print("   the CRC32 bytes, not the SN bytes ──")
# ext = SN(8 bytes) + CRC32(4 bytes)
# Position 5 comes from SN[5] (6th byte of SN, 0-indexed)
# Position 8 comes from CRC32[0] (first byte of CRC32)
# If CRC32[0] % 29 = 21 ('L') for BOTH devices,
# that means crc1[0] and crc2[0] both ≡ 21 (mod 29)
# crc1[0] = 0x6C = 108, 108 % 29 = 108 - 3*29 = 108-87 = 21 ✓
# So for P2[8]='L', we need: crc2[0] % 29 = 21
# Possible CRC first bytes: 21, 50, 79, 108, 137, 166, 195, 224
print(f"  CRC1[0] = {ext1[8]} ({ext1[8]}), {ext1[8]} % 29 = {ext1[8] % 29} (should be 21 for 'L')")
print(f"  For any SN2, need CRC2[0] % 29 = 21")
print(f"  Possible CRC2[0] values: {[b for b in range(256) if b%29==21]}")

# For P2[5]='R': SN2[5] % 29 = 7
# SN[5] is the 6th byte of SN (unique part byte 2)
# Possible SN2[5] values: 7, 36, 65, 94, 123, 152, 181, 210, 239
print(f"  For P2[5]='R': SN2[5] % 29 = 7")
print(f"  Possible SN2[5] values: {[b for b in range(256) if b%29==7]}")
print(f"  SN1[5] = {sn1_bytes[5]} ({hex(sn1_bytes[5])}), {sn1_bytes[5]} % 29 = {sn1_bytes[5] % 29}")
