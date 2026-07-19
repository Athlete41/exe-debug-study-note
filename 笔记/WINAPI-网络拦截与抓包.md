# Windows 网络拦截与抓包相关 WinAPI 笔记

## ws2_32.dll

Winsock 2 的核心动态链接库，几乎所有 Windows 网络应用程序都会加载。通过 Hook 该 DLL 中的函数，可以在应用层拦截网络通信。

| 匹配字段 | 功能 |
|---------|------|
| `socket` | 创建套接字 |
| `connect` | 建立 TCP 连接 |
| `bind` | 绑定套接字到本地地址和端口 |
| `listen` | 开始监听连接 |
| `accept` | 接受传入连接 |
| `send` | 发送 TCP 数据 |
| `recv` | 接收 TCP 数据 |
| `sendto` | 发送 UDP 数据 |
| `recvfrom` | 接收 UDP 数据 |
| `WSASend` | Winsock 2 异步发送 |
| `WSARecv` | Winsock 2 异步接收 |
| `WSASendTo` | Winsock 2 异步 UDP 发送 |
| `WSARecvFrom` | Winsock 2 异步 UDP 接收 |
| `closesocket` | 关闭套接字 |
| `ioctlsocket` | 控制套接字 I/O 模式（如设置混杂模式） |
| `WSAEventSelect` | 事件通知 |
| `WSAStartup` | 初始化 Winsock 库 |


---

## wpcap.dll

WinPcap/Npcap 的高层 API 库，提供与 libpcap 兼容的跨平台抓包接口。

| 匹配字段 | 功能 |
|---------|------|
| `pcap_findalldevs` | 获取所有可用网络适配器列表 |
| `pcap_open_live` | 打开网络设备进行实时捕获 |
| `pcap_open` / `pcap_create` + `pcap_activate` | 创建并激活捕获句柄 |
| `pcap_setfilter` | 设置 BPF 过滤规则 |
| `pcap_compile` | 编译过滤表达式 |
| `pcap_loop` | 循环捕获数据包 |
| `pcap_next_ex` | 获取下一个数据包 |
| `pcap_sendpacket` | 发送原始数据包 |
| `pcap_dump_open` | 打开 pcap 文件用于保存 |
| `pcap_dump` | 将数据包写入 pcap 文件 |
| `pcap_close` | 关闭捕获设备 |
| `pcap_setnonblock` | 设置非阻塞模式 |
| `pcap_init` | 全局初始化（Npcap 新增） |
| `pcap_wsockinit` | Windows Sockets 初始化（Npcap） |

> **应用场景**：用户态抓包工具（如 Wireshark）的基础库。wpcap.dll 底层通过 Packet.dll 与内核驱动 npf.sys 通信。


---

## Packet.dll

WinPcap 的低层 API 库，提供与内核驱动 NPF 交互的接口。

| 匹配字段 | 功能 |
|---------|------|
| `PacketGetAdapterNames` | 获取适配器名称列表 |
| `PacketOpenAdapter` | 打开网络适配器 |
| `PacketCloseAdapter` | 关闭适配器 |
| `PacketAllocatePacket` | 分配数据包结构 |
| `PacketFreePacket` | 释放数据包结构 |
| `PacketReceivePacket` | 从驱动接收数据包 |
| `PacketSendPacket` | 通过驱动发送数据包 |
| `PacketGetVersion` | 获取 Packet.dll 版本 |
| `PacketSetFilter` | 设置过滤规则 |
| `PacketSetBuff` | 设置内核缓冲区大小 |
| `PacketGetNetType` | 获取网络类型 |
| `PacketGetMacAddress` | 获取 MAC 地址 |

> **应用场景**：直接与 NPF 驱动交互，提供比 wpcap.dll 更底层的控制能力。


---

## fwpuclnt.dll

Windows Filtering Platform (WFP) 的用户态 API 库。WFP 是微软官方推荐的网络过滤平台，用于取代 TDI 过滤、NDIS 过滤和 Winsock LSP。

| 匹配字段 | 功能 |
|---------|------|
| `FwpmEngineOpen` | 打开与过滤引擎的会话 |
| `FwpmEngineClose` | 关闭引擎会话 |
| `FwpmFilterAdd` | 添加过滤规则 |
| `FwpmFilterDeleteById` | 按 ID 删除过滤规则 |
| `FwpmCalloutAdd` | 注册标注（Callout）驱动 |
| `FwpmLayerGetById` | 获取分层信息 |
| `FwpmProviderAdd` | 添加服务提供者 |
| `FwpmSessionEnum` | 枚举当前会话 |
| `FwpmNetEventCreate` | 创建网络事件 |
| `FwpmFilterGetById` | 按 ID 获取过滤规则 |

> **应用场景**：实现防火墙、入侵检测、网络监控、家长控制等。支持 Windows Vista 及以上系统。WFP 可在网络栈多个层级拦截和修改数据。

