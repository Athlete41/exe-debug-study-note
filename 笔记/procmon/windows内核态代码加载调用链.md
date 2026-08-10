### 📓 Windows 内核态代码加载调用链

**前提**：本篇以用户态程序的视角，梳理用户态程序如何加载内核态驱动（.sys）。用户态程序无权限直接操作内核，必须通过SCM或特殊系统调用作为“中介”进入Ring 0。


### 前置知识：DSE（驱动签名强制）

64位Windows（Vista+）强制要求内核驱动有有效的WHQL数字签名才能加载。

- **测试模式**：`bcdedit -set TESTSIGNING ON` 可加载测试签名驱动（桌面右下角水印），但开启Secure Boot时无效
- **禁用DSE**：重启按F7/选择“禁用驱动签名强制”进入调试模式
- **内核补丁保护（KPP/PatchGuard）**：64位Windows的内核保护机制，禁止修改内核关键结构（如SSDT、IDT、内核代码段），会阻止某些DSE绕过方式


### 四类加载方式

### 第一类：标准SCM加载

**难度**：⭐（需管理员权限）

用户态程序通过SCM将驱动注册为“服务”，由SCM调用系统服务进入内核。

**调用链**：
`OpenSCManager` → `CreateService`（创建服务项，写入注册表 `HKLM\SYSTEM\CurrentControlSet\Services\`）→ `StartService` → **`NtLoadDriver`**（SCM内部调用的系统调用）→ `IopLoadDriver`（I/O管理器）→ `ObCreateObject`（创建 `DRIVER_OBJECT`）→ `DriverEntry`（驱动入口点）

**签名要求**：WHQL签名

**隐蔽性**：低

**ProcMon特征**：
- **注册表操作**：`services.exe` 写入 `Services` 注册表键（创建服务项）
- `LoadImage` 事件（`System` 进程记录）
- `.sys` 文件读取操作


### 第二类：直接调用 NtLoadDriver（半隐蔽）

**难度**：⭐⭐（需管理员权限，驱动信息需预先写入注册表）

用户态程序直接调用 `NtLoadDriver`，**绕过 `StartService` 和 `services.exe` 层的日志记录**。但驱动信息**仍需预先写入注册表 `Services` 键**（可通过 `CreateService` 或直接写注册表完成）。

**调用链**：
（预配注册表 `Services` 键）→ **`NtLoadDriver`**（用户态直接调用）→ `IopLoadDriver` → `DriverEntry`

**签名要求**：WHQL签名

**隐蔽性**：中

**ProcMon特征**：
- **注册表操作**：**用户进程自身** 写入 `Services` 注册表键（无services.exe参与）
- `LoadImage` 事件（`System` 进程记录）
- `.sys` 文件读取操作

**与第一类的区别**：
| | 第一类（标准SCM） | 第二类（直接NtLoadDriver） |
|:---|:---|:---|
| 写注册表主体 | `services.exe` | 用户进程自身 |
| `LoadImage` | 有 | 有 |
| `services.exe` 参与 | 是 | 否 |


### 第三类：ZwSetSystemInformation（高度隐蔽，但标准调用仍受签名限制）

**难度**：⭐⭐⭐⭐（需了解未文档化API，稳定性风险高）

通过 `ZwSetSystemInformation` 系统调用，使用 `SystemLoadAndCallImage` 功能类，在内核中加载模块。**它与第一、二类的本质区别在于完全不触碰注册表 `Services` 键，且不创建标准 `DRIVER_OBJECT`**。

**关键机制修正**：
- **完全不写注册表**：无 `Services` 键操作，系统不创建标准 `DRIVER_OBJECT`
- **磁盘读取与签名校验依然存在**：标准调用 `SystemLoadAndCallImage` 时，内核的 `MmLoadSystemImage` 会**从磁盘读取 `.sys` 文件**，并且**必须经过 `SeValidateImageHeader` 进行WHQL签名校验**。它跳过的只是 `IopLoadDriver` 中的注册表解析和标准驱动对象创建流程。
- **真正的“无文件内存加载”通常不在此列**：若想完全不读磁盘且绕过DSE加载未签名代码，通常需要先通过第四类（BYOVD）获取任意内核内存写入原语，再手动将Shellcode/驱动映射到内核内存——这已超出标准API调用的范畴。

**调用链**：
`ZwSetSystemInformation(SystemLoadAndCallImage, ...)` → `MmLoadSystemImage`（读盘+签名校验）→ 内核加载模块 → 执行入口点

**签名要求**：标准调用**仍然要求WHQL签名**。若需绕过，必须配合其他漏洞（如已获取任意内核内存写入能力）手动映射。

**隐蔽性**：极高

**ProcMon特征（修正）**：
- **无注册表操作**（完全不碰 `Services` 键，这是最关键的区分特征）
- **有磁盘文件读取**（标准调用需要读 `.sys` 文件，ProcMon可捕捉到 `CreateFile`/`ReadFile` 操作）
- **`LoadImage` 回调在内核触发**：`PsSetLoadImageNotifyRoutine` 会记录该事件，但**ProcMon默认不显示内核态的图像加载**（它主要监控用户态进程），需依赖 **ETW (Microsoft-Windows-Kernel-Image)** 或内核调试器方可捕获


### 第四类：BYOVD（自带漏洞驱动，借刀杀人）

**难度**：⭐⭐⭐⭐（需掌握漏洞驱动资源，技术门槛高）

**BYOVD**全称**Bring Your Own Vulnerable Driver**。攻击者利用**有WHQL签名但存在漏洞的合法驱动程序**作为“跳板”获取内核权限。

**BYOVD不是注入技术，而是获取内核权限的手段。获取内核权限后，攻击者可以做任何内核级操作。**

**为什么难以防御**：
- 驱动有**有效的WHQL数字签名**，通过DSE检查
- 系统天然信任有签名的驱动，传统安全产品不会对加载行为告警
- 利用阶段通过合法IOCTL调用，行为混杂在正常系统中

**攻击流程**：
1. **搜集**：寻找有WHQL签名但存在漏洞的驱动（公开渠道有大量此类驱动）
2. **投放**：将漏洞驱动写入磁盘
3. **加载**：通过第一类或第二类方式正规加载该驱动（签名有效，系统放行）
4. **获取内核权限**：通过 `DeviceIoControl` 向驱动发送恶意构造的IOCTL，利用漏洞（如任意地址读写、执行未校验的调用）获取任意内核内存读写原语
5. **执行**：利用内核R/W原语做以下任意操作：
   - **不涉及注入**：调用 `ZwTerminateProcess` 终止EDR/AV进程、修改进程Token提权至SYSTEM、修改系统DSE状态标志、破坏PPL保护
   - **涉及注入内核**：将未签名的恶意驱动手动映射到内核内存并执行（绕过DSE）、将内核Shellcode写入内核并执行、修改内核数据结构（如 `HalDispatchTable`）植入恶意钩子

**微软应对**：
- **Microsoft Vulnerable Driver Blocklist**：Windows默认禁止已入库的已知漏洞驱动加载（但攻击者可通过修改PE头TimeDateStamp字段，在不破坏签名验证的前提下改变文件哈希，绕过基于哈希的阻断）
- **HVCI（Hypervisor-Protected Code Integrity）**：开启后限制内核可执行内存修改，可阻止部分BYOVD利用方式（如Shellcode注入、修改内核数据结构），但**不影响直接IOCTL调用终止进程等操作**

**签名要求**：漏洞驱动本身必须有WHQL签名

**隐蔽性**：
- 加载阶段：低（与第一/二类相同）
- 利用阶段：中（IOCTL调用是合法操作，但异常行为如进程被终止，会在系统日志中留下痕迹）


### 检测手段（按使用顺序）

#### 手段一：数字签名快速判断（最快，不依赖任何工具）

捕获到可疑 `.sys` 驱动文件后，右键 → 属性 → 数字签名：

| 签名状态 | 结论 |
|:---|:---|
| **有效WHQL签名** | 正规驱动，或BYOVD的漏洞驱动（需结合行为判断） |
| **测试签名** | 测试模式已开启（注意：HVCI开启时禁用测试模式），可能是开发调试或绕过DSE |
| **无签名** | 64位系统上无法加载（除非DSE已关闭），32位系统可以；也可能是已通过漏洞绕过DSE手动映射到内核的驱动（不会出现在磁盘上） |
| **签名过期/无效** | 数字签名无效，无法通过DSE正常加载（除非系统处于调试模式或32位系统），高危信号 |


#### 手段二：ProcMon动态监控 + API Monitor（主手段）

**ProcMon 过滤设置**：`Process Name` 为可疑进程名，`Operation` 包含 `RegSetValue`、`RegCreateKey`、`CreateFile`，`Path` 包含 `Services` 或 `.sys`。

**关键区分**：

| 加载方式 | 注册表操作 | 注册表写操作主体 | 磁盘文件读取 | ProcMon是否显示LoadImage |
|:---|:---|:---|:---|:---|
| **第一类（标准SCM）** | 有（写Services） | **`services.exe`** | 有 | 有（用户态视图可见） |
| **第二类（NtLoadDriver）** | 有（写Services） | **用户进程自身** | 有 | 有（用户态视图可见） |
| **第三类（ZwSetSystemInformation）** | **无** | — | **有**（标准调用需读盘） | **内核有回调，但ProcMon默认不显示**（需ETW捕获） |
| **第四类（BYOVD加载阶段）** | 有 | 同第一类或第二类 | 有（漏洞驱动.sys） | 同第一/二类 |

**为什么识别“谁在写注册表”是关键**：
- `services.exe` 写注册表 → 标准SCM流程
- 用户进程自己写注册表 → 绕过了SCM，是第二类
- 无注册表操作 → 第三类（但注意，第三类仍然会读磁盘文件）

**BYOVD利用阶段补充监控（ProcMon的盲区）**：
- ProcMon **看不到** `DeviceIoControl` 的具体调用内容。建议配合 **API Monitor** 监控用户态进程对 `DeviceIoControl` 的调用，重点关注 `dwIoControlCode` 参数是否匹配已知漏洞驱动的特定控制码（如任意地址读写的控制码）。
- 若BYOVD用于终止EDR/提权，可额外监控 **`NtOpenProcess`** 请求高权限（如 `PROCESS_TERMINATE`）访问敏感进程（如 `lsass.exe` 或安全产品进程）的行为——若调用进程是刚刚加载了WHQL驱动的进程，则高度可疑。


#### 手段三：driverquery快照对比（辅助手段）

```cmd
driverquery /v > driverlist_before.txt
（执行驱动加载操作）
driverquery /v > driverlist_after.txt
fc driverlist_before.txt driverlist_after.txt
```

**看什么**：对比前后驱动列表，找出新增的驱动及其路径。

> ⚠️ **局限性**：恶意驱动可能通过Rootkit技术隐藏自身，不出现在driverquery列表中。`ZwSetSystemInformation` 加载的驱动因不创建标准 `DRIVER_OBJECT`，也不会出现在列表中。


#### 手段四：注册表 Services 键快照对比（辅助手段）

```cmd
reg export HKLM\SYSTEM\CurrentControlSet\Services services_before.reg
（执行驱动加载操作）
reg export HKLM\SYSTEM\CurrentControlSet\Services services_after.reg
fc services_before.reg services_after.reg
```

**看什么**：对比前后注册表，找出新增的服务项，关注 `Type = 1`（内核驱动）的条目。

> ⚠️ **局限性**：某些恶意驱动加载后会自动删除自己的注册表项（自毁），此时reg对比抓不到。对 `ZwSetSystemInformation` 方式完全无效（因为它根本不写此键）。


### 综合判断表（修正版）

| 场景 | 数字签名 | ProcMon注册表操作主体 | 磁盘文件读取 | driverquery | reg对比 | 是否涉及内核注入 |
|:---|:---|:---|:---|:---|:---|:---|
| **第一类（标准SCM）** | WHQL | `services.exe` 写 | 有 | 新增驱动 | 新增服务项 | 否（标准加载） |
| **第二类（NtLoadDriver）** | WHQL | 用户进程写 | 有 | 新增驱动 | 新增服务项 | 否（标准加载） |
| **第三类（ZwSetSystemInformation）** | WHQL（标准调用必须） | **无** | **有**（标准调用） | 看不到 | 看不到 | 否（DriverEntry执行，非动态注入） |
| **第四类（BYOVD加载阶段）** | WHQL（漏洞驱动） | 同第一/二类 | 有 | 新增漏洞驱动 | 新增漏洞驱动服务 | 否（仅为加载跳板） |
| **第四类（BYOVD利用——终止进程/提权）** | 不适用 | 无新增 | 无新增 | 看不到 | 看不到 | 否（利用权限做操作） |
| **第四类（BYOVD利用——手动映射驱动/Shellcode到内核）** | 不适用 | 无新增 | 无新增（内存中操作） | 看不到 | 看不到 | **是**（恶意代码注入内核内存） |


### 💡 一句话总结

**四类加载方式的本质区别在于：走不走SCM、写不写注册表、以及是否创建标准驱动对象。**

**DSE是门槛，BYOVD是绕开门槛的“合法钥匙”，最终目的是获得内核内存操作能力。** 有了内核权限，攻击者可以做任何事，包括将恶意代码注入内核。

检测分层：
1. **数字签名**：看签名的有无和类型（最快的初步判断）
2. **ProcMon**：看注册表谁在写、写不写（区分一二三类）；**API Monitor** 补充监控 `DeviceIoControl` 控制码和 `NtOpenProcess` 高权限访问（覆盖BYOVD利用阶段）
3. **driverquery + reg**：做前后快照对比（验证辅助）
