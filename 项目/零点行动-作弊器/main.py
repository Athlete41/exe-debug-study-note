import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QFrame
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtGui import QGuiApplication
import math
import win32gui
import win32con
import keyboard

import cz_mem_module
from qt6_canvas3d import Qt6Numpy3DCanvas, Point3D, Text3D
from qt6_radar import Qt6RadarCanvas, RadarEntity



class CZCheatMainWindow(QWidget):
    RANGE = 2000.0
    FILTER_RANGE = 500.0
    FPS = 30.0
    FOV = 90.0
    Z_NEAR = 0.1
    Z_FAR = 10000.0
    SLIENT = False
    WINDOW_WIDTH = 1600
    WINDOW_HEIGHT = 900
    
    def setup_overlay(self):
        # 1. 设置窗口属性：无边框、置顶、Tool（不抢焦点）
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )

        # 2. 启用真正的透明背景（关键！）
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # 3. 取消颜色键设置（不再需要）
        # 不需要 setStyleSheet，不需要 SetLayeredWindowAttributes

        hwnd = int(self.winId())
        # 4. 依然需要鼠标穿透（WS_EX_TRANSPARENT）
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        ex_style |= win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

        # 5. 置顶
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
        

    
    def __init__(self):
        super().__init__()
        self.setup_overlay()

        screen = QGuiApplication.primaryScreen()
        logical_size = screen.size()
        self.setGeometry(
            logical_size.width() // 2 - self.WINDOW_WIDTH // 2, 
            logical_size.height() // 2 - self.WINDOW_HEIGHT // 2, 
            self.WINDOW_WIDTH, 
            self.WINDOW_HEIGHT
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)

        self.content_frame = QFrame(self)
        self.content_layout = QVBoxLayout(self.content_frame)
        main_layout.addWidget(self.content_frame)

        # 3D canvas
        self.canvas3D = Qt6Numpy3DCanvas(self.content_frame)
        self.canvas3D.setScreen(self.FOV, self.Z_NEAR, self.Z_FAR)
        self.content_layout.addWidget(self.canvas3D)

        # Radar canvas
        self.radar = Qt6RadarCanvas(self.content_frame)
        self.radar.setRadarRadius(self.RANGE)
        self.radar.setGeometry(0, 0, 200, 100)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.timerTask)
        self.timer.start(1000 // self.FPS)

        self.timer2 = QTimer(self)
        self.timer2.timeout.connect(self.timer2Task)
        self.timer2.start(1000)
        self.timer2Task()


        insert_filter_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        insert_filter_shortcut.activated.connect(self.insertFilter)

        clear_filter_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        clear_filter_shortcut.activated.connect(self.clearFilter)

        self.filter = {}

    def insertFilter(self):
        for i in range(1, 20, 1):
            plyPos = cz_mem_module.Player.get_pos()
            entPos = cz_mem_module.RobotList.get_pos(i)
            if entPos is not None and plyPos is not None:
                dist = math.sqrt((entPos[0] - plyPos[0])**2 + (entPos[1] - plyPos[1])**2 + (entPos[2] - plyPos[2])**2)
                if dist < self.FILTER_RANGE:
                    self.filter[i] = True

    def clearFilter(self):
        self.filter.clear()

    def timer2Task(self):
        if cz_mem_module.PM is None:
            cz_mem_module.find_pm()

    def keyCheck(self):
        if keyboard.is_pressed("Ctrl+F"):
            self.insertFilter()
        if keyboard.is_pressed("Ctrl+C"):
            self.clearFilter()

    def timerTask(self):
        self.keyCheck()

        if cz_mem_module.PM is None:
            return
        
        try:
            camPos, camAng = cz_mem_module.Player.get_pos(), cz_mem_module.Player.get_ang()


            # 雷达渲染
            if camPos is not None:
                self.radar.setCenterPos(camPos)
            if camAng is not None:
                self.radar.setCenterYaw(camAng[1])

            for i in range(1, 20, 1):
                if i in self.filter:
                    continue

                entHealth, entPos, entAng = cz_mem_module.RobotList.get_health(i), cz_mem_module.RobotList.get_pos(i), cz_mem_module.RobotList.get_ang(i)
                entId = f"Robot-{i}"
                entName = f"{entHealth}"
                if entPos is not None and entAng is not None and entHealth is not None:
                    if entHealth > 1:
                        self.radar.addEntity(entId, RadarEntity(entName, entPos, yaw=entAng[1]))
            
            self.radar.update() 
            
            # 3D渲染
            fov = cz_mem_module.Player.get_fov()
            if fov is not None:
                self.canvas3D.setScreen(fov, self.Z_NEAR, self.Z_FAR)
                
            if camPos is not None and camAng is not None:
                # pitch yaw roll -> roll pitch yaw
                self.canvas3D.setCamPosAng(camPos, [camAng[2], camAng[0], camAng[1]])
   
            for i in range(1, 20, 1):
                if i in self.filter:
                    continue

                entHealth, entPos, entAng = cz_mem_module.RobotList.get_health(i), cz_mem_module.RobotList.get_pos(i), cz_mem_module.RobotList.get_ang(i)
                entId = f"Robot-{i}"
                entName = f"{entHealth}"
                if entPos is not None and entAng is not None and entHealth is not None:
                    if entHealth > 1:
                        self.canvas3D.addPoint3D(entId, Point3D(entPos, 5000))
                        self.canvas3D.addText3D(entId, Text3D(entPos, f"{entHealth}"))

            self.canvas3D.update()
        except Exception as e:
            if not self.SLIENT:
                print(e)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CZCheatMainWindow()
    window.show()
    sys.exit(app.exec())




