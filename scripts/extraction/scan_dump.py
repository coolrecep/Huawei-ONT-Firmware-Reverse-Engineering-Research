import os

def scan_dump(filepath):
    print(f"Scanning file: {filepath} ({os.path.getsize(filepath)} bytes)")
    
    # Common magic bytes
    magics = {
        b"UBI#": "UBI Erase Count Header",
        b"UBI!": "UBI Volume Identifier Header",
        b"hsqs": "Squashfs image (little endian)",
        b"sqsh": "Squashfs image (big endian)",
        b"\x27\x05\x19\x56": "uImage Header",
        b"U-Boot": "U-Boot String",
        b"dts": "Device Tree blob",
        b"\xd0\x0d\xfe\xed": "Device Tree Structure (Flattened DTB)",
    }
    
    results = []
    
    with open(filepath, "rb") as f:
        # Read in 1MB chunks to be fast
        chunk_size = 1024 * 1024
        offset = 0
        
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
                
            for magic, name in magics.items():
                start = 0
                while True:
                    idx = chunk.find(magic, start)
                    if idx == -1:
                        break
                    abs_offset = offset + idx
                    results.append((abs_offset, name, magic))
                    start = idx + 1
                    
            offset += len(chunk)

    print(f"\nScan results (found {len(results)} matches):")
    # Group results by type to be clean
    grouped = {}
    for offset, name, magic in results:
        if name not in grouped:
            grouped[name] = []
        grouped[name].append(offset)
        
    for name, offsets in grouped.items():
        print(f"\n{name} (Count: {len(offsets)}):")
        # Print first 5 and last 5
        if len(offsets) <= 20:
            for off in offsets:
                print(f"  - Hex: {hex(off)} (Dec: {off})")
        else:
            for off in offsets[:10]:
                print(f"  - Hex: {hex(off)} (Dec: {off})")
            print("  ...")
            for off in offsets[-10:]:
                print(f"  - Hex: {hex(off)} (Dec: {off})")

if __name__ == "__main__":
    scan_dump("/home/recep/Masaüstü/Firmware/20260518_140638_TC58CVG2S0HRA.bin")
