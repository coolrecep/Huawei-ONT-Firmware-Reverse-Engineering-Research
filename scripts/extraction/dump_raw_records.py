def dump_raw_records(filepath):
    layout_offsets = [0xe700000, 0xf600000]
    record_size = 146
    
    with open(filepath, "rb") as f:
        for off in layout_offsets:
            print(f"\n==========================================")
            print(f"Hex dump of first 4 records at {hex(off)}")
            print(f"==========================================")
            
            f.seek(off + 8192)
            vtbl_data = f.read(record_size * 10) # 10 records
            
            for i in range(10):
                record = vtbl_data[i * record_size : (i + 1) * record_size]
                if len(record) < record_size:
                    break
                    
                meta = record[:16]
                if any(meta):
                    print(f"\nRecord {i}:")
                    print(f"  Metadata (Hex): {meta.hex()}")
                    # Let's read the name block as bytes
                    name_bytes = record[16:64]
                    print(f"  Name Block (Hex): {name_bytes.hex()}")
                    print(f"  Name Block (Str): {name_bytes.decode('utf-8', errors='ignore')}")

if __name__ == "__main__":
    dump_raw_records("/home/recep/Masaüstü/Firmware/20260518_140638_TC58CVG2S0HRA.bin")
