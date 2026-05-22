def extract_both_squashfs():
    vol_path = "/home/recep/Masaüstü/Firmware/extracted_partitions/volume_4.bin"
    
    # Filesystem 1 details: size 42829510 bytes, offset 2670740
    # Filesystem 2 details: let's read the rest from offset 45502548
    
    with open(vol_path, "rb") as f:
        # Extract FS 1
        f.seek(2670740)
        fs1 = f.read(42829510)
        with open("/home/recep/Masaüstü/Firmware/extracted_partitions/fs1.squashfs", "wb") as f_out:
            f_out.write(fs1)
        print(f"Saved fs1.squashfs ({len(fs1)} bytes)")
        
        # Extract FS 2
        f.seek(45502548)
        fs2 = f.read()
        with open("/home/recep/Masaüstü/Firmware/extracted_partitions/fs2.squashfs", "wb") as f_out:
            f_out.write(fs2)
        print(f"Saved fs2.squashfs ({len(fs2)} bytes)")

if __name__ == "__main__":
    extract_both_squashfs()
