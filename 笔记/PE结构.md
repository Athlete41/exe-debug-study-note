# PE 文件结构——逐字节实战手册

> **一句话**：PE 文件 = DOS 兼容壳 + PE 头（描述自身布局） + 节表（索引） + 节（代码/数据/资源）。
>
> **怎么读**：打开 x64dbg → 拖入一个 EXE → Ctrl+M 看到内存映射 → 用"文件偏移"模式 dump 头。本文全程用**一个真实的 64-bit Release EXE** 的原始 hex dump 做逐字段注解。

---

## 零、原始 dump

```
偏移        十六进制字节                                            ASCII
$0000       4D 5A 90 00 03 00 00 00 04 00 00 00 FF FF 00 00  MZ..........ÿÿ..
$0010       B8 00 00 00 00 00 00 00 40 00 00 00 00 00 00 00  ¸.......@.......
$0020       00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
$0030       00 00 00 00 00 00 00 00 00 00 00 00 80 00 00 00  ................
$0040       0E 1F BA 0E 00 B4 09 CD 21 B8 01 4C CD 21 54 68  ..º..´.Í!¸.LÍ!Th
$0050       69 73 20 70 72 6F 67 72 61 6D 20 63 61 6E 6E 6F  is program canno
$0060       74 20 62 65 20 72 75 6E 20 69 6E 20 44 4F 53 20  t be run in DOS
$0070       6D 6F 64 65 2E 0D 0D 0A 24 00 00 00 00 00 00 00  mode....$.......
$0080       50 45 00 00 64 86 0F 00 35 E0 5C 6A 00 72 00 00  PE..d...5à\j.r..
$0090       48 05 00 00 F0 00 27 00 0B 02 02 1E 00 20 00 00  H...ð.'...... ..
$00A0       00 42 00 00 00 0A 00 00 E0 14 00 00 00 10 00 00  .B......à.......
$00B0       00 00 40 00 00 00 00 00 00 10 00 00 00 02 00 00  ..@.............
$00C0       04 00 00 00 00 00 00 00 05 00 02 00 00 00 00 00  ................
$00D0       00 20 01 00 00 04 00 00 D9 DF 01 00 03 00 00 00  . ......Ùß......
$00E0       00 00 20 00 00 00 00 00 00 10 00 00 00 00 00 00  .. .............
$00F0       00 00 10 00 00 00 00 00 00 10 00 00 00 00 00 00  ................
$0100       00 00 00 00 10 00 00 00 00 00 00 00 00 00 00 00  ................
$0110       00 80 00 00 20 0C 00 00 00 00 00 00 00 00 00 00  .... ...........
$0120       00 50 00 00 AC 02 00 00 00 00 00 00 00 00 00 00  .P..¬...........
$0130       00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
$0140       00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
$0150       80 40 00 00 28 00 00 00 00 00 00 00 00 00 00 00  .@..(...........
$0160       00 00 00 00 00 00 00 00 9C 82 00 00 38 02 00 00  ............8...
$0170       00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
$0180       00 00 00 00 00 00 00 00 2E 74 65 78 74 00 00 00  .........text...
$0190       E0 1F 00 00 00 10 00 00 00 20 00 00 00 04 00 00  à........ ......
$01A0       00 00 00 00 00 00 00 00 00 00 00 00 60 00 50 60  ............`.P`
$01B0       2E 64 61 74 61 00 00 00 D0 00 00 00 00 30 00 00  .data...Ð....0..
$01C0       00 02 00 00 00 24 00 00 00 00 00 00 00 00 00 00  .....$..........
$01D0       00 00 00 00 40 00 50 C0 2E 72 64 61 74 61 00 00  ....@.PÀ.rdata..
$01E0       74 05 00 00 00 40 00 00 00 06 00 00 00 26 00 00  t....@.......&..
$01F0       00 00 00 00 00 00 00 00 00 00 00 00 40 00 60 40  ............@.`@
$0200       2E 70 64 61 74 61 00 00 AC 02 00 00 00 50 00 00  .pdata..¬....P..
$0210       00 04 00 00 00 2C 00 00 00 00 00 00 00 00 00 00  .....,..........
$0220       00 00 00 00 40 00 30 40 2E 78 64 61 74 61 00 00  ....@.0@.xdata..
$0230       50 02 00 00 00 60 00 00 00 04 00 00 00 30 00 00  P....`.......0..
$0240       00 00 00 00 00 00 00 00 00 00 00 00 40 00 30 40  ............@.0@
$0250       2E 62 73 73 00 00 00 00 80 09 00 00 00 70 00 00  .bss.........p..
$0260       00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
$0270       00 00 00 00 80 00 60 C0 2E 69 64 61 74 61 00 00  ......`À.idata..
$0280       20 0C 00 00 00 80 00 00 00 0E 00 00 00 34 00 00   ............4..
$0290       00 00 00 00 00 00 00 00 00 00 00 00 40 00 30 C0  ............@.0À
$02A0       2E 43 52 54 00 00 00 00 68 00 00 00 00 90 00 00  .CRT....h.......
$02B0       00 02 00 00 00 42 00 00 00 00 00 00 00 00 00 00  .....B..........
$02C0       00 00 00 00 40 00 40 C0 2E 74 6C 73 00 00 00 00  ....@.@À.tls....
$02D0       10 00 00 00 00 A0 00 00 00 02 00 00 00 44 00 00  ..... .......D..
$02E0       00 00 00 00 00 00 00 00 00 00 00 00 40 00 40 C0  ............@.@À
$02F0       2F 34 00 00 00 00 00 00 50 00 00 00 00 B0 00 00  /4......P....°..
```

这是 x64dbg 以文件偏移模式 dump 的。俗称"二进制情人"，直接拿它解剖。

---

## 一、DOS Header + DOS Stub（0x00 ~ 0x7F）

> **目的**：纯为了兼容 DOS。Windows 加载器只看其中一个字段（`e_lfanew`），其余全是历史包袱。

### 字段对照

```c
typedef struct _IMAGE_DOS_HEADER {
    WORD   e_magic;     // 0x00: 4D 5A → "MZ"
    WORD   e_cblp;      // 0x02: 90 00 → 0x0090
    // ... 中间一堆没用的 ...
    LONG   e_lfanew;    // 0x3C: 80 00 00 00 → 指向 0x80
} IMAGE_DOS_HEADER;
```

在 dump 中找：

```
$0030      ... 00 00 00 00 00 00 00 00 80 00 00 00
                                          ^^^^^^^^
                                    偏移 0x3C → e_lfanew = 0x80
