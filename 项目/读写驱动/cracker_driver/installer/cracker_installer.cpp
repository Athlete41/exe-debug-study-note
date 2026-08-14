#include "cracker_installer.hpp"
#include <windows.h>
#include <winsvc.h>
#include <winreg.h>
#include <vector>
#include <fstream>
#include <iostream>
#include <random>
#include <iomanip>
#include <sstream>
#include "driver_data.cpp"  // 包含 kDriverData, kDriverDataSize, kDriverHash

#pragma comment(lib, "advapi32.lib")

namespace {

    // ---------- 辅助函数 ----------

    // 生成随机服务名（格式：Ckr_xxxxxx，6位十六进制）
    std::wstring GenerateRandomServiceName() {
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<> dis(0, 15);
        std::wstringstream ss;
        ss << L"Ckr_";
        for (int i = 0; i < 6; ++i) {
            ss << std::hex << dis(gen);
        }
        return ss.str();
    }

    // 获取驱动释放路径：优先 exe 同目录，失败则回退到 Temp
    std::wstring GetDriverOutputPath(const std::wstring& outputDir) {
        if (!outputDir.empty()) {
            return outputDir + L"\\cracker.sys";
        }

        wchar_t exePath[MAX_PATH];
        GetModuleFileNameW(NULL, exePath, MAX_PATH);
        std::wstring dir = exePath;
        dir = dir.substr(0, dir.find_last_of(L"\\"));
        std::wstring fullPath = dir + L"\\cracker.sys";

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
        return std::wstring(tempPath) + L"cracker.sys";
    }

    // 从内存解密并写入驱动文件
    bool WriteDriverFromMemory(const std::wstring& outputPath) {
        const unsigned char* pEncData = cracker_installer::kDriverData;
        size_t size = cracker_installer::kDriverDataSize;
        if (!pEncData || size == 0) return false;

        std::vector<unsigned char> decData(pEncData, pEncData + size);
        for (auto& b : decData) {
            b ^= 0x55;   // 解密，和加密时使用同一密钥
        }

        std::ofstream ofs(outputPath, std::ios::binary);
        if (!ofs) return false;
        ofs.write(reinterpret_cast<const char*>(decData.data()), decData.size());
        return ofs.good();
    }

    // 打开服务管理器
    SC_HANDLE OpenSCManagerHelper() {
        return OpenSCManagerW(NULL, NULL, SC_MANAGER_ALL_ACCESS);
    }

    // 启动服务（如果停止）
    bool StartServiceIfStopped(SC_HANDLE hService) {
        SERVICE_STATUS status;
        if (!QueryServiceStatus(hService, &status)) return false;
        switch (status.dwCurrentState) {
        case SERVICE_RUNNING: return true;
        case SERVICE_STOPPED: return StartServiceW(hService, 0, NULL) != 0;
        default: return false;
        }
    }

    // 停止服务（等待30秒）
    bool StopService(SC_HANDLE hService) {
        SERVICE_STATUS status;
        if (!QueryServiceStatus(hService, &status)) return false;
        if (status.dwCurrentState == SERVICE_STOPPED) return true;
        if (!ControlService(hService, SERVICE_CONTROL_STOP, &status)) return false;

        for (int i = 0; i < 30; ++i) {
            Sleep(1000);
            if (!QueryServiceStatus(hService, &status)) return false;
            if (status.dwCurrentState == SERVICE_STOPPED) return true;
        }
        return false;
    }

    // ---------- 注册表操作（哈希写入与读取） ----------

    // 写入 FileHash 键值
    bool WriteFileHashToRegistry(const std::wstring& serviceName, const std::string& hash) {
        std::wstring regPath = L"SYSTEM\\CurrentControlSet\\Services\\" + serviceName;
        HKEY hKey;
        if (RegOpenKeyExW(HKEY_LOCAL_MACHINE, regPath.c_str(), 0, KEY_SET_VALUE, &hKey) != ERROR_SUCCESS)
            return false;
        // 将 std::string 转为 std::wstring 存储为 REG_SZ
        std::wstring wHash(hash.begin(), hash.end());
        LONG ret = RegSetValueExW(hKey, L"FileHash", 0, REG_SZ,
            (const BYTE*)wHash.c_str(),
            (DWORD)((wHash.size() + 1) * sizeof(wchar_t)));
        RegCloseKey(hKey);
        return ret == ERROR_SUCCESS;
    }

    // 读取指定服务的 FileHash（返回 std::string）
    std::string ReadFileHashFromRegistry(const std::wstring& serviceName) {
        std::wstring regPath = L"SYSTEM\\CurrentControlSet\\Services\\" + serviceName;
        HKEY hKey;
        if (RegOpenKeyExW(HKEY_LOCAL_MACHINE, regPath.c_str(), 0, KEY_QUERY_VALUE, &hKey) != ERROR_SUCCESS)
            return "";
        wchar_t hashW[33] = { 0 };
        DWORD size = sizeof(hashW);
        DWORD type = 0;
        if (RegQueryValueExW(hKey, L"FileHash", NULL, &type, (LPBYTE)hashW, &size) != ERROR_SUCCESS || type != REG_SZ) {
            RegCloseKey(hKey);
            return "";
        }
        RegCloseKey(hKey);
        // 转换为 std::string
        std::wstring wHash(hashW);
        return std::string(wHash.begin(), wHash.end());
    }

