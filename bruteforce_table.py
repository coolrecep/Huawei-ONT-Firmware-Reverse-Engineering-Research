import struct
import zlib

data = open('/home/recep/Masaüstü/Firmware/squashfs-root-recovered/bin/ssmp', 'rb').read()

CHECKS_32 = [
    (1,57),(2,72),(3,82),(4,69),(7,57),(10,33),(11,80),
    (15,52),(18,72),(19,69),(22,76),(30,57)
]

print(f"Searching for 32-byte block with XOR or ADD encoding...")
for K in range(256):
    # Try XOR
    xor_checks = [(idx, val ^ K) for idx, val in CHECKS_32]
    # Try ADD (val - K) % 256
    add_checks = [(idx, (val - K) % 256) for idx, val in CHECKS_32]
    # Try SUB (val + K) % 256
    sub_checks = [(idx, (val + K) % 256) for idx, val in CHECKS_32]
    
    for offset in range(len(data) - 32):
        b = data[offset:offset+32]
        
        # Check XOR
        if sum(1 for idx, val in xor_checks if b[idx] == val) >= 12:
            print(f"MATCH XOR K={K} at offset {offset} (0x{offset:x})")
            print([hex(x) for x in b])
        
        # Check ADD
        if sum(1 for idx, val in add_checks if b[idx] == val) >= 12:
            print(f"MATCH ADD K={K} at offset {offset} (0x{offset:x})")
            print([hex(x) for x in b])
            
        # Check SUB
        if sum(1 for idx, val in sub_checks if b[idx] == val) >= 12:
            print(f"MATCH SUB K={K} at offset {offset} (0x{offset:x})")
            print([hex(x) for x in b])

print("Done.")
