import os
import sys
sys.path.append('/usr/local/bin')  # Add the directory to sys.path

from picamera2 import Picamera2
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QDateTime
from styles import stylesheet  # uncomment if you have a stylesheet module

class DesktopFileCreator(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(stylesheet)  # uncomment if you have a stylesheet
        self.initUI()
        self.process = None  # Initialize QProcess instance

    def initUI(self):
        self.setWindowTitle('MultiCam')
        self.setWindowIcon(QIcon('MultiCam.png'))  
        self.setGeometry(200, 50, 400, 250)

        layout = QVBoxLayout(self)
        self.take_picture_button = QPushButton('Take Picture', self)
        self.take_picture_button.clicked.connect(self.take_picture)
        layout.addWidget(self.take_picture_button)
        self.setLayout(layout)

    def take_picture(self):

        # Example: Capture pictures from 3 cameras
        for i in range(3):
            try:
                picam = Picamera2(i)  # create PiCamera instance
                picam.start()
                timestamp = QDateTime.currentDateTime().toString("yyyyMMdd-hhmmss")
                filename = f'cam{i}_{timestamp}.jpg'  # Unique filename based on timestamp
                picam.capture_file(filename)
                picam.stop()
                print(f"Picture taken from camera {i} saved as {filename}")
            except Exception as e:
                print(f"Error capturing picture from camera {i}: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DesktopFileCreator()
    window.show()
    sys.exit(app.exec_())

