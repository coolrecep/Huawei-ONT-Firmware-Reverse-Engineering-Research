def extract_squashfs():
    # Let's extract the Squashfs image starting at 0x28c094 from volume_4.bin
    vol_path = "/home/recep/Masaüstü/Firmware/extracted_partitions/volume_4.bin"
    out_path = "/home/recep/Masaüstü/Firmware/extracted_partitions/volume_4_extracted.squashfs"
    
    offset = 2670740
    
    with open(vol_path, "rb") as f_in:
        f_in.seek(offset)
        # SquashFS size can be determined or we can just read the rest of the file
        data = f_in.read()
        
    with open(out_path, "wb") as f_out:
        f_out.write(data)
        
    print(f"Extracted squashfs image to {out_path} ({len(data)} bytes).")

if __name__ == "__main__":
    extract_squashfs()
