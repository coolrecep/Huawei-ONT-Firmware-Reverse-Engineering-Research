def search_squashfs_offsets():
    filepath = "/home/recep/Masaüstü/Firmware/20260518_140638_TC58CVG2S0HRA.bin"
    sig = b"hsqs"
    
    with open(filepath, "rb") as f:
        # Search Squashfs offsets
        # We know that volume_9.bin does NOT have SquashFS.
        # Which volume has it?
        # Let's check which volumes have the hsqs magic!
        import glob
        for name in glob.glob("/home/recep/Masaüstü/Firmware/extracted_partitions/*.bin"):
            with open(name, "rb") as f_vol:
                data = f_vol.read()
                idx = data.find(sig)
                if idx != -1:
                    print(f"File {name} has SquashFS magic at offset {hex(idx)} (Dec: {idx})!")
                    
if __name__ == "__main__":
    search_squashfs_offsets()
