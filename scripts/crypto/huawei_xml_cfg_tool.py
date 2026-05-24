#!/usr/bin/env python3
"""
Huawei ONT Configuration and Password Cryptographic Utility

Replicates the functionality of huaweiXML_CFG.exe:
1. Configuration File Decryption (AES-256-CBC with dynamic key derivation + GZIP decompression)
2. Configuration File Encryption (AES-256-CBC with custom CRC-32 + GZIP compression)
3. Text Password Decryption Mode 1 ($1...$) - AES-256-ECB with block-dynamic key derivation
4. Text Password Decryption Mode 2 ($2...$) - AES-256-CBC
5. Text Password Decryption Mode 3 (de_su)   - Custom MD5-based superuser password generation
"""

import sys
import os
import argparse
import hashlib
import hmac
import gzip
import html
from Crypto.Cipher import AES

# Custom CRC-32 table extracted from huaweiXML_CFG.exe (virtual address 0xeb7640)
# This is a standard MSB-first CRC-32 table (polynomial 0x04C11DB7)
CRC_TABLE = [
    0x00000000, 0x04c11db7, 0x09823b6e, 0x0d4326d9, 0x130476dc, 0x17c56b6b, 0x1a864db2, 0x1e475005,
    0x2608edb8, 0x22c9f00f, 0x2f8ad6d6, 0x2b4bcb61, 0x350c9b64, 0x31cd86d3, 0x3c8ea00a, 0x384fbdbd,
    0x4c11db70, 0x48d0c6c7, 0x4593e01e, 0x4152fda9, 0x5f15adac, 0x5bd4b01b, 0x569796c2, 0x52568b75,
    0x6a1936c8, 0x6ed82b7f, 0x639b0da6, 0x675a1011, 0x791d4014, 0x7ddc5da3, 0x709f7b7a, 0x745e66cd,
    0x9823b6e0, 0x9ce2ab57, 0x91a18d8e, 0x95609039, 0x8b27c03c, 0x8fe6dd8b, 0x82a5fb52, 0x8664e6e5,
    0xbe2b5b58, 0xbaea46ef, 0xb7a96036, 0xb3687d81, 0xad2f2d84, 0xa9ee3033, 0xa4ad16ea, 0xa06c0b5d,
    0xd4326d90, 0xd0f37027, 0xddb056fe, 0xd9714b49, 0xc7361b4c, 0xc3f706fb, 0xceb42022, 0xca753d95,
    0xf23a8028, 0xf6fb9d9f, 0xfbb8bb46, 0xff79a6f1, 0xe13ef6f4, 0xe5ffeb43, 0xe8bccd9a, 0xec7dd02d,
    0x34867077, 0x30476dc0, 0x3d044b19, 0x39c556ae, 0x278206ab, 0x23431b1c, 0x2e003dc5, 0x2ac12072,
    0x128e9dcf, 0x164f8078, 0x1b0ca6a1, 0x1fcdbb16, 0x018aeb13, 0x054bf6a4, 0x0808d07d, 0x0cc9cdca,
    0x7897ab07, 0x7c56b6b0, 0x71159069, 0x75d48dde, 0x6b93dddb, 0x6f52c06c, 0x6211e6b5, 0x66d0fb02,
    0x5e9f46bf, 0x5a5e5b08, 0x571d7dd1, 0x53dc6066, 0x4d9b3063, 0x495a2dd4, 0x44190b0d, 0x40d816ba,
    0xaca5c697, 0xa864db20, 0xa527fdf9, 0xa1e6e04e, 0xbfa1b04b, 0xbb60adfc, 0xb6238b25, 0xb2e29692,
    0x8aad2b2f, 0x8e6c3698, 0x832f1041, 0x87ee0df6, 0x99a95df3, 0x9d684044, 0x902b669d, 0x94ea7b2a,
    0xe0b41de7, 0xe4750050, 0xe9362689, 0xedf73b3e, 0xf3b06b3b, 0xf771768c, 0xfa325055, 0xfef34de2,
    0xc6bcf05f, 0xc27dede8, 0xcf3ecb31, 0xcbffd686, 0xd5b88683, 0xd1799b34, 0xdc3abded, 0xd8fba05a,
    0x690ce0ee, 0x6dcdfd59, 0x608edb80, 0x644fc637, 0x7a089632, 0x7ec98b85, 0x738aad5c, 0x774bb0eb,
    0x4f040d56, 0x4bc510e1, 0x46863638, 0x42472b8f, 0x5c007b8a, 0x58c1663d, 0x558240e4, 0x51435d53,
    0x251d3b9e, 0x21dc2629, 0x2c9f00f0, 0x285e1d47, 0x36194d42, 0x32d850f5, 0x3f9b762c, 0x3b5a6b9b,
    0x0315d626, 0x07d4cb91, 0x0a97ed48, 0x0e56f0ff, 0x1011a0fa, 0x14d0bd4d, 0x19939b94, 0x1d528623,
    0xf12f560e, 0xf5ee4bb9, 0xf8ad6d60, 0xfc6c70d7, 0xe22b20d2, 0xe6ea3d65, 0xeba91bbc, 0xef68060b,
    0xd727bbb6, 0xd3e6a601, 0xdea580d8, 0xda649d6f, 0xc423cd6a, 0xc0e2d0dd, 0xcda1f604, 0xc960ebb3,
    0xbd3e8d7e, 0xb9ff90c9, 0xb4bcb610, 0xb07daba7, 0xae3afba2, 0xaafbe615, 0xa7b8c0cc, 0xa379dd7b,
    0x9b3660c6, 0x9ff77d71, 0x92b45ba8, 0x9675461f, 0x8832161a, 0x8cf30bad, 0x81b02d74, 0x857130c3,
    0x5d8a9099, 0x594b8d2e, 0x5408abf7, 0x50c9b640, 0x4e8ee645, 0x4a4ffbf2, 0x470cdd2b, 0x43cdc09c,
    0x7b827d21, 0x7f436096, 0x7200464f, 0x76c15bf8, 0x68860bfd, 0x6c47164a, 0x61043093, 0x65c52d24,
    0x119b4be9, 0x155a565e, 0x18197087, 0x1cd86d30, 0x029f3d35, 0x065e2082, 0x0b1d065b, 0x0fdc1bec,
    0x3793a651, 0x3352bbe6, 0x3e119d3f, 0x3ad08088, 0x2497d08d, 0x2056cd3a, 0x2d15ebe3, 0x29d4f654,
    0xc5a92679, 0xc1683bce, 0xcc2b1d17, 0xc8ea00a0, 0xd6ad50a5, 0xd26c4d12, 0xdf2f6bcb, 0xdbee767c,
    0xe3a1cbc1, 0xe760d676, 0xea23f0af, 0xeee2ed18, 0xf0a5bd1d, 0xf464a0aa, 0xf9278673, 0xfde69bc4,
    0x89b8fd09, 0x8d79e0be, 0x803ac667, 0x84fbdbd0, 0x9abc8bd5, 0x9e7d9662, 0x933eb0bb, 0x97ffad0c,
    0xafb010b1, 0xab710d06, 0xa6322bdf, 0xa2f33668, 0xbcb4666d, 0xb8757bda, 0xb5365d03, 0xb1f740b4,
]

