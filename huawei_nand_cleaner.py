#!/usr/bin/env python3
"""
Huawei HG8245X6 (ve benzeri) SPI-NAND OOB/ECC Temizleme Aracı
Bu araç, donanımsal okuyucu ile alınmış ham bir NAND dökümünün (firmware.bin) 
aralarına serpiştirilmiş donanımsal OOB (Out-of-Band) çöplerini ayıklayarak 
dosyayı binwalk ile açılabilir (ardışık) hale getirir.
"""

import sys
import os

def clean_nand_dump(input_file, output_file, page_size=4096, oob_size=256):
    # Toplam fiziksel okuma bloğu (Asıl Veri + Çöp Veri)
    block_size = page_size + oob_size
    
    if not os.path.exists(input_file):
        print(f"[HATA] Dosya bulunamadı: {input_file}")
        sys.exit(1)
        
    file_size = os.path.getsize(input_file)

    print(f"[*] Hedef Dosya: {input_file} ({file_size / (1024*1024):.2f} MB)")
    print(f"[*] Sayfa (Page) Boyutu: {page_size} bayt")
    print(f"[*] OOB (ECC) Boyutu: {oob_size} bayt")
    print(f"[*] Temizleniyor, lütfen bekleyin...\n")

    processed_bytes = 0

    with open(input_file, 'rb') as f_in, open(output_file, 'wb') as f_out:
        while True:
            # Fiziksel çipten (Veri + OOB) kadar oku
            chunk = f_in.read(block_size)
            
            if not chunk:
                break
                
            # Eğer son satır sayfa boyutundan küçükse olduğu gibi yaz
            if len(chunk) < page_size:
                f_out.write(chunk)
                break
                
            # Sadece asıl veriyi (page_size kadar) yeni dosyaya yaz, geri kalanını (oob) at!
            f_out.write(chunk[:page_size])
            
            processed_bytes += len(chunk)
            
            # İlerleme durumu
            if processed_bytes % (block_size * 5000) == 0:
                print(f"    ... %{int((processed_bytes/file_size)*100)} tamamlandı")

    print(f"\n[+] MUHTEŞEM! İşlem tamam.")
    print(f"[+] Temizlenmiş Dosya: {output_file}")
    print(f"[!] Artık bu komutu çalıştırabilirsiniz: binwalk -e {output_file}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Kullanım: python3 huawei_nand_cleaner.py <ham_firmware.bin> <temiz_firmware.bin>")
        sys.exit(1)

    in_file = sys.argv[1]
    out_file = sys.argv[2]
    
    # Huawei HG8245X6 standart değerleri
    clean_nand_dump(in_file, out_file, page_size=4096, oob_size=256)