---

## ndisapi（WinpkFilter）

基于 NDIS (Network Driver Interface Specification) 的包过滤库，通过用户态接口与 Windows Packet Filter 驱动交互。

| 匹配字段 | 功能 |
|---------|------|
| `NdisapiOpenAdapter` | 打开网络适配器 |
| `NdisapiCloseAdapter` | 关闭适配器 |
| `NdisapiSetFilter` | 设置包过滤规则 |
| `NdisapiReceivePacket` | 接收数据包 |
| `NdisapiSendPacket` | 发送数据包 |
| `NdisapiGetAdapterInfo` | 获取适配器信息 |
| `NdisapiGetPacket` | 获取数据包内容 |
| `NdisapiSetEvent` | 设置捕获事件 |

> **应用场景**：高性能包过滤，适用于防火墙、VPN、IDS/IPS 等。工作在 NDIS 层，可处理原始网络包。

---

## WinDivert（windivert.dll）

用户态包拦截库，可在 Windows 网络栈中拦截、修改、丢弃或重注入数据包。

| 匹配字段 | 功能 |
|---------|------|
| `WinDivertOpen` | 打开 WinDivert 句柄 |
| `WinDivertRecv` | 接收拦截的数据包 |
| `WinDivertSend` | 发送/重注入数据包 |
| `WinDivertClose` | 关闭句柄 |
| `WinDivertSetParam` | 设置参数 |
| `WinDivertGetParam` | 获取参数 |
| `WinDivertHelperCalcChecksums` | 计算校验和 |
| `WinDivertHelperParsePacket` | 解析数据包 |

> **应用场景**：轻量级用户态抓包与流量操控。支持 Windows 7/8/10。支持多种拦截层（网络层、流层、套接字层等）。



在 `mswsock.dll` 上对网络数据流下断点，通常聚焦于其导出的、用于**收发数据**的核心函数。下表整理了几个关键的断点目标：

| 函数 | 功能 |
| :--- | :--- |
| **`WSARecvEx`** | **接收数据**。这是 `mswsock.dll` 中少数几个直接导出的数据接收函数。它类似于标准的 `recv` 函数，但在处理数据报协议时能提供更详细的信息。 |
| **`AcceptEx`** | **接受连接并接收首批数据**。此函数在建立新连接的同时，能接收客户端发送的第一块数据。若想捕获连接建立瞬间的初始数据包，在此下断很有效。 |
| **`TransmitFile`** | **发送文件数据**。这是一个高性能的文件发送函数，用于直接通过套接字传输文件。如果目标程序通过此函数发送文件内容，在此下断即可截获。 |

### 💡 深入一点：更底层的断点选择

值得注意的是，`ws2_32.dll` 中的标准函数（如 `send`、`recv`）最终会调用到 `mswsock.dll`，而 `mswsock.dll` 内部最终又会调用内核级的 `NtDeviceIoControlFile` 函数来与驱动交互。

因此，如果你进行更底层的调试，也可以考虑在 **`NtDeviceIoControlFile`** 函数下断。这个断点能捕获到更底层的、几乎所有类型的网络收发指令（包括TCP和UDP）。

### ⚠️ 注意事项

*   **区分断点层级**：在对 `mswsock.dll` 下断前，需明确你的目标。大部分应用层程序直接调用 `ws2_32.dll` 的 `send`/`recv`，因此在这些更上层的函数下断通常更直接、干扰更少。
*   **理解调用关系**：`mswsock.dll` 是 `ws2_32.dll` 与内核驱动之间的桥梁。在此下断能捕获到经过Winsock处理后的数据，更接近底层。
*   **注意函数获取方式**：`mswsock.dll` 中的许多高级扩展函数（如 `ConnectEx`、`DisconnectEx`、`TransmitPackets` 等）**并不在导出表中**，无法直接下断。它们需要在运行时通过 `WSAIoctl` 函数动态获取指针后才能调用。
*   **留意反调试手段**：某些程序会采用反调试技术，使在API函数下断点失效。

---

## 总结

| 方案 | 工作层级 | 典型 DLL | 适用场景 |
|------|---------|---------|---------|
| Winsock Hook | 应用层 | ws2_32.dll | 拦截特定进程网络调用，获取明文数据 |
| WinPcap/Npcap | 链路层 | wpcap.dll / Packet.dll | 通用抓包，兼容 libpcap |
| WFP | 网络栈多层 | fwpuclnt.dll | 防火墙、IDS、官方推荐方案 |
| NDISAPI | NDIS 层 | ndisapi | 高性能底层包过滤 |
| WinDivert | 网络栈 | windivert.dll | 轻量级用户态流量操控 |

不同方案适用于不同场景，可根据需求选择：应用层调试选 Winsock Hook，通用抓包选 WinPcap/Npcap，系统级过滤选 WFP。