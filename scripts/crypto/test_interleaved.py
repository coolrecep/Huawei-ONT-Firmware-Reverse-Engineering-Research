data = open('/home/recep/Masaüstü/Firmware/squashfs-root-recovered/bin/ssmp', 'rb').read()

CHECKS_32 = [
    (1,57),(2,72),(3,82),(4,69),(7,57),(10,33),(11,80),
    (15,52),(18,72),(19,69),(22,76),(30,57)
]

print("Searching for interleaved table...")

for stride in [2, 4, 8]:
    print(f"Testing stride {stride}...")
    table_size = 32 * stride
    for offset in range(len(data) - table_size):
        b = data[offset:offset+table_size]
        score = sum(1 for idx, val in CHECKS_32 if b[idx * stride] == val)
        if score >= 10:
            print(f"MATCH stride {stride} at offset {offset} (0x{offset:x}) score {score}")

print("Done.")
