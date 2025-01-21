import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush
from neck_tilt import NeckTiltApp
from head_movement import HeadMovementApp

class RoundedMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set main window properties
        self.setWindowTitle("Relaxify - Your Exercise Companion")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: #f0f8ff; border-radius: 15px;")

        # Central widget and layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Header text
        header_label = QLabel("Welcome to Relaxify")
        header_label.setFont(QFont("Arial", 24, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("color: #2e8b57;")
        layout.addWidget(header_label)

        subheader_label = QLabel("Choose an exercise to get started")
        subheader_label.setFont(QFont("Arial", 16))
        subheader_label.setAlignment(Qt.AlignCenter)
        subheader_label.setStyleSheet("color: #555;")
        layout.addWidget(subheader_label)

        # Buttons for exercises
        neck_tilt_button = QPushButton("Neck Tilt Exercise")
        neck_tilt_button.setFont(QFont("Arial", 14))
        neck_tilt_button.setStyleSheet(self.button_style())
        neck_tilt_button.clicked.connect(self.open_neck_tilt)

        head_movement_button = QPushButton("Head Movement Exercise")
        head_movement_button.setFont(QFont("Arial", 14))
        head_movement_button.setStyleSheet(self.button_style())
        head_movement_button.clicked.connect(self.open_head_movement)

        layout.addWidget(neck_tilt_button)
        layout.addWidget(head_movement_button)

        central_widget.setLayout(layout)

    def button_style(self):
        return (
            "QPushButton {"
            "background-color: #4682b4;"
            "color: white;"
            "border: none;"
            "border-radius: 10px;"
            "padding: 10px 20px;"
            "margin: 10px;"
            "font-weight: bold;"
            "}"
            "QPushButton:hover {"
            "background-color: #5a9bd3;"
            "}"
            "QPushButton:pressed {"
            "background-color: #336d92;"
            "}"
        )

    def open_neck_tilt(self):
        self.neck_tilt_window = NeckTiltApp()
        self.neck_tilt_window.show()
        self.close()

    def open_head_movement(self):
        self.head_movement_window = HeadMovementApp()
        self.head_movement_window.show()
        self.close()

    def paintEvent(self, event):
        # Add rounded edges with a custom painter
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor("#f0f8ff")))
        painter.setPen(Qt.NoPen)
        rect = self.rect()
        rect.setWidth(rect.width() - 1)
        rect.setHeight(rect.height() - 1)
        painter.drawRoundedRect(rect, 15, 15)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = RoundedMainWindow()
    window.show()

    sys.exit(app.exec_())