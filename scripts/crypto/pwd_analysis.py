#!/usr/bin/env python3
"""
Huawei HG8245X6 - sUser Password Generation Analysis
Passwords to correlate:
  EP!99R4HLH9E  -> SN: 485754437C07DEA5 (our device)
  Y7.15R1TLU6?  -> SN: unknown (another device)

Key observations:
  - Both are exactly 12 characters
  - Both have 'R' at position 5
  - Both have 'L' at position 8
  - Position 2 always has a special char (! or .)
"""

import hashlib, struct, binascii, itertools

TARGET_PWD  = "EP!99R4HLH9E"
TARGET_SN   = "485754437C07DEA5"
SECOND_PWD  = "Y7.15R1TLU6?"

# ─── Observation helpers ────────────────────────────────────────────────────
def analyze_passwords():
    print("=== Password Pattern Analysis ===")
    p1, p2 = TARGET_PWD, SECOND_PWD
    print(f"P1: {p1}  len={len(p1)}")
    print(f"P2: {p2}  len={len(p2)}")
    print()
    print("Pos | P1  | P2  | Match")
    print("----|-----|-----|------")
    for i, (a, b) in enumerate(zip(p1, p2)):
        mark = "✓ SAME" if a == b else ""
        print(f" {i:2d} |  {a}  |  {b}  | {mark}")
    
    print()
    char_types = lambda c: 'DIGIT' if c.isdigit() else ('UPPER' if c.isupper() else 'SPECIAL')
    print("Pos | P1  | Type P1   | P2  | Type P2")
    for i, (a, b) in enumerate(zip(p1, p2)):
        print(f" {i:2d} |  {a}  | {char_types(a):<9}|  {b}  | {char_types(b)}")

# ─── Character set discovery ────────────────────────────────────────────────
def find_alphabet():
    """What alphabet would map SN bytes to the password?"""
    print("\n=== Possible Alphabet Detection ===")
    # Both passwords, all unique chars sorted by ASCII
    all_chars = set(TARGET_PWD + SECOND_PWD)
    print(f"All chars used: {''.join(sorted(all_chars))}")
    print(f"Count: {len(all_chars)}")
    print(f"ASCII values: {[ord(c) for c in sorted(all_chars)]}")

# ─── Hash-based approaches ──────────────────────────────────────────────────
def try_hash_approaches():
    print("\n=== Hash-Based Approach Tests ===")
    sn_bytes = bytes.fromhex(TARGET_SN)
    sn_str   = TARGET_SN.encode()

    # Known Huawei custom Base-N alphabets seen in firmware research
    alphabets = {
        "B64std":    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",
        "B64url":    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_",
        # Huawei uses uppercase-only alphanumeric + some special chars
        "HW_upper":  "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()?.",
        "HW_upper2": "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!.?#@",
        "custom32":  "ABCDEFGHIJKLMNOPQRSTUVWXYZ012345",
        "base36":    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    }

    hash_funcs = {
        "MD5_hexstr": hashlib.md5(sn_str).digest(),
        "MD5_bytes":  hashlib.md5(sn_bytes).digest(),
        "SHA1_hex":   hashlib.sha1(sn_str).digest(),
        "SHA1_bytes": hashlib.sha1(sn_bytes).digest(),
        "SHA256_hex": hashlib.sha256(sn_str).digest(),
        "SHA256_bytes": hashlib.sha256(sn_bytes).digest(),
    }

    def encode_hash(digest, alphabet, length=12):
        """Encode digest bytes using the given alphabet, taking `length` chars."""
        n = len(alphabet)
        result = []
        # Method 1: nibble-based
        for i in range(length):
            byte_idx = i * len(digest) // length
            result.append(alphabet[digest[byte_idx] % n])
        return ''.join(result)

    def encode_hash_6bit(digest, alphabet):
        """6-bit groups from digest bytes → alphabet chars."""
        bits = int.from_bytes(digest, 'big')
        total_bits = len(digest) * 8
        result = []
        n = len(alphabet)
        used = 0
        while len(result) < 12 and used + 6 <= total_bits:
            val = (bits >> (total_bits - used - 6)) & 0x3F
            result.append(alphabet[val % n])
            used += 6
        return ''.join(result[:12])

    for hname, digest in hash_funcs.items():
        for aname, alpha in alphabets.items():
            attempt = encode_hash_6bit(digest, alpha)
            match = "✓ MATCH!" if attempt == TARGET_PWD else ""
            if match or attempt[:4] == TARGET_PWD[:4]:
                print(f"{hname} + {aname}: {attempt} {match}")

