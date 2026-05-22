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

# Instead of running aescrypt2, we want to download aescrypt2 to run it locally or emulate it
chan.send("hexdump -v -e '16/1 \"%02x \" \"\\n\"' /bin/aescrypt2\n")
out = recv_until(chan, "# ", timeout=20)
lines = out.split('\n')
hex_data = []
for l in lines:
    if len(l.strip()) > 30 and "hexdump" not in l:
        hex_data.append(l.strip().replace(' ', ''))

bin_data = bytes.fromhex(''.join(hex_data))
with open("/home/recep/Masaüstü/Firmware/aescrypt2", "wb") as f:
    f.write(bin_data)
print(f"Downloaded aescrypt2, size: {len(bin_data)}")

client.close()
