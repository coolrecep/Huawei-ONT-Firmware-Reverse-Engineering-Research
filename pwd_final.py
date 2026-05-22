#!/usr/bin/env python3
"""
Final approach: 
1. Extract the password generation function from /bin/ssmp on the router
2. Also: brute-force SN2 given P2 constraints + N=29 partial alphabet

Key confirmed facts:
- Algorithm: SN (8 bytes) + CRC32(SN) (4 bytes) = 12 bytes
- Each byte → char via ALPHA[byte % 29]
- CRC1[0]=108, 108%29=21='L' ✓ confirmed
- SN1[5]=7,    7%29=7='R'   ✓ confirmed

Partial alphabet (N=29):
  slots: 0=P, 7=R, 8=9, 9=9, 10=E, 14=E, 15=9, 19=4, 20=H, 21=L, 23=H, 26=!
  unknown: 1,2,3,4,5,6,11,12,13,16,17,18,22,24,25,27,28

Now from P2="Y7.15R1TLU6?":
  P2[5]='R' → SN2[5] % 29 = 7
  P2[8]='L' → CRC2[0] % 29 = 21
  
  P2[0]='Y', P2[1]='7', P2[2]='.', P2[3]='1', P2[4]='5', 
  P2[6]='1', P2[7]='T', P2[9]='U', P2[10]='6', P2[11]='?'
  → All new chars occupy unknown alphabet slots

Let's use P2 to fill in more of the alphabet,
then verify consistency.
"""

import zlib, struct, hashlib

P1  = "EP!99R4HLH9E"
SN1 = "485754437C07DEA5"
P2  = "Y7.15R1TLU6?"

N = 29
sn1_bytes = bytes.fromhex(SN1)
crc1      = zlib.crc32(sn1_bytes) & 0xFFFFFFFF
ext1      = list(sn1_bytes) + list(struct.pack('>I', crc1))

# Build partial alphabet from P1
alpha = [None] * N
for b, c in zip(ext1, P1):
    alpha[b % N] = c

print("=== Confirmed Algorithm: SN(8) + CRC32(SN)(4) → ALPHA[byte%29] ===\n")
print(f"SN1    = {SN1}")
print(f"CRC32  = {hex(crc1)}")
print(f"Ext1   = {[hex(b) for b in ext1]}")
print(f"Slots  = {[b%N for b in ext1]}")
print(f"P1     = {P1}  [CONFIRMED]")

# ── Try to brute-force SN2 ────────────────────────────────────────────────────
# SN2 is 8 bytes. First 4 bytes are vendor ID.
# From P2, SN2[5] % 29 = 7 → SN2[5] ∈ {7,36,65,94,123,152,181,210,239}
# CRC2[0] % 29 = 21 → the CRC32 of SN2 must have first byte ≡ 21 (mod 29)

# Strategy: 
# - P2[0..3] → SN2[0..3]: these bytes must produce 'Y','7','.','1' via alpha
# - 'Y','7','.','1' are in unknown slots, so SN2[0..3] % 29 must be unknown slots
# - P2[4] = '5' → SN2[4] % 29 must be an unknown slot
# - P2[6] = '1' → SN2[6] % 29 must map to same char as P2[3]='1' or same slot
# - etc.

# The characters '1' appears twice in P2 (pos 3 and pos 6):
# → ALPHA[SN2[3] % 29] = '1' and ALPHA[SN2[6] % 29] = '1'
# → SN2[3] % 29 == SN2[6] % 29  (they must be in the same slot, or both map to '1')
# This is a strong constraint!

print("\n=== P2 Repeated Char Constraints ===")
char_positions = {}
for i, c in enumerate(P2):
    char_positions.setdefault(c, []).append(i)
for c, positions in char_positions.items():
    if len(positions) > 1:
        print(f"  '{c}' at positions {positions} → all must map to same slot")
        print(f"  Constraint: SN2_ext[{positions}] all ≡ X (mod 29) for some X")

# '1' appears at positions 3 and 6: SN2[3] % 29 == SN2[6] % 29
# Since SN2[3] and SN2[6] are both in the SN (not CRC32 part):
# SN2_byte3 % 29 == SN2_byte6 % 29
# SN2_byte3 and SN2_byte6 have the same remainder mod 29

print("\n=== Attempting SN2 Recovery via Constraint Solving ===")

# For a Huawei ONT SN: likely starts with 4-byte vendor code
# Common vendors: HWTC, ZTEG, ALCL, etc.
# We showed HWTC gives wrong P2[0..3], so vendor might be different

# Let's approach differently: the NEW chars in P2 define new alphabet slots.
# P2[0]='Y' → slot = SN2[0] % 29 (some unknown slot, call it s0)
# P2[1]='7' → slot = SN2[1] % 29 (call it s1)
# ...
# Since all new chars are in different (unknown) slots, the algorithm is:
# Find any 8-byte SN2 that:
#   1. SN2[5] % 29 = 7
#   2. CRC32(SN2)[0] % 29 = 21 (for 'L' at position 8)
#   3. The assigned slots for positions 0,1,2,3,4,6,7 (from SN2) and 9,10,11 (from CRC2)
#      are all UNASSIGNED slots in the partial alphabet
#   4. Repeated chars produce the same slot

# This is still under-constrained. Let's try to find SN2 by scanning
# with known constraints.

# From the analysis, both passwords share:
# - 'R' at pos 5 (from SN[5] ≡ 7 mod 29)
# - 'L' at pos 8 (from CRC[0] ≡ 21 mod 29)

# Let's verify our N=29 hypothesis with a known mapping and see if the full
# alphabet can be recovered.

# First, let's check what a complete N=29 alphabet might look like
# that is consistent with known Huawei character sets

