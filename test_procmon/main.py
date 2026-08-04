# 截图当前窗口并随机放在某个目录下

import os
import uuid
import win32gui
from PIL import ImageGrab

def capture_active_window():
    """截取当前活动窗口并保存到随机目录"""
    # 1. 获取活动窗口句柄
    hwnd = win32gui.GetForegroundWindow()
    if hwnd == 0:
        print("没有活动窗口")
        return

    # 2. 获取窗口位置
    rect = win32gui.GetWindowRect(hwnd)
    left, top, right, bottom = rect
    # 确保窗口可见（非最小化）
    if win32gui.IsIconic(hwnd):
        print("窗口被最小化，请恢复后再试")
        return

    # 3. 截图
    bbox = (left, top, right, bottom)
    img = ImageGrab.grab(bbox)

    # 4. 生成随机目录名
    rand_dir = str(uuid.uuid4())
    os.makedirs(rand_dir, exist_ok=True)

    # 5. 保存图片
    file_path = os.path.join(rand_dir, "screenshot.png")
    img.save(file_path, "PNG")

if __name__ == "__main__":
    capture_active_window()