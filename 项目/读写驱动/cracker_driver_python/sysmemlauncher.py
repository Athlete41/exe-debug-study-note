"""
Cracker.sys 驱动加载/卸载工具（服务方式）
使用 CreateService 直接创建内核驱动服务，避免 InstallService 硬编码 Win32 类型。
需要管理员权限运行。
"""
import os
import sys
import ctypes
import win32serviceutil
import win32service
import win32api
import winerror

# ---------- 配置 ----------
SERVICE_NAME = "Cracker"
SERVICE_DISPLAY_NAME = "Cracker Driver Service"
SERVICE_DESCRIPTION = "Cracker 内核驱动服务"
DRIVER_PATH = os.path.join(os.path.dirname(__file__), "cracker.sys")


def isAdmin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False


def installDriver():
    """使用 CreateService 创建内核驱动服务并启动"""
    if not os.path.exists(DRIVER_PATH):
        print(f"[-] 驱动文件不存在: {DRIVER_PATH}")
        return False

    # 检查服务是否已存在
    try:
        win32serviceutil.QueryServiceStatus(SERVICE_NAME)
        print(f"[!] 服务 {SERVICE_NAME} 已存在，请先卸载")
        return False
    except win32api.error as e:
        if e.winerror != winerror.ERROR_SERVICE_DOES_NOT_EXIST:
            print(f"[-] 检查服务状态失败: {e}")
            return False

    # 打开服务管理器
    try:
        hScm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
    except win32api.error as e:
        print(f"[-] 打开服务管理器失败: {e}")
        return False

    # 创建服务（直接指定 SERVICE_KERNEL_DRIVER）
    try:
        print(f"[+] 正在创建服务 {SERVICE_NAME} ...")
        # 参数顺序依据 pywin32 312 的 CreateService 签名
        hService = win32service.CreateService(
            hScm,                              # SC_HANDLE
            SERVICE_NAME,                      # 服务名
            SERVICE_DISPLAY_NAME,              # 显示名
            win32service.SERVICE_ALL_ACCESS,   # 访问权限
            win32service.SERVICE_KERNEL_DRIVER,  # 【关键】服务类型 = 1
            win32service.SERVICE_DEMAND_START, # 启动类型：手动
            win32service.SERVICE_ERROR_NORMAL, # 错误控制
            DRIVER_PATH,                       # 二进制路径
            None,                              # 加载顺序组
            False,                             # 是否获取标签
            None,                              # 依赖项
            None,                              # 账户名（本地系统）
            None                               # 密码
        )
        # 设置描述（可选）
        if SERVICE_DESCRIPTION:
            win32service.ChangeServiceConfig2(
                hService,
                win32service.SERVICE_CONFIG_DESCRIPTION,
                SERVICE_DESCRIPTION
            )
        win32service.CloseServiceHandle(hService)
        print(f"[+] 服务 {SERVICE_NAME} 创建成功（类型: KERNEL_DRIVER）")
    except win32api.error as e:
        if e.winerror == winerror.ERROR_SERVICE_EXISTS:
            print(f"[!] 服务 {SERVICE_NAME} 已存在，请先卸载")
        else:
            print(f"[-] 创建服务失败: {e}")
        return False
    finally:
        win32service.CloseServiceHandle(hScm)

    # 启动服务
    try:
        print(f"[+] 正在启动服务 {SERVICE_NAME} ...")
        win32serviceutil.StartService(SERVICE_NAME)
        print(f"[+] 服务 {SERVICE_NAME} 启动成功")
        return True
    except win32api.error as e:
        if e.winerror == winerror.ERROR_SERVICE_ALREADY_RUNNING:
            print(f"[!] 服务 {SERVICE_NAME} 已在运行")
            return True
        else:
            print(f"[-] 启动服务失败: {e}")
            return False


def uninstallDriver():
    """停止并卸载驱动服务（完全保持原样）"""
    try:
        win32serviceutil.QueryServiceStatus(SERVICE_NAME)
    except win32api.error as e:
        if e.winerror == winerror.ERROR_SERVICE_DOES_NOT_EXIST:
            print(f"[!] 服务 {SERVICE_NAME} 不存在，无需卸载")
            return True
        else:
            print(f"[-] 检查服务状态失败: {e}")
            return False

    try:
        print(f"[+] 正在停止服务 {SERVICE_NAME} ...")
        win32serviceutil.StopService(SERVICE_NAME)
        print(f"[+] 服务 {SERVICE_NAME} 已停止")
    except win32api.error as e:
        if e.winerror == winerror.ERROR_SERVICE_NOT_ACTIVE:
            print(f"[!] 服务 {SERVICE_NAME} 未运行")
        else:
            print(f"[-] 停止服务失败: {e}")
            return False

    try:
        print(f"[+] 正在卸载服务 {SERVICE_NAME} ...")
        win32serviceutil.RemoveService(SERVICE_NAME)
        print(f"[+] 服务 {SERVICE_NAME} 卸载成功")
        return True
    except Exception as e:
        print(f"[-] 卸载服务失败: {e}")
        return False


def main():
    if not isAdmin():
        print("[-] 请以管理员权限运行此脚本")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("用法:")
        print(f"  python {os.path.basename(__file__)} install    # 安装并启动驱动")
        print(f"  python {os.path.basename(__file__)} uninstall  # 停止并卸载驱动")
        sys.exit(1)

    action = sys.argv[1].lower()
    if action == "install":
        success = installDriver()
        sys.exit(0 if success else 1)
    elif action == "uninstall":
        success = uninstallDriver()
        sys.exit(0 if success else 1)
    else:
        print(f"[-] 未知操作: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()