```

**加载器干的事**：
1. 读文件头 2 字节 → 确认是 `4D 5A`（MZ）
2. 跳到 0x3C，读 4 字节 → 得 0x80
3. 跳到 0x80 → 找 `50 45 00 00`（"PE\0\0"）

**DOS Stub（0x40~0x7F）**：

```
$0040     0E 1F BA 0E 00 B4 09 CD 21 B8 01 4C CD 21 54 68   ..º..´.Í!¸.LÍ!Th
$0050     69 73 20 70 72 6F ...                               is program canno...
```

这是一段 16 位汇编，在 DOS 下执行时打印 `"This program cannot be run in DOS mode"`。
在 Windows 下完全忽略，改它不会影响程序行为——恶意软件常用它藏 payload。

---

## 二、PE Signature + IMAGE_FILE_HEADER（0x80 ~ 0x97）

### PE 总体头

```c
typedef struct _IMAGE_NT_HEADERS64 {
    DWORD Signature;                    // 4 字节, "PE\0\0"
    IMAGE_FILE_HEADER FileHeader;       // 20 字节
    IMAGE_OPTIONAL_HEADER64 OptionalHeader; // 240 字节（PE32+ for x64）
} IMAGE_NT_HEADERS64;
```

### Signature

```
$0080     50 45 00 00 64 86 0F 00 35 E0 5C 6A 00 72 00 00
          ^^^^^^^^^^^
          "PE\0\0" → 0x00004550
