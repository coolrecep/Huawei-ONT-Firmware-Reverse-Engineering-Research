def find_all_filesystem_signatures():
    # Let's scan the physical NAND dump for SquashFS, UBIFS, and UBI images
    filepath = "/home/recep/Masaüstü/Firmware/20260518_140638_TC58CVG2S0HRA.bin"
    chunk_size = 1024 * 1024
    
    signatures = {
        b"hsqs": "SquashFS (le)",
        b"sqsh": "SquashFS (be)",
        b"UBI#": "UBI Erase Count",
        b"\x31\x18\x10\x06": "UBIFS Superblock (le)" # UBIFS_NODE_MAGIC little endian
    }
    
    results = []
    with open(filepath, "rb") as f:
        offset = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            for sig, name in signatures.items():
                start = 0
                while True:
                    idx = chunk.find(sig, start)
                    if idx == -1:
                        break
                    results.append((offset + idx, name))
                    start = idx + 1
            offset += len(chunk)
            
    print(f"Found {len(results)} filesystem signatures:")
    # Group by name
    grouped = {}
    for off, name in results:
        if name not in grouped:
            grouped[name] = []
        grouped[name].append(off)
        
    for name, offsets in grouped.items():
        print(f"\n{name} (Count: {len(offsets)}):")
        # Print first 10
        for off in offsets[:10]:
            print(f"  - Hex: {hex(off)} (Dec: {off})")
        if len(offsets) > 10:
            print("  ...")

if __name__ == "__main__":
    find_all_filesystem_signatures()
