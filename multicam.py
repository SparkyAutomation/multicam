import os
import sys
sys.path.append('/usr/local/bin')  # Add the directory to sys.path

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtGui import QIcon, QImage, QPixmap
from PyQt5.QtCore import QTimer, QDateTime, QThread, pyqtSignal
import cv2

# Assuming these imports are corrected based on your environment
from picamera2 import Picamera2  # Corrected import name
from styles import stylesheet  # uncomment if you have a stylesheet module

# Set Qt platform plugin path
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = '/usr/lib/aarch64-linux-gnu/qt5/plugins/platforms/'

class VideoFeedWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.video_capture = cv2.VideoCapture(0)
        if not self.video_capture.isOpened():
            print("Error: Could not open USB camera.")
            return
        
        self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        self.image_label = QLabel()
        self.image_label.setFixedSize(640, 480)
        
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        
        self.setLayout(layout)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(1000 // 30)  # Update every 30 milliseconds (approximately 30 FPS)
    
    def update_frame(self):
        ret, frame = self.video_capture.read()
        if ret:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            self.image_label.setPixmap(pixmap)


class ImageCaptureThread(QThread):
    update_status = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, image_directory, parent=None):
        super().__init__(parent)
        self.image_directory = image_directory
        self.success = True

    def run(self):
        timestamp = QDateTime.currentDateTime().toString("yyyyMMdd-hhmmss")

        for i in range(3):
            try:
                picam = Picamera2(i)
                picam.start()
                filename = os.path.join(self.image_directory, f'cam{i}_{timestamp}.jpg')
                picam.capture_file(filename)
                picam.stop()
                picam.close()
                self.update_status.emit(f"Picture {i+1} taken successfully")
            except Exception as e:
                self.update_status.emit(f"Error capturing picture from camera {i}: {str(e)}")
                self.success = False
                break

        self.finished.emit()


class DesktopFileCreator(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(stylesheet)  # uncomment if you have a stylesheet
        self.video_feed_widget = VideoFeedWidget()  # Initialize video feed widget
        self.is_taking_picture = False  # Initialize is_taking_picture attribute
        self.initUI()
        self.process = None
        self.picameras = []
        
    def initUI(self):
        self.setWindowTitle('MultiCam')
        self.setWindowIcon(QIcon('multicam.png'))  
        self.setGeometry(200, 50, 800, 600)  # Adjusted size for accommodating live view

        layout = QVBoxLayout(self)
        
        # Add video feed widget
        layout.addWidget(self.video_feed_widget)
        
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
        if self.is_taking_picture:
            return
        
        self.is_taking_picture = True
        self.cleanup_cameras()  # Ensure any existing cameras are stopped before capturing new pictures
        self.status_label.setText("Taking images...")  # Update status label
        
        # Stop live view
        self.video_feed_widget.video_capture.release()
        self.video_feed_widget.timer.stop()
        
        # Create and start the image capture thread
        self.capture_thread = ImageCaptureThread(self.image_directory)
        self.capture_thread.update_status.connect(self.update_status_label)
        self.capture_thread.finished.connect(self.reset_status_label)
        self.capture_thread.finished.connect(self.restart_live_view)  # Restart live view after capture
        self.capture_thread.start()

    def update_status_label(self, message):
        self.status_label.setText(message)

    def reset_status_label(self):
        # Reset status label after 1 second
        QTimer.singleShot(1000, lambda: self.status_label.setText("Camera is ready"))
        self.is_taking_picture = False

    def restart_live_view(self):
        # Restart live view after picture capture is complete
        self.video_feed_widget.video_capture.open(0)
        self.video_feed_widget.timer.start()

    def cleanup_cameras(self):
        for picam in self.picameras:
            try:
                # Replace with your PiCamera2 cleanup logic
                # picam.stop()
                # picam.close()
                pass
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

