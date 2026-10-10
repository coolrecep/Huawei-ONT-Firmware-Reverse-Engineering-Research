import os
import struct
from pathlib import Path

def extract_ubi_volumes(filepath, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    EC_MAGIC = b"UBI#"
    VID_MAGIC = b"UBI!"
    block_size = 262144  # 256KB PEB size
    
    print(f"[*] Analyzing UBI in {filepath}...")
    
    # First pass: collect all blocks and group by vol_id and lnum
    volumes = {}
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
                    
                    if vol_id not in volumes:
                        volumes[vol_id] = []
                    volumes[vol_id].append((lnum, offset))
                    
            offset += block_size
            
    print(f"[*] Found {len(volumes)} unique UBI volumes.")
    
    # Parse layout records (vol_id = 0x7efff000 = 2147479551) to map volume names
    layout_vol_id = 2147479551
    vol_names = {}
    
    if layout_vol_id in volumes:
        # Layout volume should have lnum 0 and 1
        layout_blocks = sorted(volumes[layout_vol_id])
        with open(filepath, "rb") as f:
            for lnum, off in layout_blocks:
                f.seek(off + 8192)
                vtbl_data = f.read(146 * 128) # up to 128 records
                for vol_idx in range(128):
                    record = vtbl_data[vol_idx*146 : (vol_idx+1)*146]
                    if len(record) < 146:
                        break
                    reserved_pebs, alignment, data_size, vtype, upd_marker, name_len = struct.unpack(
                        ">IIIBBH", record[:16]
                    )
                    if name_len > 0 and name_len <= 128:
                        name = record[16:16+name_len].decode('utf-8', errors='ignore').strip()
                        # Clean name from any null bytes or garbage
                        name = "".join(c for c in name if c.isalnum() or c in "_-")
                        if name:
                            vol_names[vol_idx] = name
                            
    print("[*] Volume Name Mapping:")
    for vol_id, name in sorted(vol_names.items()):
        print(f"  - Vol ID {vol_id}: Name='{name}'")
        
    # Reconstruct and write out each volume
    for vol_id, blocks in sorted(volumes.items()):
        if vol_id == layout_vol_id:
            name = "ubi_layout"
        else:
            name = vol_names.get(vol_id, f"volume_{vol_id}")
            
        print(f"\n[*] Reconstructing volume '{name}' (ID: {vol_id})...")
        
        # Sort blocks by logical block number (lnum)
        sorted_blocks = sorted(blocks, key=lambda x: x[0])
        max_lnum = sorted_blocks[-1][0] if sorted_blocks else 0
        print(f"  - Max logical block (lnum): {max_lnum}")
        print(f"  - Physical blocks count: {len(sorted_blocks)}")
        
        output_file = output_dir / f"{name}.bin"
        
        # We will write block by block, padding any missing lnums
        written_count = 0
        with open(filepath, "rb") as f_in, open(output_file, "wb") as f_out:
            block_map = {lnum: off for lnum, off in sorted_blocks}
            for lnum in range(max_lnum + 1):
                if lnum in block_map:
                    off = block_map[lnum]
                    f_in.seek(off + 8192) # data offset is 8192
                    data = f_in.read(block_size - 8192) # usable data size
                    f_out.write(data)
                    written_count += 1
                else:
                    # Write padding
                    f_out.write(b"\x00" * (block_size - 8192))
                    
        print(f"  [+] Saved {output_file} ({os.path.getsize(output_file)} bytes)")

if __name__ == "__main__":
    extract_ubi_volumes(
        "/home/recep/Masaüstü/Firmware/20260518_140638_TC58CVG2S0HRA.bin",
        "/home/recep/Masaüstü/Firmware/extracted_partitions"
    )
