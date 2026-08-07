import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QFrame
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication

import win32gui
import win32con


import css_mem_module
from qt6_canvas3d import Qt6Numpy3DCanvas, Point3D, Text3D
from qt6_radar import Qt6RadarCanvas, RadarEntity



class CSSCheatMainWindow(QWidget):
    FPS = 30.0

    RADAR_RANGE = 2000.0

    Z_NEAR = 0.1
    Z_FAR = 10000.0

    BOT_MAX = 32

    SLIENT = False
    WINDOW_WIDTH = 1600
    WINDOW_HEIGHT = 900

    PLAYER_NAME = "装唐阴他一手"
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
        css_mem_module.Init()

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
        self.canvas3D.setScreen(90.0, self.Z_NEAR, self.Z_FAR)
        self.content_layout.addWidget(self.canvas3D)

        # Radar canvas
        self.radar = Qt6RadarCanvas(self.content_frame)
        self.radar.setRadarRadius(self.RADAR_RANGE)
        self.radar.setGeometry(0, 0, 200, 100)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.timerTask)
        self.timer.start(1000 // self.FPS)


    def timerTask(self):
   
        try:
            playerInfo = None
            botList = []
            for i in range(self.BOT_MAX):
                botInfo = css_mem_module.BotInfo.getData(i)
                if botInfo is None:
                    continue

                botName = botInfo["Name"]
                if botName is None:
                    continue

                botTeamType = botInfo["TeamType"]
                if botTeamType is None or botTeamType == "观察者" or botTeamType == "未知":
                    continue 

                if botName == self.PLAYER_NAME:
                    playerInfo = botInfo
                    continue
    
                botList.append((i, botInfo))

  
            if playerInfo is None:
                return
            
            # 雷达渲染
            camPos, camAng = playerInfo["Pos"], playerInfo["Ang"]

            if camPos is not None:
                self.radar.setCenterPos(camPos)
            if camAng is not None:
                self.radar.setCenterYaw(camAng[1])


            for i, botInfo in botList:
                botHealth, botPos, botAng = botInfo["Health"], botInfo["Pos"], botInfo["Ang"]
                botTeamType = botInfo["TeamType"]
                botId = f"Robot-{i}"
                text = f"{botHealth}"
                if botPos is not None and botAng is not None and botHealth is not None:
                    if botHealth > 1:
                        color = Qt.green if botTeamType == playerInfo["TeamType"] else Qt.red
                        self.radar.addEntity(botId, RadarEntity(text, botPos, yaw=botAng[1], color=color))
            
            self.radar.update() 
            
            # 3D渲染
            fov = css_mem_module.FOVGetter.getData()
            if fov is not None:
                self.canvas3D.setScreen(fov, self.Z_NEAR, self.Z_FAR)
                
            if camPos is not None and camAng is not None:
                # pitch yaw roll -> roll pitch yaw
                self.canvas3D.setCamPosAng(camPos, [camAng[2], camAng[0], camAng[1]])
   
            for i, botInfo in botList:
                botHealth, botPos, botAng = botInfo["Health"], botInfo["Pos"], botInfo["Ang"]
                botTeamType = botInfo["TeamType"]
                botId = f"Robot-{i}"
                text = f"{botHealth}"
                if botPos is not None and botAng is not None and botHealth is not None:
                    if botHealth > 1:
                        color = Qt.green if botTeamType == playerInfo["TeamType"] else Qt.red
                        self.canvas3D.addPoint3D(botId, Point3D(botPos, 5000, color=color))
                        self.canvas3D.addText3D(botId, Text3D(botPos, text, color=color))

            self.canvas3D.update()
        except Exception as e:
            if not self.SLIENT:
                print(e)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CSSCheatMainWindow()
    window.show()
    sys.exit(app.exec())




