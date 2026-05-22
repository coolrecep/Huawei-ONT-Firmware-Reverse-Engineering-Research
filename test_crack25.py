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

# Wait, why `file read head type err, type (559903)`?
# Our file has magic bytes at the beginning:
# 01 00 00 00 02 76 14 7e
# The 559903 in hex is 0x00088B1F. Wait... 8B 1F? 
# 1f 8b is gzip! So maybe the file is gzipped, not aescrypt2'd!
# Actually, the file header we saw earlier was `01 00 00 00 b9 a6 5a 19`. 
# Wait, let's copy hw_ctree.xml to /tmp again WITHOUT any modifications, just straight copy.

chan.send("cp /mnt/jffs2/hw_ctree.xml /tmp/test.xml\n")
recv_until(chan, "# ", timeout=5)

chan.send("hexdump -C /tmp/test.xml | head -4\n")
out = recv_until(chan, "# ", timeout=5)
print(out)

# Try gzip
chan.send("mv /tmp/test.xml /tmp/test.xml.gz\n")
recv_until(chan, "# ", timeout=5)
chan.send("gunzip /tmp/test.xml.gz\n")
out = recv_until(chan, "# ", timeout=5)
print(out)

client.close()
