# iphlpapi.dll

IP Helper API，Windows 网络配置、状态监控与诊断的核心接口库。它不直接用于抓包或拦截流量，而是提供网络环境检查、连接枚举、状态查询和配置管理能力。

| 匹配字段 | 功能 |
|---------|------|
| `GetAdaptersAddresses` | 获取本机所有网络适配器的完整地址信息（IPv4/IPv6、MAC、标志状态），是 `ipconfig` 的底层实现 |
| `GetNetworkParams` | 获取主机名、域名及 DNS 服务器列表等全局网络参数 |
| `GetIpForwardTable` | 获取 IPv4 路由表，查看系统路由转发路径 |
| `GetIpNetTable` / `GetIpNetEntry` | 获取或查询 ARP 缓存表（IP 到 MAC 地址的映射），用于局域网设备发现 |
| `GetExtendedTcpTable` | 获取扩展 TCP 连接表，包含本地/远程地址、端口、连接状态及**关联进程 PID** |
| `GetExtendedUdpTable` | 获取扩展 UDP 监听表，包含本地地址、端口及**关联进程 PID**，用于检测可疑 UDP 服务 |
| `GetTcpTable` / `GetTcp6Table` | 获取 IPv4/IPv6 TCP 连接表（基础版，无 PID） |
| `GetUdpTable` / `GetUdp6Table` | 获取 IPv4/IPv6 UDP 监听表（基础版，无 PID） |
| `GetIfEntry` / `GetIfEntry2` | 获取指定网络接口的 MIB-II 统计信息（收发字节数、丢包数、错误数、带宽等） |
| `GetIfTable` | 获取所有网络接口的列表及状态信息 |
| `GetIpStatistics` / `GetIpStatisticsEx` | 获取 IP 层协议统计（数据报数、分片情况、路由失败次数等） |
| `IcmpCreateFile` | 创建 ICMP 句柄，用于发送 Ping 探测 |
| `IcmpSendEcho` / `IcmpSendEcho2` | 同步/异步发送 ICMP Echo 请求（经典 Ping 实现），可用于主机存活检测和延迟测量 |
| `IcmpCloseHandle` | 关闭 ICMP 句柄 |
| `NotifyIpInterfaceChange` | 注册回调，监听网络接口状态变化（启用/禁用、地址变更、MTU 变化等） |
| `NotifyAddrChange` | 监听 IP 地址变更事件（可用于感知网络切换） |
| `NotifyRouteChange` | 监听路由表变更事件 |
| `SetIpForwardEntry` | 添加或修改路由表条目（需管理员权限，可用于网络诊断时临时调整路由） |
| `ConvertInterfaceLuidToIndex` / `ConvertInterfaceIndexToLuid` | 网络接口标识符（LUID）与索引号之间的相互转换 |
| `GetBestInterface` / `GetBestRoute` | 获取到指定目标 IP 的最佳出口接口或最优路由条目 |
| `GetPerTcpConnectionEStats` / `GetPerUdpConnectionEStats` | 获取特定 TCP/UDP 连接的扩展性能统计（RTT、拥塞窗口、重传次数等），用于深度网络质量诊断 |


---

## ndfapi.dll

Network Diagnostics Framework，提供智能网络问题诊断和修复能力。

| 匹配字段 | 功能 |
|---------|------|
| `NdfCreateWebIncident` | 创建 Web 连接诊断事件（用于检测网站访问问题） |
| `NdfCreateNetConnectionIncident` | 创建网络连接诊断事件 |
| `NdfDiagnoseIncident` | 对诊断事件进行原因分析 |
| `NdfRepairIncident` | 尝试修复诊断发现的问题 |
| `NdfCloseIncident` | 关闭诊断事件句柄 |

---

## netshell.dll

网络外壳库，支撑 `netsh` 命令，提供配置查询与修改的底层接口。公开 API 较少，通常通过 `netsh` 命令行调用，开发者很少直接调用此 DLL。

| 匹配字段 | 功能 |
|---------|------|
| 无公开直接调用的用户态 API | （该 DLL 主要供 `netsh.exe` 和系统组件内部使用，一般编程不直接引用） |

---

## mpr.dll

Multiple Provider Router，用于管理网络资源（如共享文件夹、映射驱动器）。

| 匹配字段 | 功能 |
|---------|------|
| `WNetOpenEnum` | 开始枚举网络资源（如工作组、计算机、共享） |
| `WNetEnumResource` | 继续枚举网络资源 |
| `WNetCloseEnum` | 结束枚举 |
| `WNetGetConnection` | 获取本地驱动器对应的网络远程路径 |
| `WNetGetUser` | 获取当前用户用于网络连接的用户名 |

