#!/usr/bin/env python3
import paramiko
import time

HOST     = "192.168.1.1"
USER     = "sUser"
PASSWORD = "EP!99R4HLH9E"

def recv_until(chan, markers, timeout=15):
    if isinstance(markers, str): markers = [markers]
    buf = b""
    start = time.time()
    while time.time() - start < timeout:
        if chan.recv_ready():
            buf += chan.recv(8192)
            decoded = buf.decode('utf-8', errors='replace')
            for m in markers:
                if m in decoded: return decoded
        elif chan.exit_status_ready(): break
        time.sleep(0.1)
    return buf.decode('utf-8', errors='replace')

def connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=15,
                   look_for_keys=False, allow_agent=False)
    chan = client.invoke_shell(width=220, height=50)
    time.sleep(2)
    out = recv_until(chan, ["WAP>", "Remove one session", "Enter the ID"], timeout=8)
    if "Remove one session" in out or "Enter the ID" in out:
        chan.send("1\n"); time.sleep(2); recv_until(chan, "WAP>", timeout=10)
    chan.send("su\n");    recv_until(chan, ["SU_WAP>"], timeout=8)
    chan.send("shell\n"); recv_until(chan, "# ", timeout=8)
    return client, chan

def run(chan, cmd, timeout=20):
    chan.send(cmd + "\n")
    return recv_until(chan, "# ", timeout)

def main():
    print("[*] Searching device for the 32-byte block...")
    client, chan = connect()
    
    # Let's search all readable files for a 32-byte string containing our known characters.
    # The characters are: E, P, !, 9, R, 4, H, L.
    # We will use grep to find any string of 32 characters that contains all of these.
    
    # We can write a tiny awk script to do this.
    awk_script = r"""
awk '
{
    for(i=1; i<=length($0)-31; i++) {
        sub_str = substr($0, i, 32)
        if (index(sub_str, "E") && index(sub_str, "P") && index(sub_str, "!") && 
            index(sub_str, "9") && index(sub_str, "R") && index(sub_str, "4") && 
            index(sub_str, "H") && index(sub_str, "L")) {
            print FILENAME ": " sub_str
        }
    }
}
'
"""
    run(chan, f"cat << 'EOF' > /tmp/search_block.awk\n{awk_script.strip()}\nEOF")
    
    print("[*] Scanning /etc, /var, /bin, /lib...")
    # we don't want to scan too much binary data with awk, it will be slow.
    # Let's use strings first and then pipe to awk.
    cmd = "find /etc /var /bin /lib /usr -type f -exec strings {} + | awk -f /tmp/search_block.awk"
    out = run(chan, cmd, timeout=60)
    print("=== RESULTS ===")
    print(out.strip()[-3000:])
    
    client.close()

if __name__ == "__main__":
    main()