    // 遍历所有服务，返回 FileHash 等于指定哈希的服务名列表
    std::vector<std::wstring> FindServicesByHash(const std::string& targetHash) {
        std::vector<std::wstring> result;
        HKEY hServices;
        if (RegOpenKeyExW(HKEY_LOCAL_MACHINE, L"SYSTEM\\CurrentControlSet\\Services",
            0, KEY_READ, &hServices) != ERROR_SUCCESS)
            return result;

        DWORD index = 0;
        wchar_t subKeyName[256];
        DWORD nameSize = 256;
        while (RegEnumKeyExW(hServices, index, subKeyName, &nameSize, NULL, NULL, NULL, NULL) == ERROR_SUCCESS) {
            std::wstring serviceName(subKeyName);
            std::string hash = ReadFileHashFromRegistry(serviceName);
            if (hash == targetHash) {
                result.push_back(serviceName);
            }
            nameSize = 256;
            index++;
        }
        RegCloseKey(hServices);
        return result;
    }

    // 删除单个服务（停止+删除）
    bool DeleteServiceByName(const std::wstring& serviceName) {
        SC_HANDLE hSCM = OpenSCManagerHelper();
        if (!hSCM) return false;

        bool success = false;
        SC_HANDLE hService = OpenServiceW(hSCM, serviceName.c_str(), SERVICE_ALL_ACCESS);
        if (hService) {
            if (StopService(hService)) {
                success = DeleteService(hService) != 0;
            }
            CloseServiceHandle(hService);
        }
        else {
            // 服务不存在视为成功（幂等）
            success = (GetLastError() == ERROR_SERVICE_DOES_NOT_EXIST);
        }
        CloseServiceHandle(hSCM);
        return success;
    }

} // anonymous namespace

// ---------- 导出函数 ----------
namespace cracker_installer {

    bool InstallDriver(const std::wstring& serviceName,
        const std::wstring& displayName,
        const std::wstring& desc,
        const std::wstring& outputDir) {
        // 1. 确定释放路径
        std::wstring driverPath = GetDriverOutputPath(outputDir);

        // 2. 从内存提取并解密驱动
        if (!WriteDriverFromMemory(driverPath)) {
            std::cerr << "Cannot write driver file!" << std::endl;
            return false;
        }

        // 3. 确定服务名和显示名
        std::wstring finalServiceName = serviceName;
        if (finalServiceName.empty()) {
            finalServiceName = GenerateRandomServiceName();
        }
        std::wstring finalDisplayName = displayName;
        if (finalDisplayName.empty()) {
            finalDisplayName = finalServiceName;
        }

        // 4. 打开SCM
        SC_HANDLE hSCM = OpenSCManagerHelper();
        if (!hSCM) {
            std::cerr << "Cannot open SCM! Try Admin!" << std::endl;
            return false;
        }

        bool success = false;
        SC_HANDLE hService = OpenServiceW(hSCM, finalServiceName.c_str(), SERVICE_ALL_ACCESS);

        if (hService) {
            // 服务已存在 -> 尝试启动（幂等）
            std::cout << "Service already exists, attempting to start." << std::endl;
            success = StartServiceIfStopped(hService);
            CloseServiceHandle(hService);
            if (!success) {
                std::cerr << "Start Service failed!" << std::endl;
            }
            // 注意：如果服务已存在，我们不再更新哈希（保持原有）
        }
        else {
            if (GetLastError() == ERROR_SERVICE_DOES_NOT_EXIST) {
                // 服务不存在 -> 创建
                hService = CreateServiceW(
                    hSCM,
                    finalServiceName.c_str(),
                    finalDisplayName.c_str(),
                    SERVICE_ALL_ACCESS,
                    SERVICE_KERNEL_DRIVER,
                    SERVICE_DEMAND_START,
                    SERVICE_ERROR_NORMAL,
                    driverPath.c_str(),
                    NULL, NULL, NULL, NULL, NULL
                );
                if (hService) {
                    // 设置描述
                    if (!desc.empty()) {
                        SERVICE_DESCRIPTIONW sd = { const_cast<LPWSTR>(desc.c_str()) };
                        ChangeServiceConfig2W(hService, SERVICE_CONFIG_DESCRIPTION, &sd);
                    }
                    // 写入 FileHash
                    if (!WriteFileHashToRegistry(finalServiceName, kDriverHash)) {
                        std::cerr << "Warning: Failed to write FileHash to registry." << std::endl;
                    }
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
        // 如果指定了服务名，按名字卸载
        if (!serviceName.empty()) {
            return DeleteServiceByName(serviceName);
        }

        // 否则按哈希卸载
        std::string targetHash = kDriverHash;  // 使用编译时嵌入的哈希
        std::vector<std::wstring> services = FindServicesByHash(targetHash);
        if (services.empty()) {
            std::cout << "No service found matching the driver hash." << std::endl;
            return true;  // 幂等：没有匹配也视为成功
        }

        bool allSuccess = true;
        for (auto& name : services) {
            if (!DeleteServiceByName(name)) {
                allSuccess = false;
                std::wcerr << L"Failed to delete service: " << std::wstring(name.begin(), name.end()) << std::endl;
            }
        }
        return allSuccess;
    }

} // namespace cracker_installer