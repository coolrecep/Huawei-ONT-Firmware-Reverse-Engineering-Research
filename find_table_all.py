import os
import sys

root_dir = '/home/recep/Masaüstü/Firmware/squashfs-root-recovered'

CHECKS_32 = [
    (1,57),(2,72),(3,82),(4,69),(7,57),(10,33),(11,80),
    (15,52),(18,72),(19,69),(22,76),(30,57)
]

print("Searching all files for the array...")
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
                if sum(1 for idx, val in CHECKS_32 if b[idx] == val) >= 12:
                    print(f"MATCH FOUND in {filepath} at offset {offset}")
                    print([hex(x) for x in b])
                    found = True
                    break
        if found: break
    if found: break

if not found:
    print("Not found anywhere.")
