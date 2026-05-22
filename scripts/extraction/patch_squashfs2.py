import struct
import sys

def patch(filename):
    with open(filename, 'r+b') as f:
        # Read the superblock
        f.seek(0)
        magic = f.read(4)
        if magic != b'hsqs':
            print("Not a standard SquashFS file!")
            return
            
        # Offset 26 is no_ids (unsigned short)
        f.seek(26)
        id_count = struct.unpack('<H', f.read(2))[0]
        print(f"Original ID count: {id_count}")
        
        # Offset 44 is id_table_start (long long)
        f.seek(44)
        id_table_start = struct.unpack('<Q', f.read(8))[0]
        print(f"Original ID table start: {id_table_start}")
        
        # We need to create a fake ID table.
        # id_table_start points to an array of 8-byte block pointers.
        # Since we just want it to pass, we can append a fake block.
        
        f.seek(0, 2)
        eof = f.tell()
        
        # Let's just set no_ids to 0! Wait, if no_ids is 0, sasquatch might not allocate ids.
        # But unsquashfs handles no_ids == 0? Usually it allocates no_ids.
        # Let's set it to 1, and make id_table_start point to a fake table we append at EOF.
        
        f.seek(26)
        f.write(struct.pack('<H', 1))
        
        f.seek(44)
        f.write(struct.pack('<Q', eof))
        
        # Write fake ID table pointer at EOF (8 bytes)
        f.seek(eof)
        f.write(struct.pack('<Q', eof + 8)) # Pointer to the compressed data block
        
        # Write fake compressed block for 1 ID
        # Uncompressed size is 4 bytes (for 1 uint32).
        # We can write an uncompressed block: bit 24 set to 1? Wait, squashfs block sizes...
        # Let's just write 0s and hope compression fails gracefully or we write an uncompressed block header.
        # In squashfs metadata blocks, the 2-byte header contains the size. 
        # MSB = 1 means uncompressed. Size = 4. Header = 0x8004.
        f.write(struct.pack('<H', 0x8004))
        f.write(struct.pack('<I', 0)) # ID 0
        
        print("Patched squashfs with fake ID table at EOF!")

patch(sys.argv[1])