```

### IMAGE_FILE_HEADER（0x84~0x97）

```c
typedef struct _IMAGE_FILE_HEADER {
    WORD  Machine;              // 0x84: CPU 架构
    WORD  NumberOfSections;     // 0x86: 节数量
    DWORD TimeDateStamp;        // 0x88: 时间戳
    DWORD PointerToSymbolTable; // 0x8C: COFF 符号表偏移（调试用）
    DWORD NumberOfSymbols;      // 0x90: 符号数量
    WORD  SizeOfOptionalHeader; // 0x94: OptionalHeader 大小
    WORD  Characteristics;      // 0x96: 文件属性
} IMAGE_FILE_HEADER;            // 20 字节
```

逐字节对照：

| 文件偏移 | 字节序列 | 小端值 | 字段 | 含义 |
|:---|:---|:---|:---|:---|
| 0x84 | `64 86` | **0x8664** | **Machine** | **AMD64（x64）**——确认是 64 位 |
| 0x86 | `0F 00` | **15** | **NumberOfSections** | 共 **15 个节** |
| 0x88 | `35 E0 5C 6A` | 0x6A5CE035 | TimeDateStamp | Unix 时间戳 |
| 0x8C | `00 72 00 00` | 0x7200 | PointerToSymbolTable | 有符号表（可能是 Debug 编译） |
| 0x90 | `48 05 00 00` | 0x548=1352 | NumberOfSymbols | 1352 个 COFF 符号 |
| **0x94** | **`F0 00`** | **0x00F0** | **SizeOfOptionalHeader** | **240 字节 → PE32+（x64 专用）** |
| 0x96 | `27 00` | **0x0027** | **Characteristics** | 见下方分解 |

**实战判断 x86 vs x64 的二合一法**：
- `Machine = 0x014C` → 32 位 x86；`0x8664` → **64 位** ← 本例
- `SizeOfOptionalHeader = 0xE0` → PE32；**`0xF0`** → **PE32+** ← 本例

两者必须一致——不一致说明文件被篡改。

**Characteristics 位分解（0x0027）**：

```
0027 = 0000 0000 0010 0111 (二进制)
                │││  └── IMAGE_FILE_RELOCS_STRIPPED (1)  — 无重定位表
                ││└───── IMAGE_FILE_EXECUTABLE_IMAGE (2)  — 可执行 ✓
                │└────── IMAGE_FILE_LINE_NUMS_STRIPPED (4)
                └─────── IMAGE_FILE_LARGE_ADDRESS_AWARE (32) — 能跑在 >2GB 地址
```

---

## 三、IMAGE_OPTIONAL_HEADER64（0x98 ~ 0x107）

> 名字叫 Optional，实际**必须有**。64 位版本 240 字节。

### 结构（x64 / PE32+ 版）

```c
typedef struct _IMAGE_OPTIONAL_HEADER64 {
    // — 标准字段 —
    WORD  Magic;                     // 0x98
    BYTE  MajorLinkerVersion;        // 0x9A
    BYTE  MinorLinkerVersion;        // 0x9B
    DWORD SizeOfCode;                // 0x9C
    DWORD SizeOfInitializedData;     // 0xA0
    DWORD SizeOfUninitializedData;   // 0xA4
    DWORD AddressOfEntryPoint;       // 0xA8  ← ★ 关键：入口点 RVA
    DWORD BaseOfCode;                // 0xAC
    // PE32+ 没有 BaseOfData 字段！
    ULONGLONG ImageBase;             // 0xB0  ← ★ x64 下 8 字节
    DWORD SectionAlignment;          // 0xB8
    DWORD FileAlignment;             // 0xBC
    // ... 操作系统版本、子版本 ...
    WORD  MajorSubsystemVersion;     // 0xC8
    WORD  MinorSubsystemVersion;     // 0xCA
    DWORD SizeOfImage;               // 0xD0  ← ★ 内存总大小
    DWORD SizeOfHeaders;             // 0xD4  ← ★ 头总大小
    DWORD CheckSum;                  // 0xD8
    WORD  Subsystem;                 // 0xDC
    WORD  DllCharacteristics;        // 0xDE
    ULONGLONG SizeOfStackReserve;    // 0xE0
    ULONGLONG SizeOfStackCommit;     // 0xE8
    ULONGLONG SizeOfHeapReserve;     // 0xF0
    ULONGLONG SizeOfHeapCommit;      // 0xF8
    DWORD LoaderFlags;               // 0x100
    DWORD NumberOfRvaAndSizes;       // 0x104  ← DataDirectory 数组长度
    IMAGE_DATA_DIRECTORY DataDirectory[16]; // 0x108 起
} IMAGE_OPTIONAL_HEADER64;
```

### 关键字段对照

```
$0098     0B 02 02 1E 00 20 00 00 ...
          ^^^^^^  ^^^^^^  ^^^^^^^^^^
          Magic   LnkVer  SizeOfCode

