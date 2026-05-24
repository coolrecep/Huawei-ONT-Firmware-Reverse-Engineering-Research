@Echo off
echo set sh=WScript.CreateObject("WScript.Shell") >tmp.vbs
echo WScript.Sleep 1000 >>tmp.vbs
echo sh.SendKeys "open 192.168.100.1{ENTER}" >>tmp.vbs
echo WScript.Sleep 1000 >>tmp.vbs
echo sh.SendKeys "root{ENTER}" >>tmp.vbs
echo WScript.Sleep 1000 >>tmp.vbs
echo sh.SendKeys "admin{ENTER}" >>tmp.vbs
echo WScript.Sleep 1000 >>tmp.vbs
echo sh.SendKeys "su{ENTER}" >>tmp.vbs
echo WScript.Sleep 1000 >>tmp.vbs
echo sh.SendKeys "shell{ENTER}" >>tmp.vbs
echo WScript.Sleep 1000 >>tmp.vbs
echo sh.SendKeys "EquipMode.sh on{ENTER}" >>tmp.vbs
echo WScript.Sleep 3000 >>tmp.vbs
echo sh.SendKeys "exit{ENTER}" >>tmp.vbs
echo WScript.Sleep 1000 >>tmp.vbs
echo sh.SendKeys "reset{ENTER}" >>tmp.vbs
echo WScript.Sleep 1000 >>tmp.vbs
start telnet
cscript //nologo tmp.vbs
del tmp.vbs
timeout /t 5 /nobreak >nul
taskkill /IM telnet.exe /F >nul 2>&1