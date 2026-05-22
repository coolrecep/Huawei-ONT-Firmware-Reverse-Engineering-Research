import struct

def parse_ubi_volumes(filepath):
    # UBI constants
    EC_MAGIC = b"UBI#"
    VID_MAGIC = b"UBI!"
    
    # TC58CVG2S0HRA has 256KB block size (262144 bytes)
    # Page size: 4096, block size: 262144
    block_size = 262144
    
    volumes = {}
    
    with open(filepath, "rb") as f:
        offset = 0
        while True:
            # Read block
            f.seek(offset)
            block = f.read(block_size)
            if not block:
                break
                
            if block.startswith(EC_MAGIC):
                # We have a UBI block! Check VID header (usually at offset 4096)
                vid_header = block[4096:4096+64]
                if vid_header.startswith(VID_MAGIC):
                    # Parse VID header
                    # struct ubi_vid_hdr:
                    #   __be32  magic;
                    #   __u8    version;
                    #   __u8    vol_type;
                    #   __u8    copy_flag;
                    #   __u8    compat;
                    #   __be32  vol_id;
                    #   __be32  lnum;
                    #   ...
                    magic, version, vol_type, copy_flag, compat, vol_id, lnum = struct.unpack(
                        ">IBBBbII", vid_header[:16]
                    )
                    
                    # Volume IDs >= 0x7fffffff are internal/metadata volumes
                    if vol_id < 0x7fffffff:
                        if vol_id not in volumes:
                            volumes[vol_id] = {
                                "lnums": [],
                                "offsets": [],
                                "vol_type": vol_type
                            }
                        volumes[vol_id]["lnums"].append(lnum)
                        volumes[vol_id]["offsets"].append(offset)
                        
            offset += block_size

    print(f"Found {len(volumes)} UBI volumes:")
    
    # Now let's read the layout volume (which has vol_id = 0x7efff000 = 2147479551)
    # to get the volume names!
    layout_vol_id = 2147479551
    layout_blocks = []
    
    if layout_vol_id in volumes:
        for lnum, off in zip(volumes[layout_vol_id]["lnums"], volumes[layout_vol_id]["offsets"]):
            layout_blocks.append((lnum, off))
            
    print(f"Found {len(layout_blocks)} layout blocks.")
    
    # Parse layout records
    # struct ubi_vtbl_record {
    #   __be32  reserved_pebs;
    #   __be32  alignment;
    #   __be32  data_size;
    #   __u8    vol_type;
    #   __u8    upd_marker;
    #   __be16  name_len;
    #   __u8    name[128];
    #   ...
    # } (size = 128 + 18 = 146 bytes)
    vol_names = {}
    with open(filepath, "rb") as f:
        for lnum, off in sorted(layout_blocks):
            # Read layout volume data
            # Data starts after VID header (usually offset 4096 + 64 = 4160, aligned to page size 4096 -> 8192)
            f.seek(off + 8192)
            vtbl_data = f.read(146 * 128) # up to 128 volumes
            for vol_idx in range(128):
                record = vtbl_data[vol_idx*146 : (vol_idx+1)*146]
                if len(record) < 146:
                    break
                reserved_pebs, alignment, data_size, vtype, upd_marker, name_len = struct.unpack(
                    ">IIIBBH", record[:16]
                )
                if name_len > 0 and name_len <= 128:
                    name = record[16:16+name_len].decode('utf-8', errors='ignore')
                    vol_names[vol_idx] = name
                    print(f"  - Vol ID {vol_idx}: Name={name}, Size={reserved_pebs} PEBs, Type={vtype}")

    # Combine names with our gathered info
    print("\nUBI Volume Details:")
    for vol_id, info in sorted(volumes.items()):
        name = vol_names.get(vol_id, f"unknown_{vol_id}")
        pebs_count = len(info["offsets"])
        min_offset = min(info["offsets"])
        max_offset = max(info["offsets"])
        print(f"  - Name: {name} (ID: {vol_id})")
        print(f"    PEBs: {pebs_count}")
        print(f"    Offset Range: {hex(min_offset)} -> {hex(max_offset)}")
        print(f"    Logical Blocks: {sorted(info['lnums'])[:5]} ... {sorted(info['lnums'])[-5:] if len(info['lnums']) > 5 else ''}")

if __name__ == "__main__":
    parse_ubi_volumes("/home/recep/Masaüstü/Firmware/20260518_140638_TC58CVG2S0HRA.bin")
