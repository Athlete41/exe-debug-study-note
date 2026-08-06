### 📓 Windows 内核态代码加载调用链

**前提**：本篇是《Windows用户态代码加载调用链》的姊妹篇，视角切换到**内核态（Ring 0）**。

**核心逻辑**：内核态代码（驱动程序 `.sys` 文件）进入内核，同样只有两条路——要么**系统启动时自动加载**，要么**管理员手动触发加载**。但无论哪条路，最终都要经过 **I/O 管理器** 的统一调度。

---

### 前置知识：驱动程序是什么？

内核态代码在 Windows 中通常以**驱动程序（Driver）** 的形式存在。驱动程序本质上是**运行在 Ring 0 的 PE 文件**（`.sys` 格式），它没有 `main` 或 `WinMain` 入口点，而是由 I/O 管理器在加载时调用其 **`DriverEntry`** 例程来完成初始化。

---

### 两类加载方式（再无其他）

#### 第一类：系统启动时自动加载（Boot/Start）

**触发时机**：Windows 内核启动早期，由 `ntoskrnl.exe` 根据注册表配置自动加载。

**典型场景**：
- **Boot Start**：引导阶段加载（如硬盘驱动、文件系统驱动）
- **System Start**：内核初始化阶段加载
- **Auto Start**：服务控制管理器（SCM）在系统启动后自动加载

**注册表位置**：`HKLM\SYSTEM\CurrentControlSet\Services\<服务名>`

**启动类型**：由注册表中的 `Start` 值决定（0=Boot，1=System，2=Auto）


#### 第二类：管理员手动触发加载（Demand）

**触发方式**：管理员通过以下方式主动加载驱动程序：
- **SC 命令**：`sc create` + `sc start`
- **服务 API**：`OpenSCManager()` → `CreateService()` → `StartService()`
- **直接调用**：`NtLoadDriver()` / `ZwLoadDriver()`

**核心前提**：调用进程必须拥有 **`SeLoadDriverPrivilege`** 特权。

---

### 完整调用链（从用户态到内核）

无论驱动是通过系统启动加载，还是手动触发加载，最终在内核层的调用路径是**高度统一**的：

```
用户态入口（services.exe / 第三方进程）
    ↓
NtLoadDriver() / ZwLoadDriver()（系统调用，进入内核）
    ↓
IopLoadDriver()（I/O 管理器加载函数）
    ↓
MmLoadSystemImage()（内存管理器：将 .sys 文件映射到内核空间）
    ↓
MiDriverLoadSucceeded()（加载成功回调）
    ↓
IoInitializeDriver()（初始化 DRIVER_OBJECT 结构）
    ↓
DriverEntry(DriverObject, NULL)（执行驱动入口点）
    ↓
驱动正式运行
```

**关键细节**：
- `NtLoadDriver` 阶段会先检查 `PsLoadedModuleList`（内核模块链表），确认驱动是否已加载
- `MmLoadSystemImage` 负责将 `.sys` 文件的 PE 映像映射到内核地址空间
- `IoInitializeDriver` 为驱动分配 `DRIVER_OBJECT` 结构，并填充默认的分发函数（`MajorFunction` 数组）
- 最后调用 `DriverEntry`，驱动正式生效

> 💡 **ReactOS 源码佐证**：上述流程在 ReactOS 的源码中有完整实现——`ntoskrnl/io/iomgr/loader.c` 中的 `IopLoadDriverImage` 调用 `LdrLoadDriver` 映射 PE 文件，`ntoskrnl/ldr/ldrpe.c` 负责 PE 映射与重定位。

---

### 🔍 如何监控内核态代码加载？

#### 1. ProcMon（有限支持）

ProcMon 可以捕获 **`Load Image`** 事件，其中既包括用户态 DLL，也包括内核态驱动。但需要注意的是：
- ProcMon 通过自身内核驱动（`ProcMon.sys`）在内核态拦截系统调用
- 驱动加载事件会出现在日志中，但**不如 Sysmon 详细**（无签名信息、无哈希）

#### 2. Sysmon（推荐）⭐

Sysmon 是监控驱动加载的**首选工具**：
- **事件 ID 6：驱动程序已加载**——专门记录系统上所有驱动加载事件
- 提供驱动文件的**签名信息**和**哈希值**（SHA1/SHA256/IMPHASH）
- 可检测驱动证书是否被吊销
- 驱动作为**引导启动驱动程序**安装，从系统启动早期就开始捕获活动

**配置示例**：`sysmon64 -i`（默认安装即可记录驱动加载）

#### 3. 内核回调（开发者/安全产品方案）

安全软件通常使用 **`PsSetLoadImageNotifyRoutine`** 设置模块加载回调：
- 回调的第二个参数判断加载类型：**PID 为 0 表示驱动加载**，PID 非零表示 DLL 加载
- 优点：更底层、更通用
- 缺点：回调触发时驱动入口点可能已经执行完毕

---

### ⚠️ 安全风险与对抗

内核态代码加载是 **Rootkit** 和**内核级木马**的核心技术手段：

| 攻击手法 | 说明 |
| :--- | :--- |
| **恶意驱动加载** | 攻击者通过社会工程或漏洞提权后，手动加载恶意 `.sys` 文件 |
| **BYOVD（Bring Your Own Vulnerable Driver）** | 利用已知漏洞的合法驱动提权或绕过安全机制 |
| **Bootkit** | 在引导阶段加载恶意驱动，比操作系统更早启动 |

**防御措施**：
- **ELAM（Early Launch Anti-Malware）**：微软提供的机制，允许安全软件注册一个在**其他第三方驱动之前**执行的内核驱动，在启动早期拦截恶意驱动
- **驱动签名强制**：64位 Windows 要求所有内核驱动必须有有效的数字签名
- **Sysmon 持续监控**：记录所有 `Event ID 6` 驱动加载事件，结合 SIEM 进行分析

---

### 🔍 最终判断法则（一张表搞定）

| 监控工具 | 看到什么 | 结论 |
| :--- | :--- | :--- |
| **ProcMon** | `Load Image` 事件，路径指向 `.sys` 文件 | 内核驱动被加载 |
| **Sysmon** | `Event ID 6`，包含驱动路径、签名、哈希 | **推荐**：驱动加载详情 |
| **内核回调** | `PsSetLoadImageNotifyRoutine` 回调，PID=0 | 驱动加载（安全产品方案） |

---

**总结**：内核态代码加载的调用链比用户态**更短、更直接**——无非是从 `NtLoadDriver` 进入内核，经过 I/O 管理器和内存管理器，最后调用 `DriverEntry`。监控手段上，**Sysmon 的 Event ID 6 是黄金标准**，而 ProcMon 的 `Load Image` 可以作为辅助参考。