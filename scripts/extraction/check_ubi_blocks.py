def check_ubi():
    filepath = "/home/recep/Masaüstü/Firmware/20260518_140638_TC58CVG2S0HRA.bin"
    block_size = 256 * 1024 # 256KB block size is standard for UBI on this flash
    
    ubi_blocks = []
    with open(filepath, "rb") as f:
        offset = 0
        while True:
            f.seek(offset)
            header = f.read(4)
            if not header:
                break
            if header == b"UBI#":
                ubi_blocks.append(offset)
            offset += 0x20000 # 128KB or 256KB? Let's check every 128KB (0x20000)
            
    print(f"Total UBI blocks found: {len(ubi_blocks)}")
    # Find contiguous ranges
    ranges = []
    if ubi_blocks:
        start = ubi_blocks[0]
        prev = ubi_blocks[0]
        for b in ubi_blocks[1:]:
            # If the gap is larger than 256KB (0x40000), we have a gap!
            if b - prev > 0x40000:
                ranges.append((start, prev))
                start = b
            prev = b
        ranges.append((start, prev))
        
    print("UBI Block Ranges:")
    for r in ranges:
        size = r[1] - r[0] + 0x40000 # assume last block is 256KB
        print(f"  - Start: {hex(r[0])} -> End: {hex(r[1])} (Size: {size / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    check_ubi()
