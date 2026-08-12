#include "cracker_client.hpp"
#include "cracker_installer.hpp"
#include <iostream>
#include <iomanip>
#include <array>
#include <cstring>
#include <optional>
#include <thread>
#include <chrono>

// 辅助：读取 uint32_t
static std::optional<std::uint32_t> readUInt32(cracker::CrackerClient& client,
    std::uint32_t pid,
    std::uintptr_t address) {
    std::uint32_t value = 0;
    std::uint64_t status = client.readWriteMemory(pid, address, sizeof(value),
        reinterpret_cast<std::uintptr_t>(&value),
        cracker::READ_FLAG);
    if (status == 0) {
        return value;
    }
    return std::nullopt;
}

// 辅助：读取 3 个 float 向量（使用普通读）
static std::optional<std::array<float, 3>> readVec3(cracker::CrackerClient& client,
    std::uint32_t pid,
    std::uintptr_t address) {
    std::array<float, 3> vec{};
    std::uint64_t status = client.readWriteMemory(pid, address, sizeof(vec),
        reinterpret_cast<std::uintptr_t>(vec.data()),
        cracker::READ_FLAG);
    if (status == 0) {
        return vec;
    }
    return std::nullopt;
}

static int test() {
    cracker::CrackerClient client;

    if (!client.open()) {
        std::cerr << "[-] Failed to open \\\\.\\Cracker. Make sure driver is loaded." << std::endl;
        return 1;
    }
    std::cout << "[+] Device opened successfully." << std::endl;

    const char* process_name = "hl.exe";
    const char* module_name = "client.dll";
    const char* module2_name = "hw.dll";

    // 1. 获取 PID
    auto pidOpt = client.getPidByName(process_name);
    if (!pidOpt) {
        std::cerr << "[-] Could not find process: " << process_name << std::endl;
        return 1;
    }
    std::uint32_t pid = *pidOpt;
    std::cout << "[+] PID of " << process_name << ": " << pid << std::endl;

    // 2. 获取 client.dll 基址
    auto baseOpt = client.getModuleBase(pid, module_name);
    if (!baseOpt) {
        std::cerr << "[-] Could not get base address of " << module_name << std::endl;
        return 1;
    }
    std::uintptr_t clientBase = *baseOpt;
    std::cout << "[+] Base of " << module_name << ": 0x" << std::hex << clientBase << std::dec << std::endl;

    // 3. 读取玩家坐标（普通读）
    const std::uintptr_t coordOffset = 0xE0388;
    auto vecOpt = readVec3(client, pid, clientBase + coordOffset);
    if (vecOpt) {
        auto& v = *vecOpt;
        std::cout << "[+] Player coordinates (normal): ("
            << v[0] << ", " << v[1] << ", " << v[2] << ")" << std::endl;
    }
    else {
        std::cerr << "[-] Failed to read player coordinates." << std::endl;
    }

    // 4. 获取 hw.dll 基址
    auto base2Opt = client.getModuleBase(pid, module2_name);
    if (!base2Opt) {
        std::cerr << "[-] Could not get base address of " << module2_name << std::endl;
        return 1;
    }
    std::uintptr_t hwBase = *base2Opt;
    std::cout << "[+] Base of " << module2_name << ": 0x" << std::hex << hwBase << std::dec << std::endl;

    // 计算生命值地址
    const std::uintptr_t healthPtrOffset = 0x100CC60;
    auto healthPtrOpt = readUInt32(client, pid, hwBase + healthPtrOffset);
    if (!healthPtrOpt) {
        std::cerr << "[-] Failed to read health pointer." << std::endl;
        return 1;
    }
    std::uintptr_t healthAddr = static_cast<std::uintptr_t>(*healthPtrOpt) + 0x80 + 0x324 + 0x160;
    std::cout << "[+] Health address: 0x" << std::hex << healthAddr << std::dec << std::endl;

    // 读取当前生命值
    auto healthValOpt = readUInt32(client, pid, healthAddr);
    if (healthValOpt) {
        std::cout << "[+] Current health: " << *healthValOpt << std::endl;
    }
    else {
        std::cerr << "[-] Failed to read health." << std::endl;
    }

    // 写入生命值为 1000.0 (float)
    float newHealth = 1000.0f;
    std::uint64_t status = client.readWriteMemory(pid, healthAddr, sizeof(newHealth),
        reinterpret_cast<std::uintptr_t>(&newHealth),
        cracker::WRITE_FLAG);
    if (status == 0) {
        std::cout << "[+] Wrote health to 1000.0 (status=0)" << std::endl;
        // 验证
        auto verifyOpt = readUInt32(client, pid, healthAddr);
        if (verifyOpt) {
            std::cout << "[+] Verified health (as uint32): " << *verifyOpt << std::endl;
        }
    }
    else {
        std::cerr << "[-] Write health failed with status: 0x" << std::hex << status << std::dec << std::endl;
    }

    // 5. 测试 MDL 读取（使用封装好的 readWriteMemoryMDL）
    {
        std::array<float, 3> mdlVec{};
        std::uint64_t statusMdl = client.readWriteMemoryMDL(pid,
            clientBase + coordOffset,
            sizeof(mdlVec),
            reinterpret_cast<std::uintptr_t>(mdlVec.data()),
            cracker::READ_FLAG);
        if (statusMdl == 0) {
            std::cout << "[+] MDL read coordinates: ("
                << mdlVec[0] << ", " << mdlVec[1] << ", " << mdlVec[2] << ")" << std::endl;
        }
        else {
            std::cerr << "[-] MDL read failed with status: 0x" << std::hex << statusMdl << std::dec << std::endl;
        }
    }

    // 6. (可选) 终止进程，默认注释掉
    //std::uint64_t termStatus = client.terminateProcess(pid);
    //if (termStatus == 0) {
    //    std::cout << "[+] Process terminated." << std::endl;
    //}
    //else {
    //    std::cerr << "[-] Terminate failed with status: 0x" << std::hex << termStatus << std::dec << std::endl;
    //}

    client.close();
    return 0;
}


int main() {

    if (cracker_installer::UninstallDriver()) {
        std::cout << "[+] Device uninstall successfully." << std::endl;
    }
    else {
        std::cerr << "[-] Failed to uninstall driver." << std::endl;
        std::this_thread::sleep_for(std::chrono::milliseconds(5000));
        return 1;
    }

    if (cracker_installer::InstallDriver()) {
        std::cout << "[+] Device install successfully." << std::endl;
    }
    else {
        std::cerr << "[-] Failed to install driver." << std::endl;
        std::this_thread::sleep_for(std::chrono::milliseconds(5000));
        return 1;
    }


    const int status = test();

    if (cracker_installer::UninstallDriver()) {
        std::cout << "[+] Device uninstall successfully." << std::endl;
    }
    else 
    {
        std::cerr << "[-] Failed to uninstall driver." << std::endl;
    }

    std::cout << "[+] Done." << std::endl;
    std::this_thread::sleep_for(std::chrono::milliseconds(5000));
    return status;

}