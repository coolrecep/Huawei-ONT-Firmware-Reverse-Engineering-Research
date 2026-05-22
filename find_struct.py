def find_struct_size():
    # Let's check the offsets of the volume names:
    # flash_configA: 8208
    # flash_configB: 8380 (Diff = 172)
    # slave_paramA:  8552 (Diff = 172)
    # slave_paramB:  8724 (Diff = 172)
    # allsystemA:    8896 (Diff = 172)
    # allsystemB:    9068 (Diff = 172)
    # wifi_paramA:   9282 (Diff = 214? Wait!)
    # Let's print out the exact byte values from offset 8192 onwards in blocks of 172 bytes.
    filepath = "/home/recep/Masaüstü/Firmware/20260518_140638_TC58CVG2S0HRA.bin"
    layout_offset = 0xe700000
    
    with open(filepath, "rb") as f:
        f.seek(layout_offset + 8192)
        data = f.read(172 * 15)
        
        # Let's inspect each 172-byte block
        for i in range(15):
            block = data[i*172 : (i+1)*172]
            print(f"\nBlock {i} (Offset: {hex(8192 + i*172)}):")
            # Print first 24 bytes in hex
            print(f"  Header (Hex): {block[:24].hex()}")
            # Find printable strings in the block
            import re
            m = re.search(b'[a-zA-Z0-9_-]{4,}', block)
            if m:
                print(f"  String: '{m.group().decode()}' at relative offset {m.start()}")

if __name__ == "__main__":
    find_struct_size()
