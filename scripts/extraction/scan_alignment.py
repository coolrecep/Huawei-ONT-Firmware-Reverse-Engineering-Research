def scan_for_strings(filepath):
    # Scan the entire layout volume block (256KB) for known volume names or strings
    # in order to find their exact byte offsets
    block_size = 262144
    layout_offset = 0xe700000
    
    with open(filepath, "rb") as f:
        f.seek(layout_offset)
        layout_data = f.read(block_size)
        
    print(f"Loaded layout data of size: {len(layout_data)} bytes")
    
    # We will search for any string patterns in this layout block
    import re
    # Match printable strings of length 4 to 32
    matches = re.finditer(b'[a-zA-Z0-9_-]{4,32}', layout_data)
    for m in matches:
        offset = m.start()
        val = m.group().decode('utf-8', errors='ignore')
        # Let's print out the offset, val, and if it aligns to 146 bytes or similar
        print(f"String '{val:<20}' at block offset {hex(offset):<8} (Dec: {offset:6d}) | Align 146: {offset % 146:3d} | Align 4096: {offset % 4096:4d}")

if __name__ == "__main__":
    scan_for_strings("/home/recep/Masaüstü/Firmware/20260518_140638_TC58CVG2S0HRA.bin")
