import os
import sys
sys.path.append('/usr/local/bin')  # Add the directory to sys.path

from picamera2 import Picamera2  # Corrected import name
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QDateTime, QTimer
from styles import stylesheet  # uncomment if you have a stylesheet module

class DesktopFileCreator(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(stylesheet)  # uncomment if you have a stylesheet
        self.initUI()
        self.process = None  # Initialize QProcess instance
        self.picameras = []  # List to hold PiCamera2 instances

    def initUI(self):
        self.setWindowTitle('MultiCam')
        self.setWindowIcon(QIcon('multicam.png'))  
        self.setGeometry(200, 50, 400, 250)

        layout = QVBoxLayout(self)
        self.take_picture_button = QPushButton('Take Picture', self)
        self.take_picture_button.clicked.connect(self.take_picture)
        layout.addWidget(self.take_picture_button)

        # Label for status messages
        self.status_label = QLabel('Camera is ready', self)
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        
        # Define the directory to save images
        self.image_directory = '/home/sparky/multiimg'
        os.makedirs(self.image_directory, exist_ok=True)  # Create directory if it doesn't exist
        
    def take_picture(self):
        self.cleanup_cameras()  # Ensure any existing cameras are stopped before capturing new pictures
        timestamp = QDateTime.currentDateTime().toString("yyyyMMdd-hhmmss")

        success = True  # Flag to check if all pictures were taken successfully

        for i in range(3):
            try:
                picam = Picamera2(i)  # create PiCamera instance
                picam.start()
                self.picameras.append(picam)  # Add to list to manage instances
                filename = os.path.join(self.image_directory, f'cam{i}_{timestamp}.jpg')  # Unique filename based on timestamp
                picam.capture_file(filename)
                picam.stop()
                picam.close()
            except Exception as e:
                error_message = f"Error capturing picture from camera {i}: {str(e)}"
                self.status_label.setText(error_message)
                success = False
                break

        if success:
            self.status_label.setText("Pictures taken successfully")
        else:
            self.status_label.setText("Failed to take pictures")

        # Reset status label after 3 seconds
        QTimer.singleShot(3000, lambda: self.status_label.setText("Camera is ready"))

    def cleanup_cameras(self):
        for picam in self.picameras:
            try:
                picam.stop()
                picam.close()
            except Exception as e:
                print(f"Error stopping camera: {str(e)}")
        self.picameras.clear()  # Clear the list of cameras

    def closeEvent(self, event):
        self.cleanup_cameras()  # Ensure cameras are stopped when the application closes
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DesktopFileCreator()
    window.show()
    sys.exit(app.exec_())

