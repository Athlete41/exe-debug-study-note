#pragma once
#include <string>

namespace cracker_installer {

    /**
     * 安装并启动内核驱动服务
     * @param serviceName 服务名，若为空则随机生成（格式 Ckr_xxxxxx）
     * @param displayName 显示名，若为空则使用 serviceName
     * @param desc 服务描述，默认空
     * @param outputDir 驱动释放目录，为空则自动选择（exe目录或Temp）
     * @return true 成功
     */
    bool InstallDriver(const std::wstring& serviceName = L"",
        const std::wstring& displayName = L"",
        const std::wstring& desc = L"Cracker 内核驱动服务",
        const std::wstring& outputDir = L"");

    /**
     * 卸载驱动
     * @param serviceName 指定服务名则按名字卸载；若为空则按文件哈希（kDriverHash）匹配卸载所有匹配的服务
     * @return true 成功（服务不存在也算成功）
     */
    bool UninstallDriver(const std::wstring& serviceName = L"");

} // namespace cracker_installer