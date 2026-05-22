def read_squashfs_headers():
    filepath = "/home/recep/Masaüstü/Firmware/20260518_140638_TC58CVG2S0HRA.bin"
    offsets = [205574228, 287449236, 331927636, 478290068]
    
    with open(filepath, "rb") as f:
        for off in offsets:
            f.seek(off)
            header = f.read(64)
            print(f"\nSquashFS Signature at {hex(off)} (Dec: {off}):")
            print(f"  Header (Hex): {header.hex()}")
            print(f"  Magic: {header[:4]}")
            # Squashfs structure fields:
            #   unsigned int s_magic;
            #   unsigned int inodes;
            #   unsigned int mkfs_time;
            #   unsigned int block_size;
            #   unsigned int fragments;
            #   unsigned short compression;
            #   unsigned short block_log;
            #   unsigned short flags;
            #   unsigned short no_ids;
            #   unsigned short s_major;
            #   unsigned short s_minor;
            # Let's inspect s_magic and other values
            import struct
            if len(header) >= 32:
                try:
                    magic, inodes, mkfs_time, block_size, fragments, compression, block_log, flags, no_ids, major, minor = struct.unpack(
                        "<IIIIIHHHHHH", header[:32]
                    )
                    print(f"    Decoded: Magic={hex(magic)}, Inodes={inodes}, Time={mkfs_time}, BlockSize={block_size}, Fragments={fragments}, Comp={compression}, Major={major}, Minor={minor}")
                except Exception as e:
                    print(f"    Failed to decode: {e}")

if __name__ == "__main__":
    read_squashfs_headers()
