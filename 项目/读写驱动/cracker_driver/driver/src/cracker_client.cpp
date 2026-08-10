#include "cracker_client.hpp"

#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <Windows.h>
#include <algorithm>
#include <cstring>
#include <array>

namespace cracker {

    // ---------- 内部辅助结构体（对齐与驱动一致）----------
#pragma pack(push, 8)
    struct IoctlParams {
        std::uint64_t arg0; // +0x00
        std::uint64_t arg1; // +0x08
        std::uint64_t arg2; // +0x10
        std::uint64_t arg3; // +0x18
        std::uint64_t arg4; // +0x20
    };
#pragma pack(pop)

    // ---------- 移动语义 ----------
    CrackerClient::CrackerClient(CrackerClient&& other) noexcept
        : m_handle(other.m_handle) {
        other.m_handle = nullptr;
    }

    CrackerClient& CrackerClient::operator=(CrackerClient&& other) noexcept {
        if (this != &other) {
            close();
            m_handle = other.m_handle;
            other.m_handle = nullptr;
        }
        return *this;
    }

    // ---------- 打开/关闭 ----------
    bool CrackerClient::open() {
        if (m_handle != nullptr && m_handle != INVALID_HANDLE_VALUE) {
            return true;
        }

        m_handle = CreateFileW(
            L"\\\\.\\Cracker",
            GENERIC_READ | GENERIC_WRITE,
            0,
            nullptr,
            OPEN_EXISTING,
            FILE_ATTRIBUTE_NORMAL,
            nullptr
        );

        return m_handle != nullptr && m_handle != INVALID_HANDLE_VALUE;
    }

    void CrackerClient::close() {
        if (m_handle != nullptr && m_handle != INVALID_HANDLE_VALUE) {
            CloseHandle(static_cast<HANDLE>(m_handle));
            m_handle = nullptr;
        }
    }

    CrackerClient::operator bool() const noexcept {
        return m_handle != nullptr && m_handle != INVALID_HANDLE_VALUE;
    }

    // ---------- 底层 IOCTL 核心 ----------
    std::optional<std::pair<std::uint64_t, std::uint64_t>>
        CrackerClient::sendIoctl(
            std::uint32_t code,
            std::uint64_t arg0,
            std::uint64_t arg1,
            std::uint64_t arg2,
            std::uint64_t arg3,
            std::uint64_t arg4
        ) {
        if (m_handle == nullptr || m_handle == INVALID_HANDLE_VALUE) {
            return std::nullopt;
        }

        IoctlParams params{ arg0, arg1, arg2, arg3, arg4 };
        DWORD bytesReturned = 0;

        const BOOL success = DeviceIoControl(
            static_cast<HANDLE>(m_handle),
            code,
            &params,
            sizeof(params),
            &params,
            sizeof(params),
            &bytesReturned,
            nullptr
        );

        if (!success) {
            return std::nullopt;
        }

        return std::make_pair(params.arg0, params.arg3);
    }

    // ---------- 高级封装实现 ----------
    std::uint64_t CrackerClient::readWriteMemory(
        std::uint32_t pid,
        std::uintptr_t targetAddr,
        std::size_t size,
        std::uintptr_t localBuf,
        std::uint64_t direction
    ) {
        auto result = sendIoctl(IOCTL_READ_WRITE_MEMORY,
            pid,
            targetAddr,
            size,
            localBuf,
            direction);
        return result ? result->first : ~0ULL;
    }


    std::uint64_t CrackerClient::readWriteMemoryMDL(
        std::uint32_t pid, 
        std::uintptr_t targetAddr,
        std::size_t size, 
        std::uintptr_t localBuf,
        std::uint64_t direction
    ) {
        auto result = sendIoctl(IOCTL_READ_WRITE_MEMORY_MDL,
            pid, 
            targetAddr, 
            size, 
            localBuf, 
            direction);
        return result ? result->first : ~0ULL;
    }



    std::optional<std::uintptr_t> CrackerClient::getModuleBase(
        std::uint32_t pid,
        std::string_view moduleNameAnsi
    ) {
        std::vector<char> nameBuf(moduleNameAnsi.size() + 1);
        std::copy(moduleNameAnsi.begin(), moduleNameAnsi.end(), nameBuf.begin());
        nameBuf.back() = '\0';

        std::uint64_t resultAddr = 0;
        auto statusPair = sendIoctl(
            IOCTL_GET_MODULE_BASE,
            pid,
            reinterpret_cast<std::uint64_t>(nameBuf.data()),
            0,
            reinterpret_cast<std::uint64_t>(&resultAddr),
            0
        );

        // 实测 status 可信，且 resultAddr 非零才有效
        if (statusPair && statusPair->first == 0 && resultAddr != 0) {
            return static_cast<std::uintptr_t>(resultAddr);
        }
        return std::nullopt;
    }

    std::optional<std::uint32_t> CrackerClient::getPidByName(
        std::string_view processNameAnsi
    ) {
        std::vector<char> nameBuf(processNameAnsi.size() + 1);
        std::copy(processNameAnsi.begin(), processNameAnsi.end(), nameBuf.begin());
        nameBuf.back() = '\0';

        std::uint64_t pidResult = 0;
        auto statusPair = sendIoctl(
            IOCTL_GET_PID_BY_NAME,
            reinterpret_cast<std::uint64_t>(nameBuf.data()),
            0,
            0,
            reinterpret_cast<std::uint64_t>(&pidResult),
            0
        );

        // 实测：status（arg0）不可信，只检查 pidResult 是否非零
        if (statusPair && pidResult != 0) {
            return static_cast<std::uint32_t>(pidResult);
        }
        return std::nullopt;
    }

    std::uint64_t CrackerClient::terminateProcess(std::uint32_t pid) {
        auto result = sendIoctl(IOCTL_TERMINATE_PROCESS, pid, 0, 0, 0, 0);
        return result ? result->first : ~0ULL;
    }

} // namespace cracker