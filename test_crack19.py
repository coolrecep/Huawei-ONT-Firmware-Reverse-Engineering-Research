import paramiko
import time
import base64

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

def run(chan, cmd, timeout=20):
    chan.send(cmd + "\n")
    return recv_until(chan, "# ", timeout)

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

with open("/home/recep/Masaüstü/Firmware/decrypt_test", "rb") as f:
    bin_data = f.read()

b64_data = base64.b64encode(bin_data).decode('utf-8')

run(chan, "cat << 'EOF' > /tmp/decrypt_test.b64")
chunk_size = 500
for i in range(0, len(b64_data), chunk_size):
    chan.send(b64_data[i:i+chunk_size] + "\n")
    time.sleep(0.05)
run(chan, "EOF")

awk_decoder = r"""
awk 'BEGIN {
    b64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    for (i=0; i<64; i++) {
        val[substr(b64, i+1, 1)] = i
    }
}
{
    len = length($0)
    for (i=1; i<=len; i+=4) {
        c1 = substr($0, i, 1); c2 = substr($0, i+1, 1)
        c3 = substr($0, i+2, 1); c4 = substr($0, i+3, 1)
        if (c1 == "=") break
        v1 = val[c1]; v2 = val[c2]
        v3 = (c3 == "=") ? 0 : val[c3]
        v4 = (c4 == "=") ? 0 : val[c4]
        
        b1 = lshift(v1, 2) + rshift(v2, 4)
        b2 = lshift(and(v2, 15), 4) + rshift(v3, 2)
        b3 = lshift(and(v3, 3), 6) + v4
        
        printf "%c", b1
        if (c3 != "=") printf "%c", b2
        if (c4 != "=") printf "%c", b3
    }
}' /tmp/decrypt_test.b64 > /tmp/decrypt_test
"""
run(chan, awk_decoder)

run(chan, "chmod +x /tmp/decrypt_test")
run(chan, "cp /mnt/jffs2/hw_ctree.xml /tmp/hw_ctree.xml")

out = run(chan, "/tmp/decrypt_test")
print("decrypt_test execution result:")
print(out)

out = run(chan, "ls -la /tmp/hw_ctree.decrypted.xml")
print("ls result:")
print(out)

out = run(chan, "head -20 /tmp/hw_ctree.decrypted.xml")
print("head result:")
print(out)

client.close()
