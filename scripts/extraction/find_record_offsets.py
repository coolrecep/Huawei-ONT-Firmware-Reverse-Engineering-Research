def find_offsets(filepath):
    layout_offsets = [0xe700000, 0xf600000]
    block_size = 262144
    
    with open(filepath, "rb") as f:
        for off in layout_offsets:
            print(f"\nAnalyzing offsets at {hex(off)}:")
            f.seek(off + 8192)
            data = f.read(146 * 128)
            
            # Find all printable strings of length >= 3
            idx = 0
            while idx < len(data):
                # Check if we have printable characters
                if 32 <= data[idx] <= 126:
                    start = idx
                    while idx < len(data) and 32 <= data[idx] <= 126:
                        idx += 1
                    name = data[start:idx].decode('utf-8', errors='ignore').strip()
                    if len(name) >= 3 and not name.isdigit():
                        print(f"  - String '{name}' starts at offset {start} (Record index: {start / 146:.2f})")
                else:
                    idx += 1

if __name__ == "__main__":
    find_offsets("/home/recep/Masaüstü/Firmware/20260518_140638_TC58CVG2S0HRA.bin")
