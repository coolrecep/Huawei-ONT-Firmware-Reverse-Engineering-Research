def read_layout_sequential(filepath):
    # Let's inspect the layout volume starting from offset 8192
    layout_offset = 0xe700000
    
    # We will search for the string "wifi_paramA"
    # and print the raw bytes around it.
    with open(filepath, "rb") as f:
        f.seek(layout_offset + 8192)
        data = f.read(172 * 30) # read 30 blocks of 172 bytes
        
    print(f"Total size: {len(data)}")
    
    # Search for all "allsystemB", "wifi_paramA", "wifi_paramB"
    # to find their exact offset in `data`.
    for name in [b"allsystemB", b"wifi_paramA", b"wifi_paramB", b"keyfile", b"file_system", b"app_system"]:
        idx = data.find(name)
        if idx != -1:
            print(f"String '{name.decode()}' found at absolute offset {hex(layout_offset + 8192 + idx)} (Relative in block: {idx})")
            # Let's print the 16 bytes before this string
            pre = data[idx-16:idx]
            print(f"  Pre-metadata: {pre.hex()}")
            # Let's decode pre-metadata as fields: PEBs, Align, Size, Type, Upd, name_len
            import struct
            if len(pre) == 16:
                try:
                    reserved_pebs, alignment, data_size, vol_type, upd_marker, name_len = struct.unpack(
                        ">IIIBBH", pre
                    )
                    print(f"    Decoded: PEBs={reserved_pebs}, Align={alignment}, Size={data_size}, Type={vol_type}, Upd={upd_marker}, Len={name_len}")
                except Exception as e:
                    print(f"    Failed to decode: {e}")

if __name__ == "__main__":
    read_layout_sequential("/home/recep/Masaüstü/Firmware/20260518_140638_TC58CVG2S0HRA.bin")
