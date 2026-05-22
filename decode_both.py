def decode_both():
    filepath = "/home/recep/Masaüstü/Firmware/extracted_partitions/volume_4.bin"
    offsets = [2670740, 45502548]
    
    import struct
    with open(filepath, "rb") as f:
        for off in offsets:
            f.seek(off)
            header = f.read(32)
            magic, inodes, mkfs_time, block_size, fragments, compression, block_log, flags, no_ids, major, minor = struct.unpack(
                "<IIIIIHHHHHH", header
            )
            print(f"\nOffset: {hex(off)} (Dec: {off})")
            print(f"  Magic:       {hex(magic)}")
            print(f"  Inodes:      {inodes}")
            print(f"  Time:        {mkfs_time}")
            print(f"  Block Size:  {block_size}")
            print(f"  Fragments:   {fragments}")
            print(f"  Compression: {compression}")
            print(f"  Major.Minor: {major}.{minor}")

if __name__ == "__main__":
    decode_both()
