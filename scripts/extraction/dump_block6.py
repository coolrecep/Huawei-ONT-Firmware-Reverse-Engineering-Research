def dump_block6():
    # Let's inspect the raw bytes of Block 5 and Block 6
    # Block 5 starts at 8192 + 5 * 172 = 9052 (0x235c)
    # Block 6 starts at 8192 + 6 * 172 = 9224 (0x2408)
    filepath = "/home/recep/Masaüstü/Firmware/20260518_140638_TC58CVG2S0HRA.bin"
    layout_offset = 0xe700000
    
    with open(filepath, "rb") as f:
        f.seek(layout_offset + 8192 + 5*172)
        block5 = f.read(172)
        block6 = f.read(172)
        block7 = f.read(172)
        
        print(f"Block 5 (allsystemB) raw: {block5.hex()[:100]}")
        print(f"Block 6 (wifi_paramA?) raw: {block6.hex()[:100]}")
        print(f"Block 7 (wifi_paramB?) raw: {block7.hex()[:100]}")

if __name__ == "__main__":
    dump_block6()
