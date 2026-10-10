def check_offsets():
    # The sBlk offsets (absolute in image):
    # sBlk.s.inode_table_start 0x28b6a70 (Dec: 42691184)
    # sBlk.s.directory_table_start 0x28c44aa (Dec: 42747050)
    # sBlk.s.fragment_table_start 0x28d6716 (Dec: 42821398)
    # sBlk.s.lookup_table_start 0x28d8629 (Dec: 42829353)
    # sBlk.s.id_table_start 0x28d86be (Dec: 42829502)
    # Filesystem size: 42829510 bytes (0x28d86c6)
    #
    # Wait, the id_table_start is at 0x28d86be.
    # 0x28d86be is only 8 bytes before the end of the file (0x28d86c6 - 0x28d86be = 8 bytes)!
    # But wait, an ID table should contain a list of pointers to compressed ID blocks!
    # With 30 IDs, we have 30 * 4 = 120 bytes of ID pointers. So it can't fit in 8 bytes!
    # This means the image size is actually LARGER than the header says, or the block reads failed because of some other issue.
    # Wait! Let's check volume_4.bin size. The size of volume_4.bin is 84058112 bytes.
    # We extracted fs1 starting at 2670740.
    # The physical NAND dump of TC58CVG2S0HRA has OOB (ECC) bytes every 4096 bytes if it was NOT cleaned.
    # Wait, the file we read was 20260518_140638_TC58CVG2S0HRA.bin, which is 536870912 bytes (512MB).
    # TC58CVG2S0HRA is a 4Gbit (512MB) SPI-NAND flash chip with 2048 blocks, 64 pages per block, 4096 bytes page size + 256 bytes OOB size.
    # Wait! If it's a 512MB dump, then the raw NAND dump size including OOB would be:
    # 2048 blocks * 64 pages/block * 4352 bytes/page = 570425344 bytes.
    # But the file "/home/recep/Masaüstü/Firmware/20260518_140638_TC58CVG2S0HRA.bin" is exactly 536870912 bytes!
    # 536870912 bytes is exactly 512MB (2048 blocks * 64 pages/block * 4096 bytes/page).
    # This means it is ALREADY a clean dump (no OOB bytes)!
    # Then why did sasquatch/unsquashfs complain about EOF or read corruption?
    # Let's inspect the ID table start block at 0x28d86be.
    path = "/home/recep/Masaüstü/Firmware/extracted_partitions/fs1.squashfs"
    with open(path, "rb") as f:
        f.seek(0x28d86be)
        data = f.read(100)
        print(f"ID table bytes (Hex): {data.hex()}")

if __name__ == "__main__":
    check_offsets()
