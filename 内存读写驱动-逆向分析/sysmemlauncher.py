"""
Cracker.sys 驱动加载/卸载工具（服务方式）
通过注册表将驱动注册为系统服务，实现加载和卸载。
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
SERVICE_NAME = "Cracker"          # 服务名称（注册表项名）
SERVICE_DISPLAY_NAME = "Cracker Driver Service"
SERVICE_DESCRIPTION = "Cracker 内核驱动服务"

# 驱动文件路径（请修改为实际路径）
# 建议将 Cracker.sys 放在脚本同目录下，或使用绝对路径
DRIVER_PATH = os.path.join(os.path.dirname(__file__), "Cracker.sys")


def isAdmin():
    """检查当前进程是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False


def installDriver():
    """安装并启动驱动服务"""
    # 1. 检查驱动文件是否存在
    if not os.path.exists(DRIVER_PATH):
        print(f"[-] 驱动文件不存在: {DRIVER_PATH}")
        return False

    # 2. 检查服务是否已存在
    try:
        win32serviceutil.QueryServiceStatus(SERVICE_NAME)
        print(f"[!] 服务 {SERVICE_NAME} 已存在，请先卸载再安装")
        return False
    except win32api.error as e:
        if e.winerror != winerror.ERROR_SERVICE_DOES_NOT_EXIST:
            print(f"[-] 检查服务状态失败: {e}")
            return False

    # 3. 安装服务（适配新版本 InstallService 签名）
    try:
        print(f"[+] 正在安装服务 {SERVICE_NAME} ...")
        win32serviceutil.InstallService(
            pythonClassString=None,               # 对于内核驱动，无需 Python 类
            serviceName=SERVICE_NAME,
            displayName=SERVICE_DISPLAY_NAME,
            startType=win32service.SERVICE_DEMAND_START,  # 手动启动
            exeName=DRIVER_PATH,                  # 驱动文件路径
            description=SERVICE_DESCRIPTION,
            # 其他参数保持默认（errorControl 等）
        )
        print(f"[+] 服务 {SERVICE_NAME} 安装成功")
    except Exception as e:
        print(f"[-] 安装服务失败: {e}")
        return False

    # 4. 启动服务
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
    """停止并卸载驱动服务"""
    try:
        win32serviceutil.QueryServiceStatus(SERVICE_NAME)
    except win32api.error as e:
        if e.winerror == winerror.ERROR_SERVICE_DOES_NOT_EXIST:
            print(f"[!] 服务 {SERVICE_NAME} 不存在，无需卸载")
            return True
        else:
            print(f"[-] 检查服务状态失败: {e}")
            return False

    # 停止服务
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

    # 卸载服务
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
        print("支持的操作: install, uninstall")
        sys.exit(1)


if __name__ == "__main__":
    main()