import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QBrush, QColor, QIcon
import winsound  # For sound effect
import subprocess

class CircularWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set window properties
        self.setWindowTitle("Circular Window")
        self.setGeometry(0, 0, 80, 80)  # Small circular window size
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # Center the window in the bottom-right corner
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.width() - 120, screen.height() - 100)  # Adjusted offset slightly to the left

        # Create a button for interaction
        central_widget = QWidget()
        layout = QVBoxLayout()

        button = QPushButton()
        button.setIcon(QIcon("fitness_icon.png"))  # Replace with the path to your fitness icon
        button.setIconSize(button.size())  # Icon size should fit the button
        button.setFixedSize(80, 80)  # Ensure button size matches the circle
        button.setStyleSheet(
            "QPushButton {"
            # "background-color: #32CD32;"  # Green background color
            "border: none;"
            "border-radius: 50px;"  # Circular shape
            "padding: 0px;"  # Remove padding for better icon fit
            "}"
            "QPushButton:pressed {"
            "background-color: #006400;"
            "}"
        )

        button.clicked.connect(self.run_relaxify)

        layout.addWidget(button)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        layout.setAlignment(Qt.AlignCenter)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Timer for the popup
        self.timer = QTimer()
        self.timer.timeout.connect(self.show_popup)
        self.timer.start(60000)  # Trigger every 1 minute

    def paintEvent(self, event):
        # Make the window circular
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor("#32CD32")))  # Green color for the circle
        painter.setPen(Qt.NoPen)
        rect = self.rect()
        painter.drawEllipse(rect)

    def run_relaxify(self):
        # Run the Relaxify script
        try:
            subprocess.Popen([sys.executable, "relaxify.py"])
        except Exception as e:
            print(f"Error running Relaxify: {e}")

    def show_popup(self):
        # Play sound effect synchronously
        try:
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)  # Play a system sound asynchronously
        except Exception as e:
            print(f"Error playing sound: {e}")

        self.popup = QMainWindow()
        self.popup.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.popup.setAttribute(Qt.WA_TranslucentBackground, True)
        screen = QApplication.primaryScreen().availableGeometry()
        popup_width, popup_height = 250, 100

        # Shift popup slightly to the right and down from the top-left
        self.popup.setGeometry(self.x() - popup_width + 120, self.y() - popup_height + 35, popup_width, popup_height)

        central_widget = QWidget()
        layout = QVBoxLayout()

        message_label = QLabel("<b>Time to take a break!<br>Let's do some exercises.</b>")
        message_label.setStyleSheet("font-size: 14px; color: #FFFFFF; background-color: #4682B4; padding: 8px; border-radius: 8px;")
        message_label.setAlignment(Qt.AlignCenter)

        close_button = QPushButton("X")
        close_button.setStyleSheet(
            "QPushButton {"
            "background-color: #FF6347;"  # Red color for close button
            "color: white;"
            "border: none;"
            "border-radius: 10px;"
            "font-weight: bold;"
            "font-size: 12px;"
            "padding: 2px;"
            "}"
            "QPushButton:hover {"
            "background-color: #FF4500;"
            "}"
        )
        close_button.setFixedSize(20, 20)
        close_button.clicked.connect(self.popup.close)

        layout.addWidget(message_label)
        layout.addWidget(close_button, alignment=Qt.AlignRight)
        layout.setContentsMargins(10, 10, 10, 10)

        central_widget.setLayout(layout)
        self.popup.setCentralWidget(central_widget)
        self.popup.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = CircularWindow()
    window.show()

    sys.exit(app.exec_())