# Hardcoded AES key materials for password decryption
PWD_KEY_MODE1 = [
    0xb8, 0x36, 0x3c, 0x9b, 0x77, 0xda, 0xed, 0x4b,
    0x9a, 0xbb, 0x9f, 0x2f, 0x6d, 0xf5, 0xf1, 0xd5,
    0xcb, 0x64, 0x97, 0x5d, 0x5d, 0x3b, 0xce, 0xe8,
    0x82, 0x7f, 0x2f, 0x42, 0x23, 0x5f, 0x92, 0x29
]

PWD_KEY_MODE2 = [
    0x6f, 0xc6, 0xe3, 0x43, 0x6a, 0x53, 0xb6, 0x31,
    0x0d, 0xc0, 0x9a, 0x47, 0x54, 0x94, 0xac, 0x77,
    0x4e, 0x7a, 0xfb, 0x21, 0xb9, 0xe5, 0x8f, 0xc8,
    0xe5, 0x8b, 0x56, 0x60, 0xe4, 0x8e, 0x24, 0x98
]


def calc_custom_crc(data: bytes) -> int:
    """Calculates the custom chunked CRC-32 checksum used in the file header."""
    crc = 0
    chunk_size = 1024
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        for b in chunk:
            idx = (crc >> 24) & 0xff
            crc = (((crc << 8) | b) ^ CRC_TABLE[idx]) & 0xffffffff
        for _ in range(4):
            idx = (crc >> 24) & 0xff
            crc = ((crc << 8) ^ CRC_TABLE[idx]) & 0xffffffff
    return crc


def derive_key(salt: bytes) -> bytes:
    """Derives a 32-byte AES key from a 16-byte salt using SHA-256 over 8192 iterations."""
    key_material = salt + b'\x00' * 16
    fixed_str = b"hex:13395537D2730554A176799F6D56A239"
    for _ in range(8192):
        h = hashlib.sha256()
        h.update(key_material)
        h.update(fixed_str)
        key_material = h.digest()
    return key_material