$00A8     E0 14 00 00 00 10 00 00 ...
          ^^^^^^^^^^  ^^^^^^^^^^
          EntryPoint  BaseOfCode
```

| 文件偏移 | 字节 | 值 | 字段 | 含义 |
|:---|:---|:---|:---|:---|
| **0x98** | `0B 02` | **0x020B** | **Magic** | **PE32+（x64）**——再次确认 |
| 0x9A-0x9B | `02 1E` | 2.30 | LinkerVersion | MSVC 链接器版本 |
| 0x9C | `00 20 00 00` | 0x2000 | SizeOfCode | `.text` 节在文件中占 8KB |
| 0xA0 | `00 42 00 00` | 0x4200 | SizeOfInitializedData | `.data` + `.rdata` 等约 16KB |
| 0xA4 | `00 0A 00 00` | 0x0A00 | SizeOfUninitializedData | BSS 约 2.5KB |
| **0xA8** | **`E0 14 00 00`** | **0x14E0** | **AddressOfEntryPoint** | **入口 RVA = 0x14E0** |
| 0xAC | `00 10 00 00` | 0x1000 | BaseOfCode | 代码节起点 RVA |
| **0xB0** | `00 00 40 00 00 00 00 00` | **0x400000** | **ImageBase** | **首选加载基址** |
| **0xB8** | `00 10 00 00` | **0x1000** | **SectionAlignment** | **内存对齐 = 4KB** |
| **0xBC** | `00 02 00 00` | **0x200** | **FileAlignment** | **文件对齐 = 512B** |
| 0xC8 | `05 00` | 5 | MajorSubsystemVer | NT 5.x+ |
| **0xD0** | `00 20 01 00` | **0x12000** | **SizeOfImage** | **加载到内存后占 72KB** |
| **0xD4** | `00 04 00 00` | **0x400** | **SizeOfHeaders** | **头总大小 1024 字节** |
| 0xD8 | `D9 DF 01 00` | 0x1DFD9 | CheckSum | 校验和 |
| **0xDC** | `03 00` | **3** | **Subsystem** | **IMAGE_SUBSYSTEM_WINDOWS_CUI**（控制台程序） |
| 0xE0 | `00 00 20 00 00 00 00 00` | **2MB** | **SizeOfStackReserve** | 栈保留大小 |
| 0xE8 | `00 10 00 00 00 00 00 00` | **1MB** | **SizeOfStackCommit** | 栈提交大小 |
| 0xF0 | `00 00 10 00 00 00 00 00` | **1MB** | SizeOfHeapReserve | 堆保留 |
| 0x100 | `00 00 00 00` | 0 | LoaderFlags | |
| **0x104** | `10 00 00 00` | **16** | **NumberOfRvaAndSizes** | **数据目录数组长度** |

### SectionAlignment vs FileAlignment——核心概念

| | 文件对齐 | 内存对齐 |
|:---|:---|:---|
| 值 | 0x200（512B） | 0x1000（4096B） |
| 含义 | 文件中节按 512B 对齐 | 内存中页按 4KB 对齐 |
| 效果 | 文件更紧凑 | 符合分页机制，但产生空隙 |

**直观理解**：`.text` 在文件中可能只占 0x1FE0 字节，但文件按 0x200 对齐存（0x2000），内存按 0x1000 对齐加载（占据 0x1000~0x2FFF 两个页）。

---

## 四、DataDirectory 数据目录表（0x108 ~ 0x187）

> **数据目录不是节**——它是 PE 头中的索引表，告诉你"某某表在哪个 RVA、有多大"。

```c
typedef struct _IMAGE_DATA_DIRECTORY {
    DWORD VirtualAddress;   // RVA
    DWORD Size;
} IMAGE_DATA_DIRECTORY;     // 8 字节 × 16 条目
```

用 dump 找实际的数据目录条目：

```
$0108     00 00 00 00 00 00 00 00    ← [0] EXPORT: RVA=0, Size=0（无导出）
$0110     00 80 00 00 20 0C 00 00    ← [1] IMPORT: RVA=0x8000, Size=0xC20  ✓
$0118     00 00 00 00 00 00 00 00    ← [2] RESOURCE: 无
$0120     00 50 00 00 AC 02 00 00    ← [3] EXCEPTION: RVA=0x5000, Size=0x2AC ✓
$0128     00 00 00 00 00 00 00 00    ← [4] SECURITY: 无
$0130     00 00 00 00 00 00 00 00    ← [5] BASERELOC: 无（已剥离 ✓）
$0138     00 00 00 00 00 00 00 00    ← [6] DEBUG: 无
$0140     00 00 00 00 00 00 00 00    ← [7] ARCH: 无
$0148     00 00 00 00 00 00 00 00    ← [8] GLOBALPTR: 无
$0150     80 40 00 00 28 00 00 00    ← [9] TLS: RVA=0x4080, Size=0x28 ✓
$0158     00 00 00 00 00 00 00 00    ←[10] LOAD_CONFIG: 无
$0160     00 00 00 00 00 00 00 00    ←[11] BOUND_IMPORT: 无
$0168     00 00 00 00 00 00 00 00    ←[12] IAT: 无
$0170     00 00 00 00 00 00 00 00    ←[13] DELAY_IMPORT: 无
$0178     00 00 00 00 00 00 00 00    ←[14] COM_DESCRIPTOR: 无
$0180     00 00 00 00 00 00 00 00    ←[15] 保留
```

**这个文件中实际有效的只有 3 个条目**（Release 版，很干净）：

| 索引 | 名称 | RVA → 对应节 | Size | 用途 |
|:---|:---|:---|:---|:---|
| [1] | IMPORT | 0x8000 → `.idata` | 0xC20 | 导入表（依赖哪些 DLL 和函数） |
| [3] | EXCEPTION | 0x5000 → `.pdata` | 0x2AC | x64 异常处理函数表 |
| [9] | TLS | 0x4080 → `.rdata` | 0x28 | 线程局部存储回调 |

---

## 五、Section Table 节表（0x188 ~ 0x3DF）

> 每个节 40 字节，数组长度 = `NumberOfSections`（本例 15 个）。

### 结构

```c
typedef struct _IMAGE_SECTION_HEADER {
    BYTE  Name[8];               // 节名（如 ".text"）
    union {
        DWORD PhysicalAddress;   // OBJ 文件用
        DWORD VirtualSize;       // 内存中节的大小 ← ★ 重点
    } Misc;
    DWORD VirtualAddress;        // 节的 RVA（相对 ImageBase）
    DWORD SizeOfRawData;         // 文件中对齐后的节大小
    DWORD PointerToRawData;      // 文件中对齐后的节偏移
    DWORD PointerToRelocations;  // OBJ 文件用
    DWORD PointerToLinenumbers;  // 调试用
    WORD  NumberOfRelocations;
    WORD  NumberOfLinenumbers;
    DWORD Characteristics;       // 属性（代码/数据/可读/可写/可执行）
} IMAGE_SECTION_HEADER;          // 40 字节
```

### 关键对照——看几个典型节

#### `.text`——代码节

```
$0188     2E 74 65 78 74 00 00 00  E0 1F 00 00  00 10 00 00  .text...à......
          ^^^^^^^^^^^^^^^^^^^^^^^  ^^^^^^^^^^  ^^^^^^^^^^
          Name[8] = ".text"        VirtualSize  VirtualAddress
                                   = 0x1FE0     = 0x1000

