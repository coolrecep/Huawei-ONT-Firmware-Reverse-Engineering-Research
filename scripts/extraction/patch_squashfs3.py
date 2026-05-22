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
        
        f.seek(48)
        id_table_start = struct.unpack('<Q', f.read(8))[0]
        print(f"Original ID table start: {id_table_start}")
        
        f.seek(0, 2)
        eof = f.tell()
        
        # Set no_ids to 1
        f.seek(26)
        f.write(struct.pack('<H', 1))
        
        # Set id_table_start to eof
        f.seek(48)
        f.write(struct.pack('<Q', eof))
        
        # Write fake ID table pointer at EOF
        f.seek(eof)
        f.write(struct.pack('<Q', eof + 8))
        
        # Write fake compressed block for 1 ID
        f.write(struct.pack('<H', 0x8004))
        f.write(struct.pack('<I', 0))
        
        print("Patched squashfs with fake ID table at EOF!")

if __name__ == '__main__':
    patch(sys.argv[1])
