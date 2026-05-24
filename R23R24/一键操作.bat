@Echo off
echo set sh=WScript.CreateObject("WScript.Shell") >tmp.vbs
echo WScript.Sleep 1000 >>tmp.vbs
echo sh.SendKeys "open 192.168.100.1{ENTER}" >>tmp.vbs
echo WScript.Sleep 1000 >>tmp.vbs
echo sh.SendKeys "root{ENTER}" >>tmp.vbs
echo WScript.Sleep 1000 >>tmp.vbs
echo sh.SendKeys "admin{ENTER}" >>tmp.vbs
echo WScript.Sleep 1000 >>tmp.vbs
echo sh.SendKeys "shell{ENTER}" >>tmp.vbs
echo WScript.Sleep 1000 >>tmp.vbs
echo sh.SendKeys "cd /mnt/jffs2{ENTER}" >>tmp.vbs
echo WScript.Sleep 1000 >>tmp.vbs
echo sh.SendKeys "tftp -p -l hw_boardinfo.org -r hwboardinfo 192.168.100.2{ENTER}" >>tmp.vbs
echo WScript.Sleep 1000 >>tmp.vbs
echo Do >>tmp.vbs
echo     result = MsgBox("TFTP 传输完成！请尽快修改以下文件：" ^& vbCrLf ^& _ >>tmp.vbs
echo                      "  - hw_boardinfo" ^& vbCrLf ^& _ >>tmp.vbs
echo                      "  - customizepara.txt" ^& vbCrLf ^& vbCrLf ^& _ >>tmp.vbs
echo                      "确认后请将文件拖入 unicom.tar.gz 继续下一步。", vbOKCancel ^+ vbQuestion, "确认") >>tmp.vbs
echo     If result = vbOK Then >>tmp.vbs
echo         Exit Do >>tmp.vbs
echo     Else >>tmp.vbs
echo         MsgBox "请点击“确定”继续，或关闭窗口退出脚本。", vbExclamation, "提示" >>tmp.vbs
echo     End If >>tmp.vbs
echo Loop >>tmp.vbs
echo sh.SendKeys "tftp -g -l unicom.tar.gz -r unicom.tar.gz 192.168.100.2{ENTER}" >>tmp.vbs
echo WScript.Sleep 10000 >>tmp.vbs
echo sh.SendKeys "tar -xvf unicom.tar.gz{ENTER}" >>tmp.vbs
echo WScript.Sleep 3000 >>tmp.vbs
echo sh.SendKeys "cp -f /mnt/jffs2/hw_boardinfo /mnt/jffs2/hw_boardinfo.bak{ENTER}" >>tmp.vbs
echo WScript.Sleep 1000 >>tmp.vbs
echo sh.SendKeys "rm -rf unicom.tar.gz{ENTER}" >>tmp.vbs
echo WScript.Sleep 1000 >>tmp.vbs
echo sh.SendKeys "EquipMode.sh off{ENTER}" >>tmp.vbs
echo WScript.Sleep 3000 >>tmp.vbs
echo sh.SendKeys "reboot{ENTER}" >>tmp.vbs
echo WScript.Sleep 1000 >>tmp.vbs
start telnet
cscript //nologo tmp.vbs
del tmp.vbs
timeout /t 5 /nobreak >nul
taskkill /IM telnet.exe /F >nul 2>&1