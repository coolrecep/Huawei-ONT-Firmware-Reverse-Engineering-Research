@echo off
title 启用 Windows 功能 & 添加辅助IP
setlocal enabledelayedexpansion


echo ========================================
echo   正在启用 Telnet 客户端...
echo ========================================
dism /online /Enable-Feature /FeatureName:TelnetClient /All /NoRestart
if !errorlevel! equ 0 (
    echo [√] Telnet 客户端启用成功
) else (
    echo [×] Telnet 客户端启用失败，请确认以管理员身份运行
)

echo.
echo ========================================
echo   正在启用 TFTP 客户端...
echo ========================================
dism /online /Enable-Feature /FeatureName:TFTP /All /NoRestart
if !errorlevel! equ 0 (
    echo [√] TFTP 客户端启用成功
) else (
    echo [×] TFTP 客户端启用失败，请确认以管理员身份运行
)

echo.
echo ========================================
echo   功能启用部分完成，可能需要重启生效
echo ========================================
echo.


echo ========================================
echo   正在检测已连接的网络适配器...
echo ========================================

set count=0
for /f "tokens=2 delims=:" %%i in ('netsh interface ip show interfaces ^| find "Connected"') do (
    set /a count+=1
    set "adapter!count!=%%i"
    echo !count!. %%i
)

if %count%==0 (
    echo [×] 未找到任何已连接的适配器，请检查网络连接后重试
    pause
    exit /b
)

echo.
set /p choice=请选择要添加辅助IP的适配器编号（1-%count%）: 
set "adapter=!adapter%choice%!"
for /f "tokens=* delims= " %%a in ("!adapter!") do set adapter=%%a

echo.
echo ========================================
echo   正在为适配器 [%adapter%] 添加辅助IP...
echo   IP: 192.168.100.2
echo   掩码: 255.255.255.0
echo ========================================
netsh interface ip add address "%adapter%" 192.168.100.2 255.255.255.0

if !errorlevel! equ 0 (
    echo [√] 辅助IP添加成功
) else (
    echo [×] 添加失败
    echo     可能原因：IP已存在、适配器名称错误、或权限不足
)

echo.
echo 全部操作完成。
echo 3秒后自动关闭窗口...
timeout /t 3 /nobreak >nul