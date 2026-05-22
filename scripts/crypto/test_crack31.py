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

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASSWORD, timeout=10,
               look_for_keys=False, allow_agent=False)
chan = client.invoke_shell(width=220, height=50)
time.sleep(2)
out = recv_until(chan, ["WAP>", "Remove one session", "Enter the ID"], timeout=8)
if "Remove one session" in out or "Enter the ID" in out:
    chan.send("1\n")
    time.sleep(2)
    recv_until(chan, "WAP>", timeout=10)

chan.send("su\n")
recv_until(chan, ["SU_WAP>", "success"], timeout=8)
chan.send("shell\n")
recv_until(chan, "# ", timeout=8)

# Wait, we know `hw_ctree.xml.enc` starts with `01 00 00 00 88 d9 48 31 3c ca 32 38`.
# Does aescrypt2 encrypt things with that header? Let's encrypt a dummy file and see.
chan.send("echo test > /tmp/dummy.txt\n")
recv_until(chan, "# ", timeout=5)

chan.send("/bin/aescrypt2 0 /tmp/dummy.txt /tmp/dummy.enc\n")
recv_until(chan, "# ", timeout=5)

chan.send("hexdump -C /tmp/dummy.enc\n")
out = recv_until(chan, "# ", timeout=5)
print(out)

client.close()
