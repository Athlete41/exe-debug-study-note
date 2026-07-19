from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, Signal

class TitleBar(QWidget):
    close_signal = Signal()
    minimize_signal = Signal()
    STYLE = """
        QWidget {
            background-color: rgba(30, 30, 30, 180);
            border-top-left-radius: 15px;
            border-top-right-radius: 15px;
        }
        QPushButton {
            background: transparent;
            color: white;
            border: none;
            font-size: 20px;
        }
        QPushButton:hover {
            border-radius: 5px;
        }
        QPushButton#minBtn:hover {
            background-color: rgba(255, 255, 255, 50);
        }
        QPushButton#closeBtn:hover {
            background-color: rgba(255, 80, 80, 150);
        }
    """

    def __init__(self, parent=None, title="自定义标题栏"):
        super().__init__(parent)
        self.parent_window = parent
        self.drag_pos = None
        self.setFixedHeight(40)
        self.setStyleSheet(self.STYLE)          # 应用类样式

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)

        self.title_label = QLabel(title, self)
        self.title_label.setStyleSheet("color: white; font-size: 16px;")
        layout.addWidget(self.title_label)
        layout.addStretch()

        self.min_btn = QPushButton("—", self, objectName="minBtn")
        self.min_btn.setFixedSize(30, 30)
        self.min_btn.clicked.connect(self.minimize_signal.emit)
        layout.addWidget(self.min_btn)

        self.close_btn = QPushButton("✕", self, objectName="closeBtn")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self.close_signal.emit)
        layout.addWidget(self.close_btn)

    def setTitle(self, title):
        self.title_label.setText(title)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos is not None:
            delta = event.globalPosition().toPoint() - self.drag_pos
            if self.parent_window:
                self.parent_window.move(self.parent_window.pos() + delta)
            self.drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = None