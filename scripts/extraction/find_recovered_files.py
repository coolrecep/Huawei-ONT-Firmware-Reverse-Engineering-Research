import os

def find_files(root_dir):
    targets = ["smp", "ssmp", "capi", "aescrypt", "decrypt"]
    
    print(f"Searching for files matching targets in {root_dir}:")
    for root, dirs, files in os.walk(root_dir):
        for f in files:
            f_lower = f.lower()
            for t in targets:
                if t in f_lower:
                    full_path = os.path.join(root, f)
                    print(f"  - Found: {full_path} (Size: {os.path.getsize(full_path)} bytes)")

if __name__ == "__main__":
    find_files("/home/recep/Masaüstü/Firmware/squashfs-root-recovered")
