def inspect_layout_completely(filepath):
    # Let's inspect the entire layout volume block from 8192 onwards.
    # UBI Layout Volume records can be up to 128, each 146 bytes.
    # Wait, the structure standard size is 146 bytes in UBI.
    # But wait! Why did we find 'flash_configA' at 8208, flash_configB at 8380 (Diff = 172)?
    # Ah! The struct size in this specific implementation of UBI (or this vendor's version)
    # might be 172 bytes!
    # Let's verify if all records align to 172 bytes.
    # 0 * 172 = 0
    # 1 * 172 = 172
    # 2 * 172 = 344
    # 3 * 172 = 516
    # 4 * 172 = 688
    # 5 * 172 = 860
    # 6 * 172 = 1032 -> Wait! wifi_paramA is at offset 1090.
    # Why is wifi_paramA at offset 1090?
    # Let's look at the gap between 1032 and 1090: it's 58 bytes.
    # Wait, let's look at the string offset of allsystemB: 0x236c (Dec: 9068).
    # Its metadata starts 16 bytes before: 0x235c (Dec: 9052).
    # Wait, is wifi_paramA at offset 0x2442?
    # Its metadata starts 16 bytes before: 0x2432 (Dec: 9266).
    # Wait, 9266 - 9052 = 214 bytes!
    # Why 214 bytes?
    # Let's check the contents of block 5 raw hex again:
    # 0000014b 00000001 00000000 0100000a
    # This is exactly PEBs=331 (0x14b), Align=1, Size=0, Type=1, Upd=0, Len=10.
    # Wait, where does the 214 byte offset come from?
    # Is it because there is another record between allsystemB and wifi_paramA?
    # Let's check: Record 6 is allsystemB. Record 7 is ... wait, wifi_paramA?
    # Let's look at our sequential scan results:
    # - String 'allsystemB' found at absolute offset 0xe70236c (Relative in block: 876)
    # - String 'wifi_paramA' found at absolute offset 0xe702442 (Relative in block: 1090)
    # Why is wifi_paramA at offset 1090?
    # Let's write a python script to search for the string "wifi_paramA" in the entire NAND dump!
    # Maybe we can find the layout table somewhere else, or the layout volume structure has multiple volumes!
    pass

if __name__ == "__main__":
    import re
    filepath = "/home/recep/Masaüstü/Firmware/20260518_140638_TC58CVG2S0HRA.bin"
    with open(filepath, "rb") as f:
        # Read the first 32KB of layout volume at 0xe700000
        f.seek(0xe700000 + 8192)
        data = f.read(32768)
        
    print("Print all valid UBI records found by searching for metadata headers:")
    # A valid metadata header starts with 4-bytes PEBs count, 4-bytes alignment, 4-bytes data_size,
    # 1-byte type, 1-byte upd_marker, 2-bytes name_len.
    # Since PEBs count is usually small (e.g. 1 to 4096), the first 2 bytes are 0x0000.
    # Align is usually 1, so bytes 4-7 are 0x00000001.
    # Data size is usually 0, so bytes 8-11 are 0x00000000.
    # Type is usually 1 or 2, upd_marker is 0.
    # So the pattern is: \x00\x00[\x00-\xff][\x00-\xff]\x00\x00\x00\x01\x00\x00\x00\x00
    # Let's search for this pattern!
    import struct
    idx = 0
    while idx < len(data) - 16:
        # Check pattern
        if data[idx:idx+4] != b"\x00\x00\x00\x00" and data[idx+4:idx+12] == b"\x00\x00\x00\x01\x00\x00\x00\x00":
            # Potential header!
            pebs, align, size, vtype, upd, name_len = struct.unpack(">IIIBBH", data[idx:idx+16])
            if name_len > 0 and name_len <= 128:
                # Read name
                name = data[idx+16:idx+16+name_len].decode('utf-8', errors='ignore')
                if any(c.isalnum() for c in name):
                    print(f"Found UBI Record at block offset {hex(idx)} (Dec: {idx}):")
                    print(f"  Name: '{name}' (Len: {name_len})")
                    print(f"  PEBs: {pebs}, Align: {align}, Size: {size}, Type: {vtype}, Upd: {upd}")
                    idx += 16 + name_len
                    continue
        idx += 1
