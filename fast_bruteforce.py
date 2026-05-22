import os
import sys

root_dir = '/home/recep/Masaüstü/Firmware/squashfs-root-recovered'

CHECKS_32 = [
    (1,57),(2,72),(3,82),(4,69),(7,57),(10,33),(11,80),
    (15,52),(18,72),(19,69),(22,76),(30,57)
]

print("Fast bruteforcing all files for XOR/ADD/SUB table...")
found = False

for root, dirs, files in os.walk(root_dir):
    for name in files:
        filepath = os.path.join(root, name)
        if not os.path.islink(filepath) and os.path.isfile(filepath):
            try:
                with open(filepath, 'rb') as f:
                    data = f.read()
            except: continue
            
            for offset in range(len(data) - 32):
                b = data[offset:offset+32]
                
                # Check XOR
                k_xor = b[1] ^ 57
                if all(b[idx] ^ k_xor == val for idx, val in CHECKS_32):
                    print(f"MATCH XOR K={k_xor} in {filepath} at offset {offset} (0x{offset:x})")
                    found = True; break
                
                # Check ADD (b[idx] = (val + K) % 256)
                k_add = (b[1] - 57) % 256
                if all((b[idx] - k_add) % 256 == val for idx, val in CHECKS_32):
                    print(f"MATCH ADD K={k_add} in {filepath} at offset {offset} (0x{offset:x})")
                    found = True; break
                    
                # Check SUB (b[idx] = (val - K) % 256) -> val = (b[idx] + K) % 256
                k_sub = (57 - b[1]) % 256
                if all((b[idx] + k_sub) % 256 == val for idx, val in CHECKS_32):
                    print(f"MATCH SUB K={k_sub} in {filepath} at offset {offset} (0x{offset:x})")
                    found = True; break
                    
            if found: break
    if found: break

if not found:
    print("Not found anywhere.")
