import struct

def map_vol4(filepath):
    EC_MAGIC = b"UBI#"
    VID_MAGIC = b"UBI!"
    block_size = 262144
    
    vol_id_target = 4
    blocks = {}
    
    offset = 0
    with open(filepath, "rb") as f:
        while True:
            f.seek(offset)
            block = f.read(block_size)
            if not block:
                break
            if block.startswith(EC_MAGIC):
                vid_header = block[4096:4096+64]
                if vid_header.startswith(VID_MAGIC):
                    magic, version, vol_type, copy_flag, compat, vol_id, lnum = struct.unpack(
                        ">IBBBbII", vid_header[:16]
                    )
                    if vol_id == vol_id_target:
                        blocks[lnum] = offset
            offset += block_size
            
    print(f"Volume {vol_id_target} Block Mapping Details:")
    print(f"  - Expected block count: {max(blocks.keys()) + 1 if blocks else 0}")
    print(f"  - Actual blocks found: {len(blocks)}")
    
    # Print any missing logical blocks
    missing = []
    for lnum in range(max(blocks.keys()) + 1 if blocks else 0):
        if lnum not in blocks:
            missing.append(lnum)
    if missing:
        print(f"  [!] Missing logical blocks: {missing}")
    else:
        print(f"  [+] All logical blocks from 0 to {max(blocks.keys())} are present!")

if __name__ == "__main__":
    map_vol4("/home/recep/Masaüstü/Firmware/20260518_140638_TC58CVG2S0HRA.bin")