def decrypt_config(enc_path: str, dec_path: str) -> bool:
    """Decrypts a configuration file (.xml.enc / .cfg) and writes it to dec_path."""
    try:
        with open(enc_path, 'rb') as f:
            data = f.read()

        file_size = len(data)
        if file_size < 56:
            print("[-] Error: File too small to be a valid encrypted configuration.")
            return False

        # If it is a CFG file (starts with 32-byte header), skip it
        # Standard XML decryption has the 8-byte header at offset 0
        header_offset = 0
        if file_size >= 88 and data[32:40] == b'\x01\x00\x00\x00':
            print("[+] CFG file structure detected. Skipping 32-byte header.")
            header_offset = 32

        header = data[header_offset : header_offset + 8]
        salt = data[header_offset + 8 : header_offset + 24]
        
        # Calculate ciphertext length using the do-while loop logic:
        # limit = file_size - header_offset - 56
        # num_blocks = math.ceil(limit / 16) -> (limit + 15) // 16
        limit = file_size - header_offset - 56
        num_blocks = (limit + 15) // 16
        ciphertext_len = num_blocks * 16
        
        ciphertext = data[header_offset + 24 : header_offset + 24 + ciphertext_len]
        # Signature is at most 32 bytes after ciphertext
        signature = data[header_offset + 24 + ciphertext_len : header_offset + 24 + ciphertext_len + 32]

        print(f"[+] Header Magic: {header[:4].hex()}")
        print(f"[+] Header Checksum: {header[4:].hex()}")
        print(f"[+] Salt/IV: {salt.hex()}")
        print(f"[+] Ciphertext Length: {len(ciphertext)} bytes")
        print(f"[+] Signature Length: {len(signature)} bytes")

        # Derive AES key
        derived_key = derive_key(salt)
        print(f"[+] Derived AES Key: {derived_key.hex()}")

        # Verify HMAC-SHA256 (allowing truncation to the signature length on disk)
        calculated_hmac = hmac.new(derived_key, ciphertext, hashlib.sha256).digest()
        if calculated_hmac[:len(signature)] != signature:
            print("[-] Warning: HMAC verification failed! File may be corrupted or modified.")
        else:
            print("[+] HMAC verified successfully.")

        # AES-CBC-256 Decryption
        cipher = AES.new(derived_key, AES.MODE_CBC, salt)
        decrypted = cipher.decrypt(ciphertext)

        # Trim padding based on the lower 4 bits of the last byte of the salt
        last_block_len = salt[15] & 0x0f
        if last_block_len != 0:
            padding_to_remove = 16 - last_block_len
            print(f"[+] Trimming {padding_to_remove} bytes of padding from the last block.")
            decrypted = decrypted[:-padding_to_remove]

        # Decompress GZIP payload
        decompressed_data = gzip.decompress(decrypted)
        with open(dec_path, 'wb') as f_out:
            f_out.write(decompressed_data)

        print(f"[+] Success: Configuration decrypted to {dec_path} (size: {len(decompressed_data)} bytes)")
        return True
    except Exception as e:
        print(f"[-] Decryption failed: {e}")
        return False


def encrypt_config(dec_path: str, enc_path: str) -> bool:
    """Compresses and encrypts an XML configuration file, writing it to enc_path."""
    try:
        with open(dec_path, 'rb') as f:
            xml_data = f.read()

        # Compress XML to GZIP
        print("[+] Compressing XML configuration with GZIP...")
        gzip_data = gzip.compress(xml_data)
        gzip_len = len(gzip_data)
        print(f"[+] GZIP compressed size: {gzip_len} bytes")

        # Compute custom CRC-32 of GZIP data
        crc_val = calc_custom_crc(gzip_data)
        print(f"[+] Custom CRC-32: {hex(crc_val)}")

        # Construct 8-byte header: 01 00 00 00 + CRC-32 (little endian)
        header = b'\x01\x00\x00\x00' + struct_pack_le(crc_val)

        # Generate a random 16-byte salt/IV
        salt_raw = os.urandom(16)
        
        # Embed the lower 4 bits of GZIP size into the last byte of salt
        last_byte = (salt_raw[15] & 0xf0) | (gzip_len & 0x0f)
        salt = salt_raw[:15] + bytes([last_byte])
        print(f"[+] Generated Salt/IV: {salt.hex()}")

        # Derive AES key
        derived_key = derive_key(salt)
        print(f"[+] Derived AES Key: {derived_key.hex()}")

        # Pad GZIP payload to 16-byte boundary (standard zero-padding for custom AES)
        padded_len = (gzip_len + 15) & ~15
        padding_size = padded_len - gzip_len
        padded_gzip = gzip_data + b'\x00' * padding_size

        # AES-CBC-256 Encryption
        cipher = AES.new(derived_key, AES.MODE_CBC, salt)
        ciphertext = cipher.encrypt(padded_gzip)

        # Calculate HMAC-SHA256 over ciphertext
        calculated_hmac = hmac.new(derived_key, ciphertext, hashlib.sha256).digest()

        # Write output file: header + salt + ciphertext + HMAC signature
        with open(enc_path, 'wb') as f_out:
            f_out.write(header)
            f_out.write(salt)
            f_out.write(ciphertext)
            f_out.write(calculated_hmac)

        print(f"[+] Success: Configuration encrypted to {enc_path} (size: {os.path.getsize(enc_path)} bytes)")
        return True
    except Exception as e:
        print(f"[-] Encryption failed: {e}")
        return False


