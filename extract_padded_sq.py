def extract_expanded_squashfs():
    # Let's read 42829510 + 2048 bytes of data from offset 2670740 in volume_4.bin
    vol_path = "/home/recep/Masaüstü/Firmware/extracted_partitions/volume_4.bin"
    out_path = "/home/recep/Masaüstü/Firmware/extracted_partitions/fs1_padded.squashfs"
    
    offset = 2670740
    size = 42829510 + 2048
    
    with open(vol_path, "rb") as f_in:
        f_in.seek(offset)
        data = f_in.read(size)
        
    with open(out_path, "wb") as f_out:
        f_out.write(data)
        
    print(f"Extracted expanded squashfs image to {out_path} ({len(data)} bytes).")

if __name__ == "__main__":
    extract_expanded_squashfs()
