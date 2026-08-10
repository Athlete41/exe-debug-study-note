#pragma once

#ifndef NOMINMAX
#define NOMINMAX
#endif

#include <cstdint>
#include <string>
#include <vector>
#include <optional>
#include <string_view>

namespace cracker {

    // ---------- IOCTL 指令码 ----------
    constexpr std::uint32_t IOCTL_READ_WRITE_MEMORY_MDL = 0x238004;
    constexpr std::uint32_t IOCTL_READ_WRITE_MEMORY = 0x238000;
    constexpr std::uint32_t IOCTL_GET_MODULE_BASE = 0x238008;
    constexpr std::uint32_t IOCTL_GET_PID_BY_NAME = 0x23801C;
    constexpr std::uint32_t IOCTL_TERMINATE_PROCESS = 0x238024;

    constexpr std::uint64_t READ_FLAG = 0;
    constexpr std::uint64_t WRITE_FLAG = 1;

    // ---------- 主客户端类 ----------
    class CrackerClient {
    public:
        CrackerClient() = default;
        ~CrackerClient() { close(); }

        // 禁用拷贝，允许移动
        CrackerClient(const CrackerClient&) = delete;
        CrackerClient& operator=(const CrackerClient&) = delete;
        CrackerClient(CrackerClient&& other) noexcept;
        CrackerClient& operator=(CrackerClient&& other) noexcept;

        // 打开设备 \\.\Cracker，成功返回 true
        bool open();

        // 关闭设备句柄
        void close();

        // 检查句柄是否有效
        explicit operator bool() const noexcept;

        // ---------- 底层通信核心 ----------
        // 发送 IOCTL，返回驱动状态码 (arg0) 和 arg3 的附加结果。
        // 若 DeviceIoControl 本身失败，返回 std::nullopt。
        std::optional<std::pair<std::uint64_t, std::uint64_t>> sendIoctl(
            std::uint32_t code,
            std::uint64_t arg0 = 0,
            std::uint64_t arg1 = 0,
            std::uint64_t arg2 = 0,
            std::uint64_t arg3 = 0,
            std::uint64_t arg4 = 0
        );

        // ---------- 高级封装指令（仅实测过的） ----------

        // 内存读写（direction: 0=读, 1=写）
        // 返回 status（arg0），成功为 0
        std::uint64_t readWriteMemory(std::uint32_t pid, std::uintptr_t targetAddr,
            std::size_t size, std::uintptr_t localBuf,
            std::uint64_t direction);

        // 内存读写MDL（direction: 0=读, 1=写）
        // 返回 status（arg0），成功为 0
        std::uint64_t readWriteMemoryMDL(std::uint32_t pid, std::uintptr_t targetAddr,
            std::size_t size, std::uintptr_t localBuf,
            std::uint64_t direction);

        // 获取模块基址（返回基址，若失败返回 nullopt）
        std::optional<std::uintptr_t> getModuleBase(std::uint32_t pid,
            std::string_view moduleNameAnsi);

        // 按进程名获取 PID（返回 PID，若未找到或失败返回 nullopt）
        // 注意：此指令的 status（arg0）不可信，实现中已忽略
        std::optional<std::uint32_t> getPidByName(std::string_view processNameAnsi);

        // 终止进程（返回 status，成功为 0）
        std::uint64_t terminateProcess(std::uint32_t pid);

    private:
        void* m_handle = nullptr;   // 实际类型为 HANDLE，但避免包含 windows.h
    };

} // namespace cracker