def struct_pack_le(val: int) -> bytes:
    """Packs a 32-bit unsigned int into little-endian bytes."""
    return bytes([
        val & 0xff,
        (val >> 8) & 0xff,
        (val >> 16) & 0xff,
        (val >> 24) & 0xff
    ])


def base93_decode(block: list) -> list:
    """Decodes 20 base-93 characters into 4 32-bit integers (16 bytes)."""
    decoded_ints = []
    for i in range(4):
        val = 0
        base = 1
        for j in range(5):
            val += block[i * 5 + j] * base
            base *= 93
        decoded_ints.append(val)
    
    # Unpack 4 integers to 16 bytes (little-endian)
    out_bytes = []
    for val in decoded_ints:
        out_bytes.extend([
            val & 0xff,
            (val >> 8) & 0xff,
            (val >> 16) & 0xff,
            (val >> 24) & 0xff
        ])
    return out_bytes


def base93_preprocess(text: str) -> list:
    """Preprocesses a ciphertext string: unescapes XML entities and maps to base-93 values."""
    unescaped = html.unescape(text)
    vals = []
    for char in unescaped:
        c = ord(char)
        if c == 0x7e:  # '~'
            vals.append(0x1e)
        else:
            vals.append(c - 0x21)
    return vals


def decrypt_password_mode1(ciphertext: str) -> str:
    """Decrypts Mode 1 password string ($1...$)."""
    # Validate prefix/suffix
    if not (ciphertext.startswith('$1') and ciphertext.endswith('$')):
        raise ValueError("Invalid Mode 1 password format. Must start with '$1' and end with '$'.")
    
    raw_ciphertext = ciphertext[2:-1]
    mapped_vals = base93_preprocess(raw_ciphertext)
    
    if len(mapped_vals) % 24 != 0:
        raise ValueError(f"Invalid Mode 1 ciphertext length ({len(mapped_vals)}). Must be a multiple of 24.")

    plaintext_bytes = bytearray()
    
    # Process blocks of 24 characters
    for offset in range(0, len(mapped_vals), 24):
        block = mapped_vals[offset : offset + 24]
        
        # Decode the first 20 characters into 16 bytes of ciphertext
        cipher_block = bytes(base93_decode(block[:20]))
        
        # Construct dynamic AES-256 key from hardcoded base and the last 4 characters of block
        key = list(PWD_KEY_MODE1)
        key[11] = block[20]
        key[17] = block[21]
        key[23] = block[22]
        key[29] = block[23]
        
        # Decrypt block using AES-256-ECB (raw AES block decryption)
        aes = AES.new(bytes(key), AES.MODE_ECB)
        decrypted_block = aes.decrypt(cipher_block)
        plaintext_bytes.extend(decrypted_block)
        
    # Null terminator strip
    null_idx = plaintext_bytes.find(0)
    if null_idx != -1:
        plaintext_bytes = plaintext_bytes[:null_idx]
        
    return plaintext_bytes.decode('utf-8', errors='ignore')