# ─── XOR/nibble approaches ──────────────────────────────────────────────────
def try_nibble_mapping():
    print("\n=== Nibble/Byte Mapping ===")
    sn = TARGET_SN  # 16 hex chars = 16 nibbles
    pwd = TARGET_PWD  # 12 chars

    print(f"SN nibbles: {' '.join(sn)}")
    print(f"Password:   {' '.join(pwd)}")
    
    # Try: 16 SN nibbles → 12 pwd chars via grouping
    # Each nibble = 4 bits; 16 nibbles = 64 bits; 12 chars need ~72 bits
    # Try taking 5 bits per char:
    sn_int = int(TARGET_SN, 16)
    print(f"\nSN as integer: {sn_int}")
    
    # 5-bit encoding (like base32)
    base32_alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    result = []
    tmp = sn_int
    for _ in range(12):
        result.append(base32_alpha[tmp & 0x1F])
        tmp >>= 5
    print(f"5-bit (reverse): {''.join(reversed(result))}")
    
    result2 = []
    tmp2 = sn_int
    shift = 64 - 5
    for _ in range(12):
        val = (sn_int >> max(0, shift)) & 0x1F
        result2.append(base32_alpha[val])
        shift -= 5
    print(f"5-bit (forward): {''.join(result2)}")

# ─── Pattern analysis: reverse-engineer the alphabet ─────────────────────────
def reverse_engineer():
    print("\n=== Reverse-Engineer Alphabet from Both Passwords ===")
    p1, p2 = TARGET_PWD, SECOND_PWD
    
    # We have 2 passwords of length 12
    # If same algorithm: password[i] = ALPHA[f(SN)[i] % len(ALPHA)]
    # For positions where chars match (pos 5='R', pos 8='L'):
    # These positions produce the SAME output for BOTH SNs
    # => f(SN1)[i] % N == f(SN2)[i] % N
    # If using a hash, this means hash bytes at those positions are equal mod N
    # This is more likely if f = identity (direct SN bytes), and those SN bytes
    # happen to be equal at those positions.
    
    # Hypothesis: The algorithm uses the SN bytes directly (no hash)
    # and the two SNs share bytes at positions 5 and 8.
    sn1 = bytes.fromhex(TARGET_SN)  # 8 bytes
    print(f"SN1 bytes: {[hex(b) for b in sn1]}")
    print(f"SN1[5]={hex(sn1[5])}, SN1[8 mod 8]={hex(sn1[0])}")  # index wraps
    
    # Hypothesis 2: Use 12 bytes derived from SN somehow (e.g. SN + checksum)
    # Common extension: SN (8 bytes) + CRC32 (4 bytes) = 12 bytes → 12 chars
    import zlib
    sn_crc = zlib.crc32(sn1) & 0xFFFFFFFF
    extended = list(sn1) + list(struct.pack('>I', sn_crc))
    print(f"\nSN + CRC32 extension: {[hex(b) for b in extended]}")
    print(f"Length: {len(extended)} bytes → could map to {len(extended)} chars")
    
    # Now, if char = ALPHA[byte % N], find what ALPHA must be:
    # For P1: each byte mod N must produce the correct char index
    # For chars 'R' (pos5) and 'L' (pos8), we need:
    # extended_sn1[5] mod N → index_of_R in ALPHA
    # extended_sn1[8] mod N → index_of_L in ALPHA
    
    print(f"\nByte at pos 5: {hex(extended[5])} = {extended[5]}")
    print(f"Byte at pos 8: {hex(extended[8])} = {extended[8]}")
    print(f"'R' = {ord('R')}, 'L' = {ord('L')}")
    
    # If byte value IS the ASCII code: extended[5]==82 would mean ALPHA[82%N]='R'
    # extended[5] = sn_crc bytes...
    
    # Simplest hypothesis: byte % 256 → direct ASCII with some offset/XOR key
    # Find XOR key: key[i] = byte[i] XOR ord(pwd[i])
    print("\nXOR key if password = SN_extended XOR key:")
    for i, (b, c) in enumerate(zip(extended, TARGET_PWD)):
        key_byte = b ^ ord(c)
        print(f"  pos{i}: {hex(b)} XOR '{c}'({ord(c)}) = {hex(key_byte)} = {key_byte}")