$0198     00 20 00 00  00 04 00 00  00 00 00 00  00 00 00 00  . .............
          ^^^^^^^^^^  ^^^^^^^^^^  ^^^^^^^^^^  ^^^^^^^^^^
          SizeOfRaw   PointerTo   Reloc        LineNum
          Data=0x2000 RawData=0x400  (0)         (0)

$01A8     00 00  00 00  60 00 50 60
          ^^^^^^ ^^^^^^ ^^^^^^^^^^
          #Reloc #Line  Characteristics = 0x60500060
```

拆解字段：

| 字段 | 值 | 含义 |
|:---|:---|:---|
| **Name** | `.text` | 代码节 |
| **VirtualSize** | **0x1FE0** | 内存中实际大小（8132 字节代码） |
| **VirtualAddress** | **0x1000** | 加载到 RVA 0x1000 |
| SizeOfRawData | 0x2000 | 文件中占 8KB（对齐到 0x200） |
| PointerToRawData | 0x400 | **文件偏移 0x400 开始才是真正的代码** |
| **Characteristics** | **0x60500060** | 见下方分解 |

**Characteristics 分解**：

```
0x60500060 =  二进制拆分:
    60000060 → IMAGE_SCN_CNT_CODE (0x20)
             → IMAGE_SCN_MEM_EXECUTE (0x20000000)
             → IMAGE_SCN_MEM_READ (0x40000000)
             → 0x00500000 →...
