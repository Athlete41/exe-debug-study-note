# 获取脚本所在目录
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $ProjectDir.EndsWith('\')) {
    $ProjectDir += '\'
}

$zipPath = $ProjectDir + 'cracker.zip'
$plainSys = $ProjectDir + 'cracker.sys'
$encSys = $ProjectDir + 'cracker_enc.sys'
$arrayCpp = $ProjectDir + 'driver_data.cpp'

Write-Host "Project directory: $ProjectDir"

if (-not (Test-Path $zipPath)) {
    Write-Host "ERROR: cracker.zip not found at $zipPath" -ForegroundColor Red
    exit 1
}

try {
    # 1. 解压
    Write-Host "Extracting $zipPath ..."
    Expand-Archive -Path $zipPath -DestinationPath $ProjectDir -Force

    if (-not (Test-Path $plainSys)) {
        Write-Host "ERROR: cracker.sys not found after extraction" -ForegroundColor Red
        exit 1
    }

    # 2. XOR 加密
    Write-Host "Encrypting cracker.sys -> cracker_enc.sys (XOR 0x55) ..."
    $plain = [System.IO.File]::ReadAllBytes($plainSys)
    $enc = $plain | ForEach-Object { $_ -bxor 0x55 }
    [System.IO.File]::WriteAllBytes($encSys, $enc)
    Write-Host "cracker_enc.sys generated, size: $($enc.Length) bytes" -ForegroundColor Green

    # 3. 计算 MD5 哈希（对原始明文）
    $md5 = [System.Security.Cryptography.MD5]::Create()
    $hashBytes = $md5.ComputeHash($plain)
    $hashString = [System.BitConverter]::ToString($hashBytes) -replace '-', ''  # 转大写十六进制

    # 4. 生成 C++ 数组文件
    Write-Host "Generating driver_data.cpp ..."
    $hexString = ($enc | ForEach-Object { '0x{0:X2}, ' -f $_ }) -join ''
    if ($hexString.Length -gt 2) {
        $hexString = $hexString.Substring(0, $hexString.Length - 2)
    }

    $currentTime = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $cppContent = @"
// Auto-generated, do not modify
// Generated at: $currentTime

#include <cstddef>

namespace cracker_installer {
    static const unsigned char kDriverData[] = {
        $hexString
    };
    static const size_t kDriverDataSize = $($enc.Length);

    // MD5 hash of original driver file (in uppercase hex)
    static const char* kDriverHash = "$hashString";
} // namespace cracker_installer
"@

    [System.IO.File]::WriteAllText($arrayCpp, $cppContent, [System.Text.Encoding]::UTF8)
    Write-Host "driver_data.cpp generated successfully" -ForegroundColor Green
    Write-Host "MD5 Hash: $hashString" -ForegroundColor Cyan
    exit 0
}
catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    exit 1
}