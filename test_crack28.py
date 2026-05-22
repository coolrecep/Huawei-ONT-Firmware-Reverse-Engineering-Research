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

# we can use cfgtool to dump the decrypted xml directly maybe?
# Remember we saw cfgtool options: cfgtool gettofile deftree InternetGatewayDevice /tmp/dump.xml
# wait, if the file is decrypted, maybe we can upload a modified version using `cfgtool batch` ?
chan.send("cfgtool\n")
out = recv_until(chan, "# ", timeout=5)
print(out)

chan.send("cfgtool batch ?\n")
out = recv_until(chan, "# ", timeout=5)
print(out)

# Or maybe just upload hw_ctree.xml in its RAW form and see if the router accepts it?
# In HG8245Q2, he encrypts it via aescrypt2. But our router aescrypt2 gives "head type err".
# Maybe our router does NOT use aescrypt2 for hw_ctree.xml anymore.
# Maybe hw_ctree.xml on this firmware uses a different encryption (hence the type error from aescrypt2)
# Wait, hw_ctree.xml header is `01 00 00 00 02 76 14 7e ...`
# Let's check another config command: backup configuration from web interface.
# Does the router have a way to backup config to USB?

client.close()
