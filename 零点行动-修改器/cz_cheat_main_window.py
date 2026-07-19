import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QFrame
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QShortcut, QKeySequence
import math

import cz_mem_module
from title_bar import TitleBar

from canvas3d import Numpy3DCanvas, EntityPoint3D
from radar import RadarCanvas, RadarEntity



class CZCheatMainWindow(QWidget):
    STYLE_CONTENT = """
        QFrame {
            background-color: rgba(0, 0, 0, 60);
            border-bottom-left-radius: 15px;
            border-bottom-right-radius: 15px;
        }
    """

    TITLE = "零点行动-作弊"
    RANGE = 2000.0
    FILTER_RANGE = 500.0
    FPS = 30.0
    FOV = 90.0
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(0, 0, 500, 500)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)

        self.title_bar = TitleBar(self, title=self.TITLE)
        self.title_bar.close_signal.connect(self.close)
        self.title_bar.minimize_signal.connect(self.showMinimized)
        main_layout.addWidget(self.title_bar)

        self.content_frame = QFrame(self)
        self.content_frame.setStyleSheet(self.STYLE_CONTENT)
        self.content_layout = QVBoxLayout(self.content_frame)
        main_layout.addWidget(self.content_frame)

        # 3D canvas
        self.canvas3D = Numpy3DCanvas(self.content_frame)
        self.canvas3D.addPointEntity(EntityPoint3D(id=1, name="point", pos=(-1400, -1000, -100), color="red"))
        self.canvas3D.setProjection(self.FOV, 0.1, 1000.0)
        self.content_layout.addWidget(self.canvas3D)

        # Radar canvas
        self.radar = RadarCanvas(self.content_frame)
        self.radar.setRadarRadius(self.RANGE)
        self.content_layout.addWidget(self.radar)

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

    def timerTask(self):
        if cz_mem_module.PM is None:
            return
        try:
            camPos, camAng = cz_mem_module.Player.get_pos(), cz_mem_module.Player.get_ang()

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
                        self.radar.addTempEntity(RadarEntity(entId, entName, entPos, yaw=entAng[1]))
            
            # 触发雷达渲染
            self.radar.update() 
        except Exception:
            pass



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CZCheatMainWindow()
    window.show()
    sys.exit(app.exec())