def examine_gap():
    # Let's inspect the layout volume starting from 0xe70236c (allsystemB) to 0xe702442 (wifi_paramA)
    # The gap is 214 bytes.
    # If a record size is 172, then:
    # allsystemB record is at offset 0x235c (which ends at 0x235c + 172 = 0x2408)
    # wifi_paramA record starts at 0x2442 - 16 = 0x2432 (Dec: 9266).
    # Wait, the gap between 0x2408 and 0x2432 is 42 bytes!
    # Let's print out the raw hex bytes from 0x235c to 0x2500.
    filepath = "/home/recep/Masaüstü/Firmware/20260518_140638_TC58CVG2S0HRA.bin"
    layout_offset = 0xe700000
    
    with open(filepath, "rb") as f:
        f.seek(layout_offset + 8192 + 0x235c)
        data = f.read(400)
        
    print(f"Data starts at 0x235c:")
    # We will print it out grouped by 172 bytes
    print(f"Record 5 (allsystemB): {data[:172].hex()}")
    # What's in the next block? Let's check from index 172 onwards
    next_part = data[172:]
    print(f"Next part (Hex): {next_part.hex()}")

if __name__ == "__main__":
    examine_gap()