```

标准 `.text` 属性：`CODE | EXECUTE | READ`——**可执行可读但不可写**。

#### `.data`——已初始化数据节

```
$01B4     2E 64 61 74 61 00 00 00  D0 00 00 00  00 30 00 00  .data...Ð....0..
$01C8     00 02 00 00  00 24 00 00  00 00 00 00  00 00 00 00
$01D0     00 00 00 00  40 00 50 C0
```

| 字段 | 值 | 含义 |
|:---|:---|:---|
| Name | `.data` | |
| **VirtualSize** | **0xD0** | 208 字节全局变量 |
| **VirtualAddress** | **0x3000** | RVA = 0x3000 |
| SizeOfRawData | 0x200 | 文件中对齐后 512B |
| PointerToRawData | 0x2400 | 文件偏移 0x2400 |
| Characteristics | 0xC0500040 | `INITIALIZED_DATA \| READ \| WRITE` |

#### `.bss`——未初始化数据节（BSS）

```
$0254     2E 62 73 73 00 00 00 00  80 09 00 00  00 70 00 00  .bss.........p..
$0268     00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00
$0270     00 00 00 00  80 00 60 C0
```

| 字段 | 值 | 含义 |
|:---|:---|:---|
| Name | `.bss` | |
| **VirtualSize** | **0x980** | **内存中占 2432 字节** |
| VirtualAddress | 0x7000 | |
| **SizeOfRawData** | **0** | **❗文件中不占空间** |
| **PointerToRawData** | **0** | **文件中不存在** |

**这就是 BSS 的含义**：声明了变量但没初值，不需要存文件，加载时在内存清 0 就行。

#### `.pdata`——x64 异常处理节

```
$0200     2E 70 64 61 74 61 00 00  AC 02 00 00  00 50 00 00  .pdata..¬....P..
$0210     00 04 00 00  00 2C 00 00
```

| 字段 | 值 | 含义 |
|:---|:---|:---|
| Name | `.pdata` | **x64 才有** |
| VirtualSize | 0x2AC  | 异常函数表 |
| VirtualAddress | 0x5000 | 匹配 DataDirectory[3] 的 RVA |
| SizeOfRawData | 0x400 | |
| PointerToRawData | 0x2C00 | |
| Characteristics | 0x40300040 | `INITIALIZED_DATA \| READ` |

#### 用 `.pdata` 特征判断 x64

记住：**一个 PE 文件有 `.pdata` 和 `.xdata` 节，几乎肯定是 x64**。x86 用基于帧的异常处理（`fs:[0]`），不需要这些。

#### 其他节一览

| 节名 | RVA | 文件偏移 | VirtualSize | 作用 |
|:---|:---|:---|:---|:---|
| .text | 0x1000 | 0x400 | 0x1FE0 | 代码 |
| .data | 0x3000 | 0x2400 | 0xD0 | 全局变量 |
| .rdata | 0x4000 | 0x2600 | 0x574 | 只读常量 |
| .pdata | 0x5000 | 0x2C00 | 0x2AC | 异常处理表 |
| .xdata | 0x6000 | 0x3000 | 0x250 | 异常展开数据 |
| .bss | 0x7000 | — | 0x980 | 未初始化变量（无文件数据） |
| .idata | 0x8000 | 0x3400 | 0xC20 | 导入表 |
| .CRT | 0x9000 | 0x4200 | 0x68 | C 运行时初始化 |
| .tls | 0xA000 | 0x4400 | 0x10 | 线程局部存储 |
| /4 | 0xB000 | 0x4600 | 0x50 | 链接器生成（长名节） |
| /19 | 0xC000 | 0x4800 | 0x1F08 | 链接器生成 |
| /31 | 0xE000 | 0x6800 | 0x149 | 链接器生成 |
| /45 | 0xF000 | 0x6A00 | 0x222 | 链接器生成 |
| /57 | 0x10000 | 0x6E00 | 0x48 | 链接器生成 |
| /70 | 0x11000 | 0x7000 | 0x9B | 链接器生成 |

**长节名**（`/4`、`/19` 等）：当节名超过 8 个字符时，MSVC 链接器把名字存在字符串表里，节表 Name 字段填 `/<十进制序号>`。

### 磁盘 vs 内存——定位公式

```
文件中的数据位置 = PointerToRawData + (RVA - VirtualAddress)
```

**例子**：入口点 RVA = 0x14E0，它在代码节内（VirtualAddress=0x1000）。
```
文件偏移 = 0x400 + (0x14E0 - 0x1000) = 0x400 + 0x4E0 = 0x4E0
```

你从文件的 0x4E0 处就能找到入口点的机器码。

---

## 六、几种你一定会遇到的"拿来就用"的节

| 节名 | 典型内容 | 属性 | 备注 |
|:---|:---|:---|:---|
| `.text` | 可执行代码 | 读+执行 | 逆向分析的主战场 |
| `.data` | 全局变量（有初值） | 读+写 | |
| `.rdata` | 常量、导入/导出表 | 只读 | 查看导入表就在这 |
| `.pdata` | 异常处理表 | 只读 | x64 才有的节 |
| `.reloc` | 基址重定位表 | 只读 | DLL 必备，EXE 可剥离 |
| `.rsrc` | 图标/版本/对话框 | 只读 | 用 Resource Hacker 改 |
| `.bss` | 未初始化全局变量 | 读+写 | 文件中不存在，加载时清 0 |
| `.tls` | 线程局部存储 | 读+写 | 多线程 TLS 变量 |
| `.idata` | 导入表 | 只读 | 有时合并到 `.rdata` |

---

## 七、磁盘布局 vs 内存布局——最核心的概念

```
磁盘上的 .exe：                         内存中的进程：
┌────────────────┐                    ┌────────────────┐  ← ImageBase
│ DOS/PE 头      │                    │ DOS/PE 头      │
│ 节表           │  按 FileAlignment │ 节表           │
├────────────────┤  (0x200) 对齐     ├────────────────┤  ← SectionAlignment
│ .text          │                    │ .text          │  (0x1000, 即4KB)
│                │                    │                │
├────────────────┤                    ├────────────────┤
│ .rdata         │                    │ .rdata         │
├────────────────┤  ← 文件里紧凑     ├────────────────┤
│ .data          │    但可能不规整    │ .data          │
├────────────────┤                    ├────────────────┤
│ .reloc / etc   │                    │ .bss           │  ← 内存中出现
│                │                    │ (已清 0)       │
└────────────────┘                    │ ▒▒ 填充 0 ▒▒   │  ← 对齐填充
                                      └────────────────┘
