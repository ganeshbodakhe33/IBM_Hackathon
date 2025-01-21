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
head_movement_count = 0
reward = 0
last_movement = None  # Track the last head movement direction
neutral_maintained = True  # Check if neutral position is maintained
movement_history = []


class HeadMovementApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Head Movement Exercise")
        self.setGeometry(100, 100, 800, 400)

        # UI Components
        self.video_label = QLabel(self)
        self.video_label.setFixedSize(400, 300)

        self.count_label = QLabel(f"Movements: {head_movement_count} | Reward: {reward}", self)
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
        global head_movement_count, reward, last_movement, neutral_maintained, movement_history
        head_movement_count = 0
        reward = 0
        last_movement = None
        neutral_maintained = True
        movement_history = []
        self.timer.start(30)

    def end_exercise(self):
        self.timer.stop()
        self.cap.release()
        cv2.destroyAllWindows()
        self.send_to_cloud("head_movement", head_movement_count, reward)
        self.count_label.setText(f"Final Movements: {head_movement_count} | Final Reward: {reward}")

    def update_frame(self):
        global head_movement_count, reward, last_movement, neutral_maintained, movement_history

        ret, frame = self.cap.read()
        if not ret or frame is None:
            print("Warning: Empty frame from webcam.")
            return

        frame = cv2.flip(frame, 1)
        height, width, _ = frame.shape

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_frame)

        feedback = "Neutral position. Move your head left or right."

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
                nose = landmarks[mp_pose.PoseLandmark.NOSE.value]
                left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
                right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

                movement_angle = np.arctan2(
                    nose.x - (left_shoulder.x + right_shoulder.x) / 2,
                    nose.y - (left_shoulder.y + right_shoulder.y) / 2
                )
                movement_angle_deg = np.degrees(movement_angle)

                movement_history.append(movement_angle_deg)
                if len(movement_history) > 10:
                    movement_history.pop(0)
                smooth_movement = np.mean(movement_history)

                if smooth_movement > 15:
                    if last_movement != "right" and neutral_maintained:
                        head_movement_count += 1
                        reward += 10
                        last_movement = "right"
                        neutral_maintained = False
                        feedback = "Good! Moved to the right."
                elif smooth_movement < -15:
                    if last_movement != "left" and neutral_maintained:
                        head_movement_count += 1
                        reward += 10
                        last_movement = "left"
                        neutral_maintained = False
                        feedback = "Good! Moved to the left."
                elif -10 <= smooth_movement <= 10:
                    neutral_maintained = True
                    last_movement = None

            except Exception as e:
                feedback = "Error in pose detection. Adjust your position."

        self.count_label.setText(f"Movements: {head_movement_count} | Reward: {reward}")

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
    window = HeadMovementApp()
    window.show()
    sys.exit(app.exec_())
