def crop_squashfs():
    # The filesystem size is exactly 42829510 bytes.
    # Let's crop volume_4_extracted.squashfs to exactly this size so it is not corrupt!
    in_path = "/home/recep/Masaüstü/Firmware/extracted_partitions/volume_4_extracted.squashfs"
    out_path = "/home/recep/Masaüstü/Firmware/extracted_partitions/volume_4_final.squashfs"
    
    size = 42829510
    
    with open(in_path, "rb") as f_in:
        data = f_in.read(size)
        
    with open(out_path, "wb") as f_out:
        f_out.write(data)
        
    print(f"Cropped squashfs image to {out_path} ({len(data)} bytes).")

if __name__ == "__main__":
    crop_squashfs()
