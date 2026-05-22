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
            
        # Offset 26 is id_count (unsigned short)
        f.seek(26)
        id_count = struct.unpack('<H', f.read(2))[0]
        print(f"Original ID count: {id_count}")
        
        # Offset 72 is id_table_start (long long)
        f.seek(72)
        id_table_start = struct.unpack('<Q', f.read(8))[0]
        print(f"Original ID table start: {id_table_start}")
        
        # Offset 56 is root_inode (long long)
        f.seek(56)
        root_inode = struct.unpack('<Q', f.read(8))[0]
        print(f"Root inode: {root_inode}")
        
        # Let's fix the ID count to 1 to prevent sasquatch from allocating large buffers or seeking out of bounds
        f.seek(26)
        f.write(struct.pack('<H', 1))
        print("Set ID count to 1")
        
        # Optional: we can set id_table_start to a valid location if it's out of bounds, but let's see.

patch(sys.argv[1])
