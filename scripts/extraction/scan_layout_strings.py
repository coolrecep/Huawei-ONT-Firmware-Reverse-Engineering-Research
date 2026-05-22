def scan_layout_strings(filepath):
    layout_offsets = [0xe700000, 0xf600000]
    block_size = 262144
    
    with open(filepath, "rb") as f:
        for off in layout_offsets:
            print(f"\nScanning UBI layout volume at offset {hex(off)}:")
            f.seek(off + 8192)
            # UBI layout volume has 128 records, each 146 bytes
            vtbl_data = f.read(146 * 128)
            for idx in range(128):
                record = vtbl_data[idx*146 : (idx+1)*146]
                if len(record) < 146:
                    break
                
                # Check for printable strings in the record
                # Let's decode the record as ASCII/UTF-8 and print any contiguous printable chars
                printable = []
                for b in record:
                    if 32 <= b <= 126:
                        printable.append(chr(b))
                    elif printable:
                        joined = "".join(printable).strip()
                        if len(joined) >= 3 and not joined.isdigit():
                            print(f"  - Record {idx}: Found string: '{joined}'")
                        printable = []
                if printable:
                    joined = "".join(printable).strip()
                    if len(joined) >= 3 and not joined.isdigit():
                        print(f"  - Record {idx}: Found string: '{joined}'")

if __name__ == "__main__":
    scan_layout_strings("/home/recep/Masaüstü/Firmware/20260518_140638_TC58CVG2S0HRA.bin")
