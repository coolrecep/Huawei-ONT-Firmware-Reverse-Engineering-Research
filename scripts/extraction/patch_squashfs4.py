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
            
        f.seek(26)
        id_count = struct.unpack('<H', f.read(2))[0]
        print(f"Original ID count: {id_count}")
        
        # Set no_ids to 1, but do NOT change id_table_start!
        f.seek(26)
        f.write(struct.pack('<H', 1))
        
        print("Patched squashfs with ID count = 1!")

if __name__ == '__main__':
    patch(sys.argv[1])
