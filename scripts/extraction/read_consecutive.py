def read_all_consecutive_records(filepath):
    # Let's inspect the first 30 records (each 146 bytes long) at 0xe700000 + 8192
    record_size = 146
    
    with open(filepath, "rb") as f:
        f.seek(0xe700000 + 8192)
        data = f.read(record_size * 30)
        
        for i in range(30):
            record = data[i*record_size : (i+1)*record_size]
            print(f"\nRecord {i}:")
            print(f"  Header (Hex): {record[:16].hex()}")
            print(f"  Header (Str): {record[:16].decode('utf-8', errors='ignore')}")
            # Try to decode string in the name field (bytes 16 to 143)
            name_part = record[16:144]
            # Find first null byte
            null_idx = name_part.find(b"\x00")
            if null_idx != -1:
                name_str = name_part[:null_idx].decode('utf-8', errors='ignore')
            else:
                name_str = name_part.decode('utf-8', errors='ignore')
            print(f"  Name (Str):   '{name_str}'")
            print(f"  Name (Hex):   {name_part[:32].hex()}...")

if __name__ == "__main__":
    read_all_consecutive_records("/home/recep/Masaüstü/Firmware/20260518_140638_TC58CVG2S0HRA.bin")
