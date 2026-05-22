#!/usr/bin/env python3
"""
Strategy: Use paramiko SFTP to directly download /bin/ssmp from the router.
Then scan it locally.
"""

import paramiko, time, struct, zlib, os

HOST     = "192.168.1.1"
USER     = "sUser"
PASSWORD = "EP!99R4HLH9E"

CHECKS_32 = [
    (1,57),(2,72),(3,82),(4,69),(7,57),(10,33),(11,80),
    (15,52),(18,72),(19,69),(22,76),(30,57)
]

P1   = "EP!99R4HLH9E"
SN1  = "485754437C07DEA5"

def main():
    print("=" * 62)
    print("  Downloading /bin/ssmp via SFTP + scanning for ALPHA table")
    print("=" * 62)

    # ── Method 1: SFTP direct download ───────────────────────────────────
    print("\n[*] Trying SFTP download of /bin/ssmp...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=15,
                   look_for_keys=False, allow_agent=False)
    
    binary_data = None
    
    try:
        sftp = client.open_sftp()
        local_path = '/tmp/ssmp_router.bin'
        print(f"  SFTP: downloading /bin/ssmp → {local_path}")
        
        def progress(transferred, total):
            pct = transferred * 100 // total if total > 0 else 0
            if transferred % 50000 < 4096 or transferred == total:
                print(f"    {transferred}/{total} bytes ({pct}%)")
        
        sftp.get('/bin/ssmp', local_path, callback=progress)
        sftp.close()
        
        size = os.path.getsize(local_path)
        print(f"  [+] Downloaded! {size} bytes")
        
        with open(local_path, 'rb') as f:
            binary_data = f.read()
    
    except Exception as e:
        print(f"  [-] SFTP failed: {e}")
        
        # ── Method 2: SSH exec to read via dd ─────────────────────────────
        print("\n[*] Trying SSH exec channel to read binary with dd+od...")
        try:
            # Use exec_command which is cleaner than interactive shell
            # Read 32 bytes at a specific offset? No, we need the full file.
            # Try reading via /proc/ssmp PID exe link
            stdin, stdout, stderr = client.exec_command(
                "cat /bin/ssmp | od -An -tx1 | tr -d ' \\n'", timeout=120
            )
            hex_output = stdout.read().decode('ascii', errors='replace').strip()
            err_output = stderr.read().decode('ascii', errors='replace').strip()
            
            if err_output:
                print(f"  stderr: {err_output[:200]}")
            
            print(f"  Hex output length: {len(hex_output)} chars")
            
            if len(hex_output) > 100:
                hex_tokens = [hex_output[i:i+2] for i in range(0, len(hex_output), 2)]
                hex_tokens = [t for t in hex_tokens if len(t)==2 and all(c in '0123456789abcdefABCDEF' for c in t)]
                binary_data = bytes([int(t,16) for t in hex_tokens])
                print(f"  [+] Reconstructed: {len(binary_data)} bytes")
                with open('/tmp/ssmp_router.bin', 'wb') as f:
                    f.write(binary_data)
        except Exception as e2:
            print(f"  [-] exec_command also failed: {e2}")

    # ── Method 3: Use shell to run a targeted binary search ───────────────
    if binary_data is None or len(binary_data) < 1000:
        print("\n[*] Trying targeted search via exec_command shell script...")
        
        # Run a shell one-liner on the router that searches for our pattern
        # and prints the result
        # We need to find a 32-byte window where:
        # byte at offset 1 = 0x39, offset 2 = 0x48, offset 3 = 0x52, ...
        # Use od to dump and process with hexdump trickery
        
        search_script = r"""
# Check od functionality
od -An -tx1 /bin/ssmp 2>/dev/null | wc -c
"""
        stdin, stdout, stderr = client.exec_command(search_script, timeout=30)
        out = stdout.read().decode()
        err = stderr.read().decode()
        print(f"  od wc: {out.strip()}")
        print(f"  err: {err.strip()[:100]}")

        # Try with hexdump
        stdin2, stdout2, stderr2 = client.exec_command(
            "hexdump -v -e '1/1 \"%02x\"' /bin/ssmp 2>&1 | wc -c",
            timeout=30
        )
        out2 = stdout2.read().decode()
        print(f"  hexdump wc: {out2.strip()}")
        
        # Try the full hexdump
        if "not found" not in out2:
            print("  [*] Using hexdump to get binary...")
            stdin3, stdout3, stderr3 = client.exec_command(
                "hexdump -v -e '1/1 \"%02x\"' /bin/ssmp",
                timeout=120
            )
            hex_full = stdout3.read().decode('ascii', errors='replace').strip()
            err3 = stderr3.read().decode()
            if err3: print(f"  hexdump err: {err3[:100]}")
            
            print(f"  hexdump output length: {len(hex_full)} chars")
            if len(hex_full) > 1000:
                binary_data = bytes([int(hex_full[i:i+2],16) for i in range(0,len(hex_full)-1,2) 
                                    if all(c in '0123456789abcdefABCDEF' for c in hex_full[i:i+2])])
                print(f"  [+] Reconstructed: {len(binary_data)} bytes")
                with open('/tmp/ssmp_router_hexdump.bin', 'wb') as f:
                    f.write(binary_data)

    # ── Scan whatever binary data we have ─────────────────────────────────
    if binary_data and len(binary_data) > 1000:
        print(f"\n[*] Scanning {len(binary_data)} bytes for 32-byte ALPHA table...")
        print(f"    MD5 of ssmp: {__import__('hashlib').md5(binary_data).hexdigest()}")
        
        best_score = 0
        best_off = -1
        all_high = []
        
        for offset in range(len(binary_data) - 32):
            b = binary_data[offset:offset+32]
            score = sum(1 for idx, val in CHECKS_32 if b[idx] == val)
            if score > best_score:
                best_score = score
                best_off = offset
            if score >= 7:
                all_high.append((score, offset, bytes(b)))
        
        print(f"\n  Best: {best_score}/12 at offset {best_off}")
        
        if all_high:
            print(f"\n  Top results (score >= 7):")
            for score, off, b in sorted(all_high, reverse=True)[:10]:
                asc = ''.join(chr(x) if 32<=x<127 else '.' for x in b)
                hex_s = ' '.join(f'{x:02x}' for x in b)
                print(f"\n  SCORE {score}/12 at offset {off} (0x{off:x}):")
                print(f"    HEX: {hex_s}")
                print(f"    ASC: {asc}")
                print(f"    Verified slots: {[CHECKS_32[i] for i in range(len(CHECKS_32)) if b[CHECKS_32[i][0]]==CHECKS_32[i][1]]}")
                
                if score == 12:
                    print(f"\n  === FULL ALPHA TABLE FOUND! ===")
                    print(f"    ALPHA = {repr(''.join(chr(x) if 32<=x<127 else '?' for x in b))}")
                    alpha = ''.join(chr(x) if 32<=x<127 else '?' for x in b)
                    
                    # Verify P1
                    sn1 = bytes.fromhex(SN1)
                    crc1 = zlib.crc32(sn1) & 0xFFFFFFFF
                    ext1 = list(sn1) + list(struct.pack('>I', crc1))
                    result = ''.join(alpha[(byte>>1)%32] for byte in ext1)
                    print(f"    P1 verification: {result} (expected: {P1}) {'✓' if result==P1 else '✗'}")
        
        # Show best even if score < 7
        if not all_high and best_off >= 0:
            b = binary_data[best_off:best_off+32]
            print(f"  Best ({best_score}/12):")
            print(f"    HEX: {' '.join(f'{x:02x}' for x in b)}")
    else:
        print(f"\n[!] No usable binary data (size={len(binary_data) if binary_data else 0})")
        print("    Alternative: use the on-device awk approach to find the table bytes")
        
        # Last resort: on-device awk scan for specific byte sequence
        print("\n[*] Running targeted on-device search...")
        # Search for the pattern: at position+3, byte=0x52(R) and position+22, byte=0x4C(L)
        # Using awk on od output
        search = r"""
od -An -tx1 /bin/ssmp 2>/dev/null | tr ' \n' '\n\n' | grep -v '^$' | head -2000 | \
awk 'NR==3 {print "byte_3="$0}; NR==22 {print "byte_22="$0}'
"""
        stdin, stdout, stderr = client.exec_command(search, timeout=30)
        print(stdout.read().decode()[:500])
        print("Hint: manual search needed")

    client.close()

if __name__ == "__main__":
    main()
