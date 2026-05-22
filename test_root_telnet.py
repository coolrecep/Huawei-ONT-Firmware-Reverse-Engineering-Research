import pexpect

print("Testing telnet...")
try:
    child = pexpect.spawn('telnet 192.168.1.1 23')
    i = child.expect(['Login:', 'Login Name:', 'WAP>', pexpect.EOF, pexpect.TIMEOUT], timeout=5)
    if i == 0 or i == 1:
        child.sendline('root')
        j = child.expect(['Password:', pexpect.EOF, pexpect.TIMEOUT], timeout=5)
        if j == 0:
            child.sendline('admin') # try basic password
            print(child.before.decode() + child.after.decode())
    else:
        print(child.before.decode() if child.before else "No prompt")
except Exception as e:
    print(e)