```

| 对比维度 | 磁盘上 | 内存中 |
|:---|:---|:---|
| 对齐粒度 | `FileAlignment`（0x200=512B） | `SectionAlignment`（0x1000=4KB） |
| 空隙 | 小填充 | 每节从页边界起，大量 0 填充 |
| 导入表 | 函数名/序号（ILT/INT） | IAT 已填入实际函数地址 |
| BSS 区 | 不存在 | 加载器分配并清 0 |
| 重定位表 | 完整保留 | 加载器用完后可丢弃 |

---

## 八、完整的加载流程（Windows 创建进程）

```
1. 读 DOS Header → 从 0x3C 取 e_lfanew（=0x80）
2. 验证 "PE\0\0" → 开始解析 PE 头
3. 读 Machine → 确认 x64（0x8664）
4. 读 OptionalHeader：
   - ImageBase → 首选基址
   - SizeOfImage → 分配 0x12000 字节虚拟空间
   - AddressOfEntryPoint → 记住入口（RVA 0x14E0）
   - Subsystem → 控制台 / GUI
5. 按节表的 15 个条目，逐节映射：
   - .text → 从文件 0x400 → 内存 RVA 0x1000，标记 RX
   - .data → 从文件 0x2400 → 内存 RVA 0x3000，标记 RW
   - .bss → 在内存 RVA 0x7000 分配 0x980 字节，全清 0
   - 其余类推...
