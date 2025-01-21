import sys
import cv2
import mediapipe as mp
import numpy as np
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QTableWidget, QTableWidgetItem, QDialog
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
from cloudant.client import Cloudant

# IBM Cloudant Credentials
CLOUDANT_APIKEY = "1rpqBTTNMtHahbpAK-FGrxe6qtsgVhjJZrZbyIA7PFSr"
CLOUDANT_URL = "https://19a338cf-2062-4f63-8540-a2da4e5740a7-bluemix.cloudantnosqldb.appdomain.cloud"
DB_NAME = "exercise_data"

# Initialize Cloudant Client
client = Cloudant.iam(None, CLOUDANT_APIKEY, url=CLOUDANT_URL, connect=True)
if DB_NAME not in client.all_dbs():
    db = client.create_database(DB_NAME)
else:
    db = client[DB_NAME]

# Pose Detection Setup
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

# Global Variables
tilt_count = 0
reward = 0
last_tilt = None
neutral_maintained = True
tilt_history = []


class NeckTiltApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neck Tilt Exercise")
        self.setGeometry(100, 100, 800, 400)

        # UI Components
        self.video_label = QLabel(self)
        self.video_label.setFixedSize(400, 300)

        self.count_label = QLabel(f"Tilts: {tilt_count} | Reward: {reward}", self)
        self.count_label.setStyleSheet("font-size: 16px; margin: 5px;")

        self.start_button = QPushButton("Start Exercise", self)
        self.start_button.setStyleSheet("padding: 5px; font-size: 14px; background-color: #5cb85c; color: white;")
        self.start_button.clicked.connect(self.start_exercise)

        self.end_button = QPushButton("End Exercise", self)
        self.end_button.setStyleSheet("padding: 5px; font-size: 14px; background-color: #d9534f; color: white;")
        self.end_button.clicked.connect(self.end_exercise)

        self.history_button = QPushButton("View History", self)
        self.history_button.setStyleSheet("padding: 5px; font-size: 14px; background-color: #0275d8; color: white;")
        self.history_button.clicked.connect(self.view_history)

        # Layout
        control_layout = QVBoxLayout()
        control_layout.addWidget(self.video_label)
        control_layout.addWidget(self.count_label)
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.end_button)
        control_layout.addWidget(self.history_button)

        self.setLayout(control_layout)

        # Timer for Video Capture
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        # OpenCV Video Capture
        self.cap = cv2.VideoCapture(0)

    def start_exercise(self):
        global tilt_count, reward, last_tilt, neutral_maintained, tilt_history
        tilt_count = 0
        reward = 0
        last_tilt = None
        neutral_maintained = True
        tilt_history = []
        self.timer.start(30)

    def end_exercise(self):
        self.timer.stop()
        self.cap.release()
        cv2.destroyAllWindows()
        self.send_to_cloud("neck_tilt", tilt_count, reward)
        self.count_label.setText(f"Final Tilts: {tilt_count} | Final Reward: {reward}")

    def update_frame(self):
        global tilt_count, reward, last_tilt, neutral_maintained, tilt_history

        ret, frame = self.cap.read()
        if not ret or frame is None:
            print("Warning: Empty frame from webcam.")
            return

        frame = cv2.flip(frame, 1)
        height, width, _ = frame.shape

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_frame)

        feedback = "Neutral position. Tilt your head left or right."

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2, circle_radius=2),
            )

            try:
                left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
                right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

                tilt_angle = np.arctan2(
                    right_shoulder.y - left_shoulder.y, right_shoulder.x - left_shoulder.x
                )
                tilt_angle_deg = np.degrees(tilt_angle)

                tilt_history.append(tilt_angle_deg)
                if len(tilt_history) > 10:
                    tilt_history.pop(0)
                smooth_tilt = np.mean(tilt_history)

                if smooth_tilt > 15:
                    if last_tilt != "right" and neutral_maintained:
                        tilt_count += 1
                        reward += 10
                        last_tilt = "right"
                        neutral_maintained = False
                        feedback = "Good! Tilted to the right."
                elif smooth_tilt < -15:
                    if last_tilt != "left" and neutral_maintained:
                        tilt_count += 1
                        reward += 10
                        last_tilt = "left"
                        neutral_maintained = False
                        feedback = "Good! Tilted to the left."
                elif -10 <= smooth_tilt <= 10:
                    neutral_maintained = True
                    last_tilt = None

            except Exception as e:
                feedback = "Error in pose detection. Adjust your position."

        self.count_label.setText(f"Tilts: {tilt_count} | Reward: {reward}")

        cv2.putText(frame, feedback, (20, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1, cv2.LINE_AA)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        qimage = QImage(rgb_frame.data, rgb_frame.shape[1], rgb_frame.shape[0], QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qimage))

    def send_to_cloud(self, exercise_name, count, reward):
        exercise_data = {
            "exercise": exercise_name,
            "counter": count,
            "reward": reward,
            "timestamp": datetime.now().isoformat()
        }
        try:
            db.create_document(exercise_data)
            print("Data sent to Cloudant:", exercise_data)
        except Exception as e:
            print("Error sending data to Cloudant:", e)

    def view_history(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Exercise History")
        dialog.resize(600, 400)

        table = QTableWidget(dialog)
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Exercise", "Counter", "Reward", "Timestamp"])
        table.setGeometry(10, 10, 580, 380)

        documents = list(db)
        table.setRowCount(len(documents))

        for i, doc in enumerate(documents):
            table.setItem(i, 0, QTableWidgetItem(doc.get("exercise", "")))
            table.setItem(i, 1, QTableWidgetItem(str(doc.get("counter", 0))))
            table.setItem(i, 2, QTableWidgetItem(str(doc.get("reward", 0))))
            table.setItem(i, 3, QTableWidgetItem(doc.get("timestamp", "")))

        dialog.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NeckTiltApp()
    window.show()
    sys.exit(app.exec_())