def decrypt_password_mode2(ciphertext: str) -> str:
    """Decrypts Mode 2 password string ($2...$)."""
    if not (ciphertext.startswith('$2') and ciphertext.endswith('$')):
        raise ValueError("Invalid Mode 2 password format. Must start with '$2' and end with '$'.")
        
    raw_ciphertext = ciphertext[2:-1]
    mapped_vals = base93_preprocess(raw_ciphertext)
    
    if len(mapped_vals) % 20 != 0:
        raise ValueError(f"Invalid Mode 2 ciphertext length ({len(mapped_vals)}). Must be a multiple of 20.")
        
    # Standard CBC mode where:
    # 1. Blocks 0 to N-1 are ciphertext blocks.
    # 2. Block N (the last block) is the IV block.
    num_blocks = len(mapped_vals) // 20
    if num_blocks < 2:
        raise ValueError("Mode 2 ciphertext must contain at least 2 blocks (IV + 1 ciphertext block).")
        
    # Decode the last block as the IV
    iv_block_chars = mapped_vals[(num_blocks - 1) * 20 :]
    iv = bytes(base93_decode(iv_block_chars))
    
    # Decode all other blocks as ciphertext
    cipher_bytes = bytearray()
    for b in range(num_blocks - 1):
        block_chars = mapped_vals[b * 20 : (b + 1) * 20]
        cipher_bytes.extend(base93_decode(block_chars))
        
    # AES-256-CBC Decryption
    key = bytes(PWD_KEY_MODE2)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(bytes(cipher_bytes))
    
    # Null terminator strip
    null_idx = decrypted.find(0)
    if null_idx != -1:
        decrypted = decrypted[:null_idx]
        
    return decrypted.decode('utf-8', errors='ignore')


def decrypt_password_mode3(ciphertext: str) -> str:
    """Decrypts Mode 3 (superuser / de_su) password string (8 characters)."""
    if len(ciphertext) != 8:
        raise ValueError("Mode 3 (de_su) password must be exactly 8 characters long.")
        
    # Process bytes
    modified_bytes = bytearray()
    for char in ciphertext:
        b = ord(char)
        if b <= 0x47:  # 71
            modified_bytes.append((b * 2) & 0xff)
        else:
            modified_bytes.append(b // 2)
            
    # MD5 hash
    m = hashlib.md5()
    m.update(modified_bytes)
    digest = m.digest()
    
    # Map first 8 bytes of MD5 digest to printable characters
    out_chars = []
    for i in range(8):
        c = (digest[i] % 90) + 33
        if c == 63:  # '?'
            c = 62   # '>'
        out_chars.append(chr(c))
        
    return "".join(out_chars)


def decrypt_password(ciphertext: str, mode: str = 'auto') -> tuple:
    """Auto-detects password format and decrypts it, returning (decrypted_pwd, mode_used)."""
    text = ciphertext.strip()
    if mode == '1' or (mode == 'auto' and text.startswith('$1')):
        return decrypt_password_mode1(text), 'Mode 1 ($1...$)'
    elif mode == '2' or (mode == 'auto' and text.startswith('$2')):
        return decrypt_password_mode2(text), 'Mode 2 ($2...$)'
    elif mode == '3' or (mode == 'auto' and len(text) == 8):
        return decrypt_password_mode3(text), 'Mode 3 (de_su)'
    else:
        raise ValueError("Could not auto-detect password decryption mode.")


def main():
    parser = argparse.ArgumentParser(description="Huawei ONT Cryptographic Offline Utility")
    subparsers = parser.add_subparsers(dest="command", help="Action command")

    # Decrypt Config parser
    dec_parser = subparsers.add_parser("decrypt-cfg", help="Decrypt XML.enc / CFG configuration files")
    dec_parser.add_argument("input", help="Encrypted input file path (.enc/.cfg)")
    dec_parser.add_argument("output", help="Output decrypted XML file path")

    # Encrypt Config parser
    enc_parser = subparsers.add_parser("encrypt-cfg", help="Encrypt XML configuration files")
    enc_parser.add_argument("input", help="Plain XML input file path")
    enc_parser.add_argument("output", help="Output encrypted file path (.enc)")

    # Decrypt Password parser
    pwd_parser = subparsers.add_parser("decrypt-pwd", help="Decrypt ONT configuration password hashes")
    pwd_parser.add_argument("ciphertext", help="Password ciphertext / hash")
    pwd_parser.add_argument("-m", "--mode", choices=['1', '2', '3', 'auto'], default='auto',
                            help="Decryption mode: 1 (Mode 1), 2 (Mode 2), 3 (de_su/Mode 3), auto (auto-detect)")

    args = parser.parse_args()

    if args.command == "decrypt-cfg":
        success = decrypt_config(args.input, args.output)
        sys.exit(0 if success else 1)
    elif args.command == "encrypt-cfg":
        success = encrypt_config(args.input, args.output)
        sys.exit(0 if success else 1)
    elif args.command == "decrypt-pwd":
        try:
            pwd, mode_used = decrypt_password(args.ciphertext, args.mode)
            print(f"Detected/Used: {mode_used}")
            print(f"Decrypted Password: {pwd}")
        except Exception as e:
            print(f"[-] Error: {e}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
