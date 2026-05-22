import struct

def inspect_duplicates(filepath):
    EC_MAGIC = b"UBI#"
    VID_MAGIC = b"UBI!"
    block_size = 262144
    
    # Store information as: vol_id -> lnum -> list of (offset, sqnum)
    blocks_info = {}
    
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
                    # Unpack VID fields:
                    #   magic (4), version (1), vol_type (1), copy_flag (1), compat (1),
                    #   vol_id (4), lnum (4)
                    magic, version, vol_type, copy_flag, compat, vol_id, lnum = struct.unpack(
                        ">IBBBbII", vid_header[:16]
                    )
                    
                    # sqnum is a 64-bit big endian integer at offset 32 in the VID header
                    sqnum = struct.unpack(">Q", vid_header[32:40])[0]
                    
                    if vol_id not in blocks_info:
                        blocks_info[vol_id] = {}
                    if lnum not in blocks_info[vol_id]:
                        blocks_info[vol_id][lnum] = []
                    blocks_info[vol_id][lnum].append((offset, sqnum))
                    
            offset += block_size
            
    print("Checking duplicate logical erase blocks (lnums):")
    for vol_id, lnums in sorted(blocks_info.items()):
        dups_count = 0
        for lnum, instances in lnums.items():
            if len(instances) > 1:
                dups_count += 1
                if dups_count <= 5:
                    print(f"  - Vol {vol_id}, Lnum {lnum} has {len(instances)} instances:")
                    for idx, (off, sq) in enumerate(instances):
                        print(f"    Instance {idx}: offset={hex(off)}, sqnum={sq}")
        if dups_count > 0:
            print(f"  [!] Vol {vol_id}: Total {dups_count} duplicate lnums.")
        else:
            print(f"  [+] Vol {vol_id}: No duplicate lnums.")

if __name__ == "__main__":
    inspect_duplicates("/home/recep/Masaüstü/Firmware/20260518_140638_TC58CVG2S0HRA.bin")
