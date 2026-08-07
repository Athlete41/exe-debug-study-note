"""
Cracker 驱动通信模块（驼峰命名风格）
基于逆向文档实现，支持所有 IOCTL 指令。
使用前需确保驱动已加载（如通过漏洞加载器或测试签名模式）。
"""
import ctypes
from ctypes import wintypes, c_ulonglong, Structure, byref, sizeof, WinError
import sys
from array import array

# ---------- Windows API 常量 ----------
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x80
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

# ---------- IOCTL 指令码 ----------
IOCTL_READ_WRITE_MEMORY = 0x238000
IOCTL_READ_WRITE_MEMORY_MDL = 0x238004
IOCTL_GET_MODULE_BASE = 0x238008
IOCTL_GET_PROC_ADDRESS = 0x23800C
IOCTL_VIRTUAL_ALLOC = 0x238010
IOCTL_VIRTUAL_FREE = 0x238014
IOCTL_VIRTUAL_PROTECT = 0x238018
IOCTL_GET_PID_BY_NAME = 0x23801C
IOCTL_SET_PROTECT_FLAG = 0x238020
IOCTL_TERMINATE_PROCESS = 0x238024
IOCTL_UNLOAD_DRIVER = 0x238040
IOCTL_DELETE_FILE = 0x238044
IOCTL_CREATE_REMOTE_THREAD = 0x238048
IOCTL_INJECT_DLL = 0x23804C

# ---------- 参数结构（40 字节） ----------
class IOCTL_PARAMS(Structure):
    _fields_ = [
        ("arg0", c_ulonglong),  # +0x00
        ("arg1", c_ulonglong),  # +0x08
        ("arg2", c_ulonglong),  # +0x10
        ("arg3", c_ulonglong),  # +0x18
        ("arg4", c_ulonglong),  # +0x20
    ]

# ---------- Windows API 函数 ----------
kernel32 = ctypes.windll.kernel32

CreateFileW = kernel32.CreateFileW
CreateFileW.argtypes = [
    wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
    wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD,
    wintypes.HANDLE
]
CreateFileW.restype = wintypes.HANDLE

DeviceIoControl = kernel32.DeviceIoControl
DeviceIoControl.argtypes = [
    wintypes.HANDLE, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD,
    wintypes.LPVOID, wintypes.DWORD, wintypes.LPDWORD, wintypes.LPVOID
]
DeviceIoControl.restype = wintypes.BOOL

CloseHandle = kernel32.CloseHandle
CloseHandle.argtypes = [wintypes.HANDLE]
CloseHandle.restype = wintypes.BOOL

# ---------- 工具函数 ----------
def openDevice():
    """
    打开 \\.\Cracker 设备
    返回 HANDLE，失败返回 None
    """
    handle = CreateFileW(
        "\\\\.\\Cracker",
        GENERIC_READ | GENERIC_WRITE,
        0, None, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, None
    )
    if handle == INVALID_HANDLE_VALUE:
        raise WinError()
    return handle

def closeDevice(handle):
    """关闭设备句柄"""
    if handle:
        CloseHandle(handle)

def deviceIoctl(handle, code, arg0=0, arg1=0, arg2=0, arg3=0, arg4=0):
    """
    发送 IOCTL 并返回 (status, resultArg3)
    status: 驱动返回的状态码（0=成功）
    resultArg3: 部分指令将结果写回 arg3（如基址、PID等）
    """
    params = IOCTL_PARAMS(arg0, arg1, arg2, arg3, arg4)
    bytesReturned = wintypes.DWORD()
    success = DeviceIoControl(
        handle,
        code,
        byref(params), sizeof(params),   # 输入和输出共用同一缓冲区
        byref(params), sizeof(params),
        byref(bytesReturned),
        None
    )
    if not success:
        raise WinError()
    # 返回状态（arg0）和结果（arg3）
    return params.arg0, params.arg3

# ---------- 高级封装指令 ----------
def readWriteMemory(handle, pid, targetAddr, size, localBuf, direction):
    """
    direction: 0=读 (目标→本地), 1=写 (本地→目标)
    返回状态
    """
    # localBuf 需为整数地址（如 buffer 的地址），或直接传入整数
    return deviceIoctl(handle, IOCTL_READ_WRITE_MEMORY,
                       arg0=pid, arg1=targetAddr, arg2=size,
                       arg3=localBuf, arg4=direction)

