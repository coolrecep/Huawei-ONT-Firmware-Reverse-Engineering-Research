def find_hsqs():
    # Let's inspect where "hsqs" is in volume_4.bin
    filepath = "/home/recep/Masaüstü/Firmware/extracted_partitions/volume_4.bin"
    sig = b"hsqs"
    
    with open(filepath, "rb") as f:
        data = f.read()
        
    start = 0
    while True:
        idx = data.find(sig, start)
        if idx == -1:
            break
        print(f"hsqs found at offset {hex(idx)} (Dec: {idx})")
        # Print next 64 bytes of hex
        chunk = data[idx:idx+64]
        print(f"  Raw: {chunk.hex()}")
        start = idx + 1

if __name__ == "__main__":
    find_hsqs()
