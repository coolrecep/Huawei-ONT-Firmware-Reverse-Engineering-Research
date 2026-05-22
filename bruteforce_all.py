import os

root_dir = '/home/recep/Masaüstü/Firmware/squashfs-root-recovered'

CHECKS_32 = [
    (1,57),(2,72),(3,82),(4,69),(7,57),(10,33),(11,80),
    (15,52),(18,72),(19,69),(22,76),(30,57)
]

print("Bruteforcing all files for XOR/ADD/SUB table...")
found = False

for root, dirs, files in os.walk(root_dir):
    for name in files:
        filepath = os.path.join(root, name)
        if not os.path.islink(filepath) and os.path.isfile(filepath):
            try:
                with open(filepath, 'rb') as f:
                    data = f.read()
            except: continue
            
            for K in range(256):
                xor_checks = [(idx, val ^ K) for idx, val in CHECKS_32]
                add_checks = [(idx, (val - K) % 256) for idx, val in CHECKS_32]
                sub_checks = [(idx, (val + K) % 256) for idx, val in CHECKS_32]
                
                for offset in range(len(data) - 32):
                    b = data[offset:offset+32]
                    
                    if sum(1 for idx, val in xor_checks if b[idx] == val) >= 12:
                        print(f"MATCH XOR K={K} in {filepath} at offset {offset}")
                        found = True; break
                    if sum(1 for idx, val in add_checks if b[idx] == val) >= 12:
                        print(f"MATCH ADD K={K} in {filepath} at offset {offset}")
                        found = True; break
                    if sum(1 for idx, val in sub_checks if b[idx] == val) >= 12:
                        print(f"MATCH SUB K={K} in {filepath} at offset {offset}")
                        found = True; break
                if found: break
        if found: break
    if found: break

if not found:
    print("Not found anywhere.")
