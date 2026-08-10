### 📓 Windows 用户态代码加载调用链（极简实战版）
**前提**：本篇是以用户态程序的视角，用户态程序加载用户态程序的调用链。
**核心逻辑**：代码进进程无非两条路——要么**磁盘文件经过内核加载**，要么**纯内存数据直接塞进去执行**。

---

### 前言：CreateFile 的真相
`CreateFile` 是 Windows 底层“万能钥匙”，**不等于创建文件**。它用于打开或创建各种对象（文件、设备、管道、目录）。判断真实意图，看 ProcMon 详情列的 **`Disposition`**：
- `OPEN`（打开已有）、`CREATE`（新建）、`OPENIF`（有则开无则建）。

---

### 两类加载方式（再无其他）

#### 第一类：标准磁盘加载（文件落地）
靠 Windows 系统机制从磁盘加载 PE 模块，系统内核全程知情。

**难度**：⭐

**调用链**：
`LoadLibrary`（用户态）  
→ `NtOpenFile`（打开磁盘文件）  
→ **`NtCreateSection`**（内核创建节对象，文件→内存的桥梁）  
→ `MapViewOfFile`（底层 `NtMapViewOfSection`，映射进进程）  
→ **`LoadImage`**（内核回调，正式记录模块）

**ProcMon 特征**：
- 出现 `CreateFile` 指向 `.dll` 路径
- 紧跟 **`LoadImage`** 事件（目标进程和 `System` 进程各有一条记录，内核正式登记）
- 全程有磁盘读写轨迹


#### 第二类：内存无文件注入（不落地）
不走系统加载器，直接把二进制数据塞进目标进程内存，手动执行。**反射式 DLL（有PE结构）和 Shellcode（裸码）都走这条路，只是写入的内容不同。**

**难度**：⭐⭐⭐

**调用链（统一）**：
`VirtualAllocEx`（申请内存）  
→ `WriteProcessMemory`（写入二进制数据）  
→ `CreateRemoteThread` / APC（创建执行流）

**ProcMon 特征（统一）**：
- 看到 `VirtualAllocEx` + 跨进程 `WriteProcessMemory`
- **没有 `CreateFile`**（无磁盘操作）
- **没有 `LoadImage`**（内核不知情，隐蔽性强）

**内部分支区分**：
- 写的是完整 PE 字节码，**注入器需手动修复重定位表和导入表（IAT）**，再跳转入口点 = **反射式 DLL 注入**
- 写的是位置无关的裸机器码，直接跳转起始地址 = **Shellcode 注入**

> ⚠️ **重要提醒**：ProcMon 监控不到线程创建（`CreateRemoteThread` 最终走 `NtCreateThreadEx`，这是内核调度行为）。要抓线程，得上 **API Monitor** 或 **WinDbg**。


### 🔍 最终判断法则（一张表搞定）

| ProcMon 看到什么 | 结论 | 难度 |
| :--- | :--- | :--- |
| `CreateFile`（磁盘路径）+ `LoadImage`（目标进程+System双记录） | **标准磁盘加载** | ⭐ |
| `VirtualAllocEx` + `WriteProcessMemory`（跨进程写数据），无 `CreateFile`，无 `LoadImage` | **内存注入**（不管里面是 PE 还是 Shellcode） | ⭐⭐⭐ |


### 💡 难度说明

| 难度 | 含义 |
|:---|:---|
| ⭐ | 基础操作，调用系统API即可完成，无需手工解析PE结构 |
| ⭐⭐⭐ | 需跨进程操作、手工修复重定位/导入表，或编写位置无关的Shellcode，技术门槛较高 |