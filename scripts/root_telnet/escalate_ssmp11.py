#!/usr/bin/env python3
"""
Phase 11: Find exact 'set userpasswd' syntax via WAP CLI tab completion.
Also: use 'su' from SU_WAP which has different behavior than shell su.
Key info collected:
- SN: 485754437C07DEA5
- ACS URL: http://acs.superonline.net:8015/cwmpWeb/WGCPEMgt
- ACS Username: superonlineacs
- Hardware: 1E8E.A
- Firmware: V500R021C00SPC128B125

The 'set userpasswd' needs SOME parameter. Let's probe with '?'
and also try the WAP su command to see if it switches users.
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

def wap_probe(chan, cmd):
    """Send command + ? to probe syntax."""
    chan.send(cmd + " ?\n")
    out = recv_until(chan, "SU_WAP>", timeout=8)
    lines = [l.strip() for l in out.strip().split('\n') if l.strip()]
    for l in lines:
        if '?' not in l and cmd[:15] not in l:
            print(f"  {l}")
    return out

def wap_cmd(chan, cmd, timeout=8):
    chan.send(cmd + "\n")
    out = recv_until(chan, "SU_WAP>", timeout)
    lines = [l.strip() for l in out.strip().split('\n') if l.strip()]
    for l in lines:
        if cmd[:15] not in l:
            print(f"  {l}")
    return out

def main():
    print("=" * 62)
    print("  HG8245X6 - WAP CLI Syntax Discovery for userpasswd")
    print("=" * 62)

    client, chan = connect_to_wap()

    # ── 1. Probe 'set userpasswd' parameters ──────────────────
    print("[*] Probing 'set userpasswd' syntax:")
    wap_probe(chan, "set userpasswd")

    print("\n[*] Trying 'set userpasswd' with username as first param:")
    wap_probe(chan, "set userpasswd srv_ssmp")

    print("\n[*] Trying 'set userpasswd' with 'user' keyword:")
    wap_probe(chan, "set userpasswd user")

    print("\n[*] Trying 'set userpasswd' with 'name' keyword:")
    wap_probe(chan, "set userpasswd name")

    print("\n[*] Trying different WAP su command:")
    # WAP's 'su' is to switch to super-user within WAP, not Linux su
    # What does su in WAP context do?
    chan.send("su ?\n")
    out = recv_until(chan, "SU_WAP>", timeout=5)
    print(f"  su ?: {out.strip()[-200:]}")

    # ── 2. Try connecting as admin (different user) ────────────
    # The WAP CLI is accessed as sUser -> su gives SU_WAP>
    # SU_WAP is the privileged WAP user (srv_ssmp level?)
    # Let's check what user SU_WAP runs as
    chan.send("shell\n")
    out = recv_until(chan, "# ", timeout=5)
    chan.send("id\n")
    out = recv_until(chan, "# ", timeout=5)
    print(f"\n[*] Shell user after SU_WAP: {out.strip()}")
    chan.send("cat /proc/self/status | grep -E 'Uid|Gid|Cap'\n")
    out = recv_until(chan, "# ", timeout=5)
    print(f"  Process info: {out.strip()}")
    
    # ── 3. Can we exec ssmp binary directly? ─────────────────
    print("\n[*] Running /bin/ssmp directly:")
    chan.send("/bin/ssmp --help 2>&1 | head -10\n")
    out = recv_until(chan, "# ", timeout=10)
    print(f"  {out.strip()[-300:]}")
    
    # ── 4. Try 'su ssmp' and 'su srv_ssmp' from shell as SU_WAP shell
    print("\n[*] Trying su ssmp (different form) from SU_WAP shell:")
    chan.send("su ssmp\n")
    out = recv_until(chan, ["Password", "# ", "$ "], timeout=5)
    print(f"  su ssmp: {repr(out.strip()[-100:])}")
    if "Password" in out:
        chan.send("\n")
        out = recv_until(chan, ["# ", "$ ", "incorrect", "WAP"], timeout=5)
        print(f"  Result: {repr(out.strip()[-100:])}")

    # ── 5. Check if WAP CLI 'su' command takes user argument ──
    chan.send("exit\n")
    recv_until(chan, "SU_WAP>", timeout=5)
    
    print("\n[*] Trying WAP CLI 'su srv_ssmp':")
    wap_cmd(chan, "su srv_ssmp")
    
    print("\n[*] Trying WAP CLI 'su ssmp':")
    wap_cmd(chan, "su ssmp")

    # ── 6. Look at 'set userpasswd' from WAP CLI more carefully ─
    print("\n[*] Try set userpasswd with just password (current user):")
    # Maybe it changes current user's password?
    chan.send("set userpasswd Admin1234!\n")
    out = recv_until(chan, ["SU_WAP>", "success", "fail", "ERROR", "Retype", "New"], timeout=10)
    print(f"  Result: {repr(out.strip()[-300:])}")
    if "Retype" in out or "New" in out or "confirm" in out.lower():
        print("  [*] Interactive prompts detected! Sending confirm...")
        chan.send("Admin1234!\n")
        out = recv_until(chan, ["SU_WAP>", "success", "fail"], timeout=5)
        print(f"  Confirm: {repr(out.strip()[-200:])}")
    
    # If success, go to shell and try su srv_ssmp 
    # (actually set userpasswd likely changes our OWN password not srv_ssmp's)
    
    # ── 7. Check the 'display file' command for config ────────
    print("\n[*] display file:")
    wap_cmd(chan, "display file ?")
    
    # ── 8. Check WAP prompt for account management ────────────
    print("\n[*] Checking WAP 'account' / 'user' commands:")
    for cmd in ["account", "user", "adduser", "newuser", "useradd", "usermod"]:
        chan.send(f"{cmd}\n")
        out = recv_until(chan, "SU_WAP>", timeout=3)
        if "not exist" not in out.lower() and "ERROR" not in out:
            print(f"  [+] '{cmd}' works: {out.strip()[-200:]}")

    # ── 9. Look at 'wap list' - WAP process list ─────────────
    print("\n[*] wap list:")
    wap_cmd(chan, "wap list")

    # ── 10. Check what 'session cli' reveals ──────────────────
    print("\n[*] More session cli data (looking for ssmp credentials):")
    chan.send("session cli\n")
    out = recv_until(chan, ["SU_WAP>", "SSMP", "ssmp", "password", "Password"], timeout=30)
    # Search for password-related lines
    lines = out.split('\n')
    relevant = [l.strip() for l in lines if any(k in l.lower() for k in ['pass', 'key', 'secret', 'token', 'auth', 'user', 'admin', 'login', 'ssmp'])]
    for l in relevant[:30]:
        print(f"  {l}")
    
    # Wait for SU_WAP> if still outputting
    recv_until(chan, "SU_WAP>", timeout=30)

    client.close()
    print("\n[*] Session closed.")

if __name__ == "__main__":
    main()
