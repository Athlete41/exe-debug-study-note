@echo off
net session >nul 2>&1
if errorlevel 1 (
    powershell start -verb runas '%0' %*
    exit /b
)
cd /d "%~dp0"
python cracker_installer.py install --path "%~dp0cracker.sys" --desc "某服务"
pause