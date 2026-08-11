#include "cracker_installer.hpp"
#include <windows.h>
#include <winsvc.h>
#include <vector>
#include <fstream>
#include <iostream>
#include "driver_data.cpp"

namespace {

    // 获取驱动释放路径：优先 exe 同目录，失败则回退到 Temp
    std::wstring GetDriverOutputPath(const std::wstring& outputDir) {
        if (!outputDir.empty()) {
            return outputDir + L"\\cracker_enc.sys";
        }

        wchar_t exePath[MAX_PATH];
        GetModuleFileNameW(NULL, exePath, MAX_PATH);
        std::wstring dir = exePath;
        dir = dir.substr(0, dir.find_last_of(L"\\"));
        std::wstring fullPath = dir + L"\\cracker_enc.sys";

        // 测试 exe 目录是否可写
        HANDLE test = CreateFileW(fullPath.c_str(), GENERIC_WRITE, 0, NULL,
            CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
        if (test != INVALID_HANDLE_VALUE) {
            CloseHandle(test);
            DeleteFileW(fullPath.c_str());
            return fullPath;
        }

        // 不可写则用系统临时目录
        wchar_t tempPath[MAX_PATH];
        GetTempPathW(MAX_PATH, tempPath);
        return std::wstring(tempPath) + L"cracker_enc.sys";
    }

    bool WriteDriverFromMemory(const std::wstring& outputPath) {
        const unsigned char* pEncData = cracker_installer::kDriverData;
        size_t size = cracker_installer::kDriverDataSize;
        if (!pEncData || size == 0) return false;

        // 复制一份到 vector 进行解密（原数组是只读的，不能直接修改）
        std::vector<unsigned char> decData(pEncData, pEncData + size);
        for (auto& b : decData) {
            b ^= 0x55;   // 解密，和加密时使用同一密钥
        }

        std::ofstream ofs(outputPath, std::ios::binary);
        if (!ofs) return false;
        ofs.write(reinterpret_cast<const char*>(decData.data()), decData.size());
        return ofs.good();
    }

    SC_HANDLE OpenSCManagerHelper() {
        return OpenSCManagerW(NULL, NULL, SC_MANAGER_ALL_ACCESS);
    }

    bool StartServiceIfStopped(SC_HANDLE hService) {
        SERVICE_STATUS status;
        if (!QueryServiceStatus(hService, &status)) return false;
        switch (status.dwCurrentState) {
        case SERVICE_RUNNING: return true;
        case SERVICE_STOPPED: return StartServiceW(hService, 0, NULL) != 0;
        default: return false;
        }
    }

    bool StopService(SC_HANDLE hService) {
        SERVICE_STATUS status;
        if (!QueryServiceStatus(hService, &status)) return false;
        if (status.dwCurrentState == SERVICE_STOPPED) return true;
        if (!ControlService(hService, SERVICE_CONTROL_STOP, &status)) return false;

        // 等待最多 30 秒
        for (int i = 0; i < 30; ++i) {
            Sleep(1000);
            if (!QueryServiceStatus(hService, &status)) return false;
            if (status.dwCurrentState == SERVICE_STOPPED) return true;
        }
        return false;
    }

} // anonymous namespace

// ---------- 导出函数（在 cracker_installer 命名空间内） ----------
namespace cracker_installer {

    bool InstallDriver(const std::wstring& serviceName,
        const std::wstring& displayName,
        const std::wstring& desc,
        const std::wstring& outputDir
    ) {
        // 1. 确定释放路径
        std::wstring driverPath = GetDriverOutputPath(outputDir);

        // 2. 从资源提取并解密驱动
        if (!WriteDriverFromMemory(driverPath)) {
            std::cerr << "Cannot write driver file!" << std::endl;
            return false;
        }

        SC_HANDLE hSCM = OpenSCManagerHelper();
        if (!hSCM) {
            std::cerr << "Cannot open SCM! Try Admin!" << std::endl;
            return false;
        }

        bool success = false;
        SC_HANDLE hService = OpenServiceW(hSCM, serviceName.c_str(), SERVICE_ALL_ACCESS);

        if (hService) {
            // 服务已存在 -> 尝试启动（幂等）

            std::cout << "The service has been found!" << std::endl;
            success = StartServiceIfStopped(hService);
            CloseServiceHandle(hService);

            if (!success) {
                std::cerr << "Start Service failed!" << std::endl;
            }
        }
        else {
            if (GetLastError() == ERROR_SERVICE_DOES_NOT_EXIST) {
                // 服务不存在 -> 创建
                hService = CreateServiceW(
                    hSCM,
                    serviceName.c_str(),
                    displayName.c_str(),
                    SERVICE_ALL_ACCESS,
                    SERVICE_KERNEL_DRIVER,
                    SERVICE_DEMAND_START,
                    SERVICE_ERROR_NORMAL,
                    driverPath.c_str(),
                    NULL, NULL, NULL, NULL, NULL
                );
                if (hService) {
                    // 设置描述
                    SERVICE_DESCRIPTIONW sd = { const_cast<LPWSTR>(desc.c_str()) };
                    ChangeServiceConfig2W(hService, SERVICE_CONFIG_DESCRIPTION, &sd);
                    success = StartServiceIfStopped(hService);
                    CloseServiceHandle(hService);

                    if (!success) {
                        std::cerr << "Start Service failed!" << std::endl;
                    }
                }
            }
        }

        CloseServiceHandle(hSCM);
        return success;
    }

    bool UninstallDriver(const std::wstring& serviceName) {
        if (serviceName.empty()) {
            std::cerr << "Service name is empty!" << std::endl;
            return false;
        }

        SC_HANDLE hSCM = OpenSCManagerHelper();
        if (!hSCM) {
            std::cerr << "Cannot open SCM! Try Admin!" << std::endl;
            return false;
        }

        bool success = false;
        SC_HANDLE hService = OpenServiceW(hSCM, serviceName.c_str(), SERVICE_ALL_ACCESS);

        if (!hService) {
            // 服务不存在 -> 视为已卸载（幂等）
            success = (GetLastError() == ERROR_SERVICE_DOES_NOT_EXIST);
        }
        else {
            if (StopService(hService)) {
                success = DeleteService(hService) != 0;
            }
            CloseServiceHandle(hService);
        }

        CloseServiceHandle(hSCM);
        return success;
    }

} // namespace cracker_installer