6. 如果实际基址 ≠ ImageBase，走基址重定位
7. 解析 DataDirectory[1]（导入表）：
    → 在 RVA 0x8000 找到 IMAGE_IMPORT_DESCRIPTOR 数组
    → 加载依赖 DLL，查函数地址，填入 IAT
8. 初始化 TLS（线程局部存储）
9. 设置主线程 RIP = ImageBase + 0x14E0 → 开始执行
```

---

## 九、小抄——快速字段索引

> 把这张表存着，x64dbg 里看到偏移直接查。

| 偏移 | 内容 | 大小 |
|:---|:---|:---|
| 0x00 | DOS MZ 签名 | 2 |
| **0x3C** | **`e_lfanew` → PE 头偏移** | **4** |
| 0x40~0x7F | DOS Stub | ~64 |
| **0x80** | **"PE\0\0" 签名** | 4 |
| 0x84 | Machine（0x8664=x64） | 2 |
| 0x86 | NumberOfSections | 2 |
| 0x94 | SizeOfOptionalHeader（0xF0=PE32+） | 2 |
| 0x96 | Characteristics | 2 |
| **0x98** | **OptionalHeader 开始** | — |
| 0x98 | Magic（0x20B=PE32+） | 2 |
| **0xA8** | **AddressOfEntryPoint（入口 RVA）** | **4** |
| **0xB0** | **ImageBase** | **8** |
| 0xB8 | SectionAlignment（0x1000） | 4 |
| 0xBC | FileAlignment（0x200） | 4 |
| **0xD0** | **SizeOfImage** | **4** |
| 0xD4 | SizeOfHeaders | 4 |
| 0xDC | Subsystem（2=GUI, 3=Console） | 2 |
| **0x108** | **DataDirectory[0]（导出表）** | 8 |
| **0x110** | **DataDirectory[1]（导入表）** | 8 |
| **0x120** | **DataDirectory[3]（异常表）** | 8 |
| **0x188** | **节表开始** | 40×N |

---

## 十、常见问题

### Q: 加载后入口地址怎么算？

```
实际入口 VA = ImageBase（或 ASLR 基址） + AddressOfEntryPoint
```

例如本例入口 RVA = 0x14E0，如果 ImageBase = 0x400000：
```
入口 VA = 0x400000 + 0x14E0 = 0x4014E0
```

在 x64dbg 里看到程序停在 0x4014E0（或 ASLR 后的某个地址），那 0x14E0 这个偏移始终不变。

### Q: 怎么找导入表？

1. 读 DataDirectory[1] → 得 RVA=0x8000, Size=0xC20
2. 查节表 → RVA 0x8000 落在 `.idata` 节（RVA 0x8000, PointerToRawData=0x3400）
3. 文件偏移 = 0x3400 + (0x8000 - 0x8000) = **0x3400**
4. 去文件 0x3400 处，是 `IMAGE_IMPORT_DESCRIPTOR` 数组

### Q: 我改了一个全局变量的初值，为啥不生效？

很可能改了 `.data` 节在文件中的原始数据，但 PE 头里的 `CheckSum` 没更新——而且系统加载时也不校验（除非是签名的驱动程序）。不生效的原因多半是改错了偏移：变量在内存的地址是 RVA，要反算回文件偏移再改。

### Q: 手动把某节的 `Characteristics` 加上"可写"会怎样？

可以用，比如给 `.text` 加写属性就可以做内存补丁。但某些安全软件会检测。**不会蓝屏**，只是破坏了 DEP。

---

> **一句话记忆**：
>
> DOS 壳 → `e_lfanew` 找到 PE 头 → 数据目录定位导入/导出/异常表 → 节表描述各段在哪 → IAT 完成动态链接 → `.reloc` 应对基址漂移 → **磁盘紧凑，内存对齐**。