---

## wininet.dll

Windows Internet 库，提供 HTTP/FTP 等协议功能，也包含简单的网络连接状态检查。

| 匹配字段 | 功能 |
|---------|------|
| `InternetGetConnectedState` | 快速检查本地系统是否具有网络连接（返回 BOOL） |
| `InternetCheckConnection` | 检查能否建立到指定服务器的连接（更精确） |

---

## WS2_32.dll（网络检查相关部分）

除了收发数据，Winsock 也提供网络信息查询功能。

| 匹配字段 | 功能 |
|---------|------|
| `getaddrinfo` | DNS 解析，将域名转换为 IP 地址 |
| `getnameinfo` | 将 IP 地址反向解析为主机名 |
| `gethostbyname` | （已废弃）同 getaddrinfo |
| `gethostbyaddr` | （已废弃）同 getnameinfo |
| `getsockopt` | 查询套接字选项（如 SO_ERROR、SO_KEEPALIVE 等） |
| `setsockopt` | 设置套接字选项 |
| `getpeername` | 获取连接的远程端地址 |
| `getsockname` | 获取本端绑定的地址 |

---

## NSI.dll

Network Service Interface，底层网络状态接口。`iphlpapi.dll` 等上层 API 依赖它，但用户态应用程序通常不直接调用其公开函数（多数函数未文档化）。

| 匹配字段 | 功能 |
|---------|------|
| 无用户态公开 API | （该 DLL 为系统内部组件，不提供可供应用程序直接调用的导出函数） |

---

## dhcpcsvc.dll

DHCP Client Service，提供与 DHCP 服务器交互的 API，可查询租约信息。

| 匹配字段 | 功能 |
|---------|------|
| `DhcpRequestParams` | 向 DHCP 服务器请求特定配置参数 |
| `DhcpGetOptionInfo` | 获取 DHCP 选项信息 |
| `DhcpNotifyConfigChange` | 通知 DHCP 配置变更 |
| `DhcpAcquireLease` | 获取 IP 地址租约（内部调用） |

---

## nlaapi.dll

Network Location Awareness，用于识别当前网络类型（域、专用、公用）。

| 匹配字段 | 功能 |
|---------|------|
| `NlaGetNetworkConnectivityHint` | 获取当前网络连接性和类型（如 Internet、本地网络） |
| `NlaSetNetworkConnectivityHint` | 设置网络连接性提示（供内部使用） |
| `NlaGetGuid` | 获取网络 GUID 标识符 |

---

# 补充：.NET 托管封装（非 DLL）

## System.Net.NetworkInformation（命名空间）

虽然不是 DLL，但它是 .NET 平台上对 `iphlpapi.dll` 等原生 API 的托管封装，使用安全便捷。

| 匹配字段 | 功能 |
|---------|------|
| `Ping.Send` | 发送 ICMP Echo（Ping） |
| `NetworkInterface.GetAllNetworkInterfaces` | 获取所有网络接口信息 |
| `IPGlobalProperties.GetActiveTcpConnections` | 获取活动 TCP 连接（含 PID） |
| `IPGlobalProperties.GetActiveUdpListeners` | 获取活动 UDP 监听器 |
| `IPGlobalProperties.GetIPGlobalProperties` | 获取主机名、域名等信息 |

---

# 总结

| 分类 | DLL / 库 | 主要用途 |
|------|----------|----------|
| **拦截/抓包** | ws2_32.dll | 应用层 Hook 截取明文数据 |
| | wpcap.dll / Packet.dll | 用户态抓包（Wireshark 底层） |
| | fwpuclnt.dll | 系统级网络过滤（WFP） |
| | windivert.dll | 用户态包操控 |
| **检查/诊断** | iphlpapi.dll | 核心网络查询（连接表、路由、ARP、Ping） |
| | ndfapi.dll | 智能诊断与修复 |
| | wininet.dll | 快速连接状态检查 |
| | mpr.dll | 网络资源（共享文件夹）枚举 |
| | WS2_32.dll | DNS 解析、套接字选项查询 |
| | dhcpcsvc.dll | DHCP 租约信息 |
| | nlaapi.dll | 网络类型识别 |
| | netshell.dll / NSI.dll | 内部组件，通常不直接使用 |
| **托管封装** | System.Net.NetworkInformation | .NET 平台便捷调用 |

以上为完整笔记，所有 DLL 均已严格按格式要求列出。如有遗漏或需要补充，可继续告知。