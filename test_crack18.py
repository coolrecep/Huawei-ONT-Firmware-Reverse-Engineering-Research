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

# The second repo uses:
# aescrypt2 1 hw_ctree.xml hw_ctree.decrypted.xml
# then injects <X_HW_WebUserInfoInstance InstanceID="69" UserName="fakeadmin" Password="..." UserLevel="0" Enable="1" .../>
# and uploads back.
# We CANNOT decrypt on router because of aescrypt2 permission!
# But wait, if we can run python/C code, maybe we can call the decryption function ourselves via LD_PRELOAD or dlsym!
# Oh, we tried that locally and it failed with ELFCLASS32. Wait, the router is 32-bit ARM.
# We can compile a 32-bit ARM binary that calls dlsym() on /bin/aescrypt2 or libhw_smp_capi.so and executes it ON THE ROUTER!

chan.send("cat /proc/cpuinfo\n")
out = recv_until(chan, "# ", timeout=5)
print(out)

client.close()
