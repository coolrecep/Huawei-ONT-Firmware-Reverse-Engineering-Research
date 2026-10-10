def read_more_bytes():
    # Let's inspect bytes in volume_4.bin starting from offset 2670740 + 42829510 onwards (up to 1000 bytes)
    filepath = "/home/recep/Masaüstü/Firmware/extracted_partitions/volume_4.bin"
    offset = 2670740 + 42829510
    
    with open(filepath, "rb") as f:
        f.seek(offset)
        data = f.read(128)
        print(f"Bytes after the calculated SquashFS size (Hex):")
        print(data.hex())

if __name__ == "__main__":
    read_more_bytes()