# ─── Try known Huawei algorithms ─────────────────────────────────────────────
def try_huawei_known():
    print("\n=== Known Huawei Password Patterns ===")
    
    # Pattern 1: Last 4 bytes of SN hex-encoded with substitution
    sn_last4 = TARGET_SN[-8:]  # "7C07DEA5"
    print(f"Last 4 bytes hex: {sn_last4}")
    
    # Pattern 2: SN bytes CRC16
    sn_bytes = bytes.fromhex(TARGET_SN)
    
    # Pattern 3: Check if password chars relate to SN nibbles via simple table
    # Build table: nibble → what char?
    # SN: 4 8 5 7 5 4 4 3 7 C 0 7 D E A 5
    # pwd:E P ! 9 9 R 4 H L H 9 E  (12 chars for 16 nibbles - doesn't map 1:1)
    
    # Pattern 4: SN bytes → decimal → some transform
    sn_dec = [b for b in sn_bytes]
    print(f"\nSN bytes decimal: {sn_dec}")
    
    # Each byte mod various numbers:
    for mod in [26, 36, 40, 62, 64]:
        vals = [b % mod for b in sn_dec]
        print(f"  mod {mod}: {vals}")
    
    # Pattern 5: Known Huawei telecomadmin algo variant
    # Some models: password = encode(sha256(mac_address)[0:9])
    # Try with MAC 90:16:BA:52:75:6F
    mac = bytes.fromhex("9016BA52756F")
    mac_sha256 = hashlib.sha256(mac).digest()
    
    # Custom B62 alphabet (commonly used in Huawei)
    B62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    val = int.from_bytes(mac_sha256[:9], 'big')
    result = []
    while val and len(result) < 12:
        result.append(B62[val % 62])
        val //= 62
    print(f"\nBase62(SHA256(MAC)[0:9]) = {''.join(reversed(result[:12]))}")
    
    # Pattern 6: SN-based, similar encoding
    sn_sha256 = hashlib.sha256(sn_bytes).digest()
    val2 = int.from_bytes(sn_sha256[:9], 'big')
    result2 = []
    while val2 and len(result2) < 12:
        result2.append(B62[val2 % 62])
        val2 //= 62
    print(f"Base62(SHA256(SN_bytes)[0:9]) = {''.join(reversed(result2[:12]))}")

# ─── Character frequency analysis ─────────────────────────────────────────────
def char_frequency():
    print("\n=== Character Frequency & Position Analysis ===")
    p1, p2 = TARGET_PWD, SECOND_PWD
    
    # Special chars are at specific position types
    specials = [c for c in p1+p2 if not c.isalnum()]
    print(f"Special chars found: {set(specials)}")
    
    # Check if position 2 special is always there
    print(f"P1[2]={p1[2]} (special={not p1[2].isalnum()})")
    print(f"P2[2]={p2[2]} (special={not p2[2].isalnum()})")
    
    # Position pattern types
    pattern1 = ''.join('D' if c.isdigit() else 'U' if c.isupper() else 'S' for c in p1)
    pattern2 = ''.join('D' if c.isdigit() else 'U' if c.isupper() else 'S' for c in p2)
    print(f"\nP1 type pattern: {pattern1}")
    print(f"P2 type pattern: {pattern2}")
    print(f"Common pattern:  {''.join(a if a==b else '?' for a,b in zip(pattern1,pattern2))}")

# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    analyze_passwords()
    find_alphabet()
    char_frequency()
    reverse_engineer()
    try_nibble_mapping()
    try_hash_approaches()
    try_huawei_known()
    
    print("\n=== Summary ===")
    print(f"Known: P1={TARGET_PWD}  SN={TARGET_SN}")
    print(f"Known: P2={SECOND_PWD}  SN=???")
    print("Shared fixed positions: [5]='R', [8]='L'")
    print("Shared structure: pos[2]=SPECIAL, pos[5]='R', pos[8]='L'")
    print("Hypothesis: XOR-based with fixed key, or")
    print("            custom base-N encoding of SN+CRC32 with Huawei alphabet")
