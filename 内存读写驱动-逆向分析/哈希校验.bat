@echo off
setlocal enabledelayedexpansion

echo 正在计算 MD5 哈希值，请稍候...
echo.

for /R %%f in (*.dll *.sys *.exe) do (
    call :getmd5 "%%f"
)

echo.
echo 所有文件处理完毕！
pause
exit /b

:getmd5
for /f "skip=1 tokens=*" %%a in ('certutil -hashfile "%~1" MD5 2^>nul') do (
    echo %~1 %%a
    goto :eof
)
goto :eof