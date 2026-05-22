import os
import sys

root_dir = '/home/recep/Masaüstü/Firmware/squashfs-root-recovered'

CHECKS_64 = [
    (8, 69),   # E
    (23, 80),  # P
    (20, 33),  # !
    (3, 57),   # 9
    (60, 57),  # 9
    (7, 82),   # R
    (30, 52),  # 4
    (37, 72),  # H
    (44, 76),  # L
    (5, 72),   # H
    (15, 57),  # 9
    (39, 69)   # E
]

print("Searching all files for 64-byte table...")
found = False

for root, dirs, files in os.walk(root_dir):
    for name in files:
        filepath = os.path.join(root, name)
        if not os.path.islink(filepath) and os.path.isfile(filepath):
            try:
                with open(filepath, 'rb') as f:
                    data = f.read()
            except: continue
            
            for offset in range(len(data) - 64):
                b = data[offset:offset+64]
                score = sum(1 for idx, val in CHECKS_64 if b[idx] == val)
                if score >= 10:
                    print(f"MATCH FOUND in {filepath} at offset {offset} score {score}/12")
                    print([hex(x) for x in b])
                    found = True
                    break
        if found: break
    if found: break

if not found:
    print("Not found anywhere.")