def readWriteMemoryMdl(handle, pid, targetAddr, size, localBuf, direction):
    """MDL版，无可靠返回值，但调用方式相同"""
    return deviceIoctl(handle, IOCTL_READ_WRITE_MEMORY_MDL,
                       arg0=pid, arg1=targetAddr, arg2=size,
                       arg3=localBuf, arg4=direction)

def getModuleBase(handle, pid, moduleNameAnsi):
    """按模块名获取基址，返回 (status, base)"""
    nameBuf = ctypes.create_string_buffer(moduleNameAnsi.encode('ascii'))
    result = ctypes.c_ulonglong(0)
    status, _ = deviceIoctl(handle, IOCTL_GET_MODULE_BASE,
                            arg0=pid,
                            arg1=ctypes.addressof(nameBuf),
                            arg3=ctypes.addressof(result))
    return status, result.value

def getProcAddress(handle, pid, moduleBase, funcNameAnsi):
    """
    获取函数地址
    返回 (status, funcAddress)
    """
    nameBuf = ctypes.create_string_buffer(funcNameAnsi.encode('ascii'))
    addr = ctypes.addressof(nameBuf)
    return deviceIoctl(handle, IOCTL_GET_PROC_ADDRESS,
                       arg0=pid, arg1=moduleBase, arg2=addr, arg3=0, arg4=0)

def virtualAlloc(handle, pid, size):
    """远程分配内存，返回 (status, baseAddress)"""
    return deviceIoctl(handle, IOCTL_VIRTUAL_ALLOC,
                       arg0=pid, arg1=0, arg2=size, arg3=0, arg4=0)

def virtualFree(handle, pid, baseAddr):
    """释放远程内存"""
    return deviceIoctl(handle, IOCTL_VIRTUAL_FREE,
                       arg0=pid, arg1=baseAddr, arg2=0, arg3=0, arg4=0)

def virtualProtect(handle, pid, baseAddr, size, newProtect):
    """修改内存保护，返回 (status, oldProtect)"""
    return deviceIoctl(handle, IOCTL_VIRTUAL_PROTECT,
                       arg0=pid, arg1=baseAddr, arg2=size,
                       arg3=0, arg4=newProtect)

def getPidByName(handle, processNameAnsi):
    """按进程名获取 PID，返回 (status, pid)"""
    nameBuf = ctypes.create_string_buffer(processNameAnsi.encode('ascii'))
    result = ctypes.c_ulonglong(0)                     # ← 分配可写内存作为输出槽
    status, _ = deviceIoctl(handle, IOCTL_GET_PID_BY_NAME,
                            arg0=ctypes.addressof(nameBuf),
                            arg3=ctypes.addressof(result))   # ← 传地址，不是 0
    return status, result.value                         # ← 从 result 读回 PID

def setProtectFlag(handle, pid, flag):
    """flag=0清除，非0设置"""
    return deviceIoctl(handle, IOCTL_SET_PROTECT_FLAG,
                       arg0=pid, arg1=0, arg2=0, arg3=0, arg4=flag)

def terminateProcess(handle, pid):
    """终止进程"""
    return deviceIoctl(handle, IOCTL_TERMINATE_PROCESS,
                       arg0=pid, arg1=0, arg2=0, arg3=0, arg4=0)

def unloadDriver(handle):
    """卸载驱动（设备将消失，句柄失效）"""
    return deviceIoctl(handle, IOCTL_UNLOAD_DRIVER,
                       arg0=0, arg1=0, arg2=0, arg3=0, arg4=0)

def deleteFile(handle, filePathAnsi):
    """删除文件（路径 ANSI）"""
    pathBuf = ctypes.create_string_buffer(filePathAnsi.encode('ascii'))
    addr = ctypes.addressof(pathBuf)
    return deviceIoctl(handle, IOCTL_DELETE_FILE,
                       arg0=addr, arg1=0, arg2=0, arg3=0, arg4=0)

def createRemoteThread(handle, pid, startAddr, parameter):
    """创建远程线程，返回状态"""
    return deviceIoctl(handle, IOCTL_CREATE_REMOTE_THREAD,
                       arg0=pid, arg1=startAddr, arg2=parameter, arg3=0, arg4=0)

def injectDll(handle, pid, dllPathAnsi):
    """注入 DLL，返回状态"""
    pathBuf = ctypes.create_string_buffer(dllPathAnsi.encode('ascii'))
    addr = ctypes.addressof(pathBuf)
    return deviceIoctl(handle, IOCTL_INJECT_DLL,
                       arg0=pid, arg1=addr, arg2=0, arg3=0, arg4=0)


