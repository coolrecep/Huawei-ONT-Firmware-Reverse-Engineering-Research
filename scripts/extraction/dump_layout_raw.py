import struct

def dump_layout(filepath):
    layout_offsets = [0xe700000, 0xf600000]
    block_size = 262144
    
    with open(filepath, "rb") as f:
        for off in layout_offsets:
            print(f"\nDumping layout at offset {hex(off)}:")
            f.seek(off + 8192)
            vtbl_data = f.read(146 * 20) # print first 20 records
            for idx in range(20):
                record = vtbl_data[idx*146 : (idx+1)*146]
                if len(record) < 146:
                    break
                header = record[:16]
                # Check if it has any non-zero bytes
                if any(header):
                    reserved_pebs, alignment, data_size, vtype, upd_marker, name_len = struct.unpack(
                        ">IIIBBH", header
                    )
                    name = record[16:16+name_len].decode('utf-8', errors='ignore') if name_len > 0 else ""
                    print(f"Record {idx}: name_len={name_len}, name='{name}', reserved_pebs={reserved_pebs}, align={alignment}, size={data_size}, vtype={vtype}, upd={upd_marker}")
                    print(f"  Raw: {header.hex()}")

if __name__ == "__main__":
    dump_layout("/home/recep/Masaüstü/Firmware/20260518_140638_TC58CVG2S0HRA.bin")
