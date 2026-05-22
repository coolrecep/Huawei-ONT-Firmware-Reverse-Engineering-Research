import struct

def read_records(filepath):
    layout_offsets = [0xe700000, 0xf600000]
    # Each record in the layout volume table is 146 bytes long.
    record_size = 146
    
    # We want to print all valid volume names from the table.
    with open(filepath, "rb") as f:
        for off in layout_offsets:
            print(f"\n==========================================")
            print(f"Reading layout records at offset {hex(off)}")
            print(f"==========================================")
            
            f.seek(off + 8192)
            vtbl_data = f.read(record_size * 128)
            
            for i in range(128):
                record = vtbl_data[i * record_size : (i + 1) * record_size]
                if len(record) < record_size:
                    break
                    
                # Struct formats:
                # >IIIHBB or >IIIBBH?
                # Let's inspect the raw bytes of a few known records first to see their structures.
                # 'flash_configA' starts at record 0. Name offset in record is 16.
                # String starts at offset 16, which is exactly after the 16 bytes of metadata.
                # Let's unpack with different assumptions to find the correct format.
                raw_meta = record[:16]
                if not any(raw_meta):
                    continue
                    
                # Let's print out the raw values and string
                # We can see from standard struct ubi_vtbl_record that the fields are:
                #   __be32  reserved_pebs; (0-3)
                #   __be32  alignment;     (4-7)
                #   __be32  data_size;     (8-11)
                #   __u8    vol_type;      (12)
                #   __u8    upd_marker;    (13)
                #   __be16  name_len;      (14-15)
                #   __u8    name[128];     (16-143)
                #   __u8    flags;         (144)
                #   __u8    padding[12];   (145-156)? Wait, 146 bytes is the struct size.
                reserved_pebs, alignment, data_size, vol_type, upd_marker, name_len = struct.unpack(
                    ">IIIBBH", raw_meta
                )
                
                if name_len > 0 and name_len <= 128:
                    name = record[16:16+name_len].decode('utf-8', errors='ignore').strip()
                    # Only print if name has alphanumeric characters
                    if any(c.isalnum() for c in name):
                        print(f"Record {i:3d} | Name: {name:<20} | PEBs: {reserved_pebs:4d} | Align: {alignment:4d} | Size: {data_size:10d} | Type: {vol_type} | Upd: {upd_marker}")

if __name__ == "__main__":
    read_records("/home/recep/Masaüstü/Firmware/20260518_140638_TC58CVG2S0HRA.bin")