# ---------- 基本类型读取辅助函数 ----------
def readUInt32(handle, pid, address) -> int | None:
    """读取 4 字节无符号整数 (uint32_t)"""
    buf = ctypes.c_uint32()
    status, _ = readWriteMemory(handle, pid, address, 4, ctypes.addressof(buf), 0)
    return buf.value if status == 0 else None

def readInt32(handle, pid, address) -> int | None:
    """读取 4 字节有符号整数 (int32_t)"""
    buf = ctypes.c_int32()
    status, _ = readWriteMemory(handle, pid, address, 4, ctypes.addressof(buf), 0)
    return buf.value if status == 0 else None

def readUInt64(handle, pid, address) -> int | None:
    """读取 8 字节无符号整数 (uint64_t)"""
    buf = ctypes.c_uint64()
    status, _ = readWriteMemory(handle, pid, address, 8, ctypes.addressof(buf), 0)
    return buf.value if status == 0 else None

def readInt64(handle, pid, address) -> int | None:
    """读取 8 字节有符号整数 (int64_t)"""
    buf = ctypes.c_int64()
    status, _ = readWriteMemory(handle, pid, address, 8, ctypes.addressof(buf), 0)
    return buf.value if status == 0 else None

def readFloat(handle, pid, address) -> float | None:
    """读取 4 字节浮点数 (float)"""
    buf = ctypes.c_float()
    status, _ = readWriteMemory(handle, pid, address, 4, ctypes.addressof(buf), 0)
    return buf.value if status == 0 else None

def readDouble(handle, pid, address) -> float | None:
    """读取 8 字节双精度浮点数 (double)"""
    buf = ctypes.c_double()
    status, _ = readWriteMemory(handle, pid, address, 8, ctypes.addressof(buf), 0)
    return buf.value if status == 0 else None

def readBytes(handle, pid, address, size) -> bytes | None:
    """读取指定长度的字节序列，返回 (status, bytes)"""
    buf = ctypes.create_string_buffer(size)
    status, _ = readWriteMemory(handle, pid, address, size, ctypes.addressof(buf), 0)
    return buf.raw if status == 0 else None

def readString(handle, pid, address, size, encoding='ascii') -> str | None:
    """
    读取指定长度的字节序列并解码为字符串（按指定编码，默认 ASCII）。
    若想读取以 null 结尾的字符串，可传递 size 为最大长度（如 256），
    解码时用 split('\x00', 1)[0] 截断。
    """
    status, data = readBytes(handle, pid, address, size)
    if status != 0:
        return None
    try:
        # 寻找第一个 null 字节，若存在则截断
        null_pos = data.find(b'\x00')
        if null_pos != -1:
            data = data[:null_pos]
        return data.decode(encoding)
    except UnicodeDecodeError:
        # TODO 可能有问题
        return data.decode(encoding, errors='replace') or None


def readFloatVector(handle, pid, address) -> list[float] | None:
    """从目标进程读取 count 个 float (4字节)，返回 (status, list)"""
    size = 12
    buf = ctypes.create_string_buffer(size)
    status, _ = readWriteMemory(handle, pid, address, size, ctypes.addressof(buf), 0)
    if status != 0:
        return None
    floats = array('f')
    floats.frombytes(buf.raw)
    return floats.tolist()

def readDoubleVector(handle, pid, address) -> list[float] | None:
    """从目标进程读取 count 个 double (8字节)，返回 (status, list)"""
    size = 24
    buf = ctypes.create_string_buffer(size)
    status, _ = readWriteMemory(handle, pid, address, size, ctypes.addressof(buf), 0)
    if status != 0:
        return None
    doubles = array('d')
    doubles.frombytes(buf.raw)
    return doubles.tolist()

# ---------- 示例用法 ----------
if __name__ == "__main__":
    try:
        # 打开设备
        h = openDevice()
        print("[+] 设备打开成功")

        status, pid = getPidByName(h, "hl.exe")
        if status == 0 and pid == 0:
            print(f"[-] 获取 PID 失败，状态 {status}")
        else:
            print(f"[+] hl.exe PID = {pid}")

        status, base = getModuleBase(h, pid, "client.dll")
        if status == 0:
            print(f"[+] 模块基址 = 0x{base:X}")

        closeDevice(h)
    except Exception as e:
        print(f"[-] 错误: {e}")
        sys.exit(1)