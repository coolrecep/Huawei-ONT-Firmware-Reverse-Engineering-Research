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

# we can use our decrypt_test but modify it to call `set userpasswd srv_ssmp Admin1234!`? No wait.
# Our decrypt_test runs under `srv_clid`. Wait, no, we can run /bin/aescrypt2 as srv_clid? Yes, we did!
# But it failed with type err. Why did the crack repo say `aescrypt2 1 hw_ctree.xml hw_ctree.decrypted.xml`?
# In HG8245Q2, it worked. In our HG8245X6, it gives a type err.
# Is there an alternative decryption command?
# Let's search the filesystem for anything containing `aescrypt` or `decrypt`
chan.send("find / -type f -name '*crypt*' -o -name '*decrypt*' 2>/dev/null\n")
out = recv_until(chan, "# ", timeout=10)
print("Files with crypt/decrypt in name:")
print(out)

chan.send("grep -r aescrypt /bin /sbin /usr/bin /usr/sbin 2>/dev/null | head -10\n")
out = recv_until(chan, "# ", timeout=10)
print("Files containing aescrypt:")
print(out)

client.close()
