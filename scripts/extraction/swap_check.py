def swap_endianness():
    # Let's check if the SquashFS image needs to be byte-swapped
    # or if we have an interleaving pattern (like OOB bytes) in volume_4.bin that we didn't account for!
    # Wait, the UBI volume data itself is aligned to UBI PEBs.
    # When we reconstructed volume_4.bin, we read (block_size - 8192) from each physical block.
    # Is the data aligned to UBI PEBs?
    # Let's check the size of volume_4.bin: 84058112 bytes.
    # UBI has physical blocks. 331 physical blocks * (262144 - 8192) = 331 * 253952 = 84058112.
    # Yes! This matches exactly!
    # But wait, why are the table block values so huge?
    # e.g., read_block: failed to read block @0x2fcecd9048fa6315
    # 0x2fcecd9048fa6315 is a huge 64-bit address!
    # In a 32-bit SquashFS (like v4.0), table offsets are 64-bit integers.
    # If the endianness was read incorrectly, a small address like 0x1563fa4890cdce2f
    # might be parsed backwards or shifted!
    # Let's check the hex bytes of sBlk.s.id_table_start = 0x28d86be (Dec: 42829502).
    # Since the file size is 42829510, the ID table starts exactly 8 bytes before the end of the file.
    # These 8 bytes are: 1563fa4890cdce2f.
    # In a SquashFS image, the last 8 bytes are usually the pointer to the ID table!
    # The pointer is a 64-bit integer pointing to the ID table block start offset!
    # Let's decode 1563fa4890cdce2f:
    # If it is little endian, 1563fa4890cdce2f is: 0x2fcecd9048fa6315 (which is exactly what sasquatch printed!).
    # But wait, why would the pointer be 0x2fcecd9048fa6315 if the image size is only 42MB?
    # Ah!!!
    # Is it because the data is encrypted, or does it have OOB bytes embedded *inside* the UBI data area?
    # Wait, does the router use a non-standard SquashFS structure?
    # Or is there a custom vendor-specific SquashFS signature/obfuscation?
    # Let's check: does the original NAND dump "20260518_140638_TC58CVG2S0HRA.bin" have any OOB bytes?
    # Let's write a python script to inspect if every page in the NAND dump has OOB bytes!
    pass

if __name__ == "__main__":
    # Let's check the first page in the NAND dump
    path = "/home/recep/Masaüstü/Firmware/20260518_140638_TC58CVG2S0HRA.bin"
    with open(path, "rb") as f:
        # Read first 10 pages (4096 bytes each)
        for i in range(10):
            f.seek(i * 4096)
            page = f.read(4096)
            # Check if there are any repetitive patterns at the end of the page,
            # or if the page starts with standard UBI headers.
            # We already know that UBI Erase Count Header starts at 0x200000 (Dec: 2097152).
            # 2097152 / 4096 = 512.
            # So physical block 8 starts at offset 0x200000.
            # Let's print out the first 64 bytes of offset 0x200000.
            if i == 0:
                f.seek(0x200000)
                block_head = f.read(64)
                print(f"Block head at 0x200000: {block_head.hex()}")
                # UBI# magic is 55424923.
                # In little-endian, it is 23494255.
                # Here, we see it matches!
