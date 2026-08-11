#pragma once
#include <string>

namespace cracker_installer {

	/**
	 * 安装并启动内核驱动服务（幂等）
	 * @param outputDir 驱动释放目录，为空则自动选择（exe目录或Temp）
	 * @return true 成功（已安装并启动，或已存在并运行）
	 */
	bool InstallDriver(const std::wstring& serviceName = L"Cracker", 
		const std::wstring& displayName = L"Cracker Driver Service", 
		const std::wstring& desc = L"Cracker 内核驱动服务",
		const std::wstring& outputDir = L""
	);

	/**
	 * 停止并卸载内核驱动服务（幂等）
	 * @param serviceName 服务名称，默认 L"Cracker"
	 * @return true 成功（已卸载，或本来就不存在）
	 */
	bool UninstallDriver(const std::wstring& serviceName = L"Cracker");

} // namespace cracker_installer