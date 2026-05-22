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

# Wait, decrypt_test just called /bin/aescrypt2 using execve. But /bin/aescrypt2 is -r-xr-x--- owned by srv_ssmp:service.
# Our user srv_clid is in the `service` group, but aescrypt2 permissions are 550, which means group has READ and EXECUTE.
# So execve() shouldn't be failing due to file permissions. 
# Oh, it outputted "<hw_ssp_ctool.c:450>file read head type err, type (559903)" earlier when we ran it from /var !
# That means it successfully executed, but failed because /tmp/hw_ctree.xml wasn't a valid aescrypt file!
# Let's check hw_ctree.xml file type via hexdump again.

chan.send("hexdump -C /mnt/jffs2/hw_ctree.xml | head -4\n")
out = recv_until(chan, "# ", timeout=5)
print(out)

# Is there another file we should crack? The github repo cracks hw_ctree.xml.
# Maybe `aescrypt2` needs different mode flag?
# Try mode 0? 
chan.send("/bin/aescrypt2 0 /mnt/jffs2/hw_ctree.xml /tmp/enc.xml\n")
out = recv_until(chan, "# ", timeout=5)
print(out)

client.close()