# The chars used so far: P, R, 9, E, 4, H, L, ! (from P1)
#                        Y, 7, ., 1, 5, T, U, 6, ? (from P2)
# Total unique: 17 chars for 29 slots → 12 slots still completely unknown

# Try candidate complete alphabets of length 29
# A natural 29-char set might be:
# A-Z (26) + 3 special chars: !, ., ?
# or digits (0-9) + letters (19) = 29
# or some other mix

candidates_29 = [
    # Uppercase + 3 specials
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ!.?",
    "0123456789ABCDEFGHIJKLMNOPQRS",
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ012",
    "!.?0123456789ABCDEFGHIJKLMNOP",
    "0123456789ABCDEFGHIJKLMNOP!.?",
]

print("\n=== Testing candidate N=29 alphabets ===")
for alpha_try in candidates_29:
    if len(alpha_try) != 29:
        continue
    # Check consistency with P1
    result = ''.join(alpha_try[b % 29] for b in ext1)
    match1 = result == P1
    
    # Check partial consistency (assigned slots)
    consistent = True
    for b, c in zip(ext1, P1):
        if alpha_try[b % 29] != c:
            consistent = False
            break
    
    # Check P2 constraints (positions 5 and 8)
    # For P2: pos5='R' → alpha_try[7]='R', pos8='L' → alpha_try[21]='L'
    r_ok = alpha_try[7] == 'R'
    l_ok = alpha_try[21] == 'L'
    
    if consistent:
        print(f"  '{alpha_try}': P1={result}  MATCH={'✓' if match1 else '✗'}  R={r_ok} L={l_ok}")

# The real alphabet likely follows a specific Huawei ordering
# Let's try: What if it's ASCII-ordered chars that Huawei chose?
# Observed chars sorted by ASCII: ! (33) . (46) 1 4 5 6 7 9 E H L P R T U Y ? (63)
# The '?' (63) comes last! This suggests the alphabet might be ASCII-ordered.
print("\n=== Testing ASCII-ordered N=29 alphabet ===")
# All printable non-space, non-lowercase chars? Let's try
# What 29 chars make sense for a password that includes !, ., ?, digits, uppercase?
import string
possible_chars = string.digits + string.ascii_uppercase + "!.?@#$"
print(f"Full candidate pool: {possible_chars}")

# The assignment we know:
# slot 0  → 'P'
# slot 7  → 'R'
# slot 8  → '9' (digit)
# slot 9  → '9' (digit)  
# slot 10 → 'E'
# slot 14 → 'E'  ← same char at two slots! This means the alphabet can repeat chars
# slot 15 → '9'
# slot 19 → '4'
# slot 20 → 'H'
# slot 21 → 'L'
# slot 23 → 'H'  ← 'H' at slots 20 and 23!
# slot 26 → '!'

# Multiple slots can map to the same char! This means the alphabet is NOT injective.
# This is unusual for a password scheme but possible.

print("\n=== Repeated char at slots! (alphabet is NOT injective) ===")
print("Slot 8 and 9 both = '9'")
print("Slot 10 and 14 both = 'E'")
print("Slot 20 and 23 both = 'H'")
print()
print("This means the 'alphabet' is not a simple mapping - it likely uses a")
print("DIFFERENT formula: the result depends on the byte value, not just (byte % N)")
print()

# Wait - let me reconsider. What if N is NOT 29?
# Multiple same chars at different slots could mean the modulus is wrong.
# Let me re-examine: maybe the character IS directly from the byte value
# via a lookup table where multiple entries map to the same char.

# Actually, looking at the bytes that map to the same char:
# 'E': bytes 72 (pos0) and 39 (pos11)
# '9': bytes 67 (pos3), 124 (pos4), 15 (pos10)
# 'H': bytes 165 (pos7) and 197 (pos9)
print("Bytes mapping to same char:")
print(f"  'E': bytes {[b for b,c in zip(ext1,P1) if c=='E']} (decimal)")
print(f"  '9': bytes {[b for b,c in zip(ext1,P1) if c=='9']} (decimal)")
print(f"  'H': bytes {[b for b,c in zip(ext1,P1) if c=='H']} (decimal)")

# For 'E': 72 and 39 → diff = 33. LCM(33,29)=... 33 = 3×11
# For '9': 67, 124, 15 → 67-15=52, 124-67=57, 124-15=109
# For 'H': 165-197 = -32, abs=32

# Modular check: for 'E' at bytes 72 and 39:
for N_test in [11, 29, 33, 36, 40, 44]:
    if (72 % N_test) == (39 % N_test):
        print(f"  N={N_test}: 72≡39 (mod {N_test}) ✓ for 'E'")

print()
for N_test in range(5, 100):
    # Check if ALL same-char bytes are congruent:
    e_bytes = [72, 39]
    nine_bytes = [67, 124, 15]
    h_bytes = [165, 197]
    
    e_ok = len(set(b % N_test for b in e_bytes)) == 1
    nine_ok = len(set(b % N_test for b in nine_bytes)) == 1
    h_ok = len(set(b % N_test for b in h_bytes)) == 1
    
    if e_ok and nine_ok and h_ok:
        # Verify no different-char bytes land on same slot
        slots = [b % N_test for b in ext1]
        slot_to_char = {}
        conflict = False
        for slot, c in zip(slots, P1):
            if slot in slot_to_char and slot_to_char[slot] != c:
                conflict = True
                break
            slot_to_char[slot] = c
        if not conflict:
            print(f"  N={N_test}: All same-char bytes congruent, no conflicts! ✓ VALID!")
            print(f"    Positions: {slots}")
            print(f"    Slot map: {slot_to_char}")
