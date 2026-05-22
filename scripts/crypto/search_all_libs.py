import os

root_dir = '/home/recep/Masaüstü/Firmware/squashfs-root-recovered'

CHECKS_32 = [
    (1,57),(2,72),(3,82),(4,69),(7,57),(10,33),(11,80),
    (15,52),(18,72),(19,69),(22,76),(30,57)
]

def search_file(filepath):
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
    except Exception:
        return
        
    best_score = 0
    best_offset = -1
    
    for offset in range(len(data) - 32):
        b = data[offset:offset+32]
        score = sum(1 for idx, val in CHECKS_32 if b[idx] == val)
        if score > best_score:
            best_score = score
            best_offset = offset
        if score >= 9:
            print(f"\n[+] MATCH in {filepath}")
            print(f"    Score {score}/12 at offset {offset} (0x{offset:x})")
            print(f"    HEX: {' '.join(f'{x:02x}' for x in b)}")
            print(f"    ASC: {''.join(chr(x) if 32<=x<127 else '.' for x in b)}")

for root, dirs, files in os.walk(root_dir):
    for name in files:
        filepath = os.path.join(root, name)
        # only search regular files, avoid symlinks if possible
        if os.path.isfile(filepath) and not os.path.islink(filepath):
            search_file(filepath)

print("Search complete.")
