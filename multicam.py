import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtGui import QIcon, QImage, QPixmap
from PyQt5.QtCore import QTimer, QDateTime, QThread, pyqtSignal
import cv2
from gpiozero import Button
from picamera2 import Picamera2  # Assuming this is the correct import
from styles import stylesheet  # uncomment if you have a stylesheet module

class VideoFeedWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 150)
        
        self.video_capture = cv2.VideoCapture(0)
        if not self.video_capture.isOpened():
            print("Error: Could not open USB camera.")
            return
        
        self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        
        self.image_label = QLabel()
        self.image_label.setFixedSize(320, 240)

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        
        self.setLayout(layout)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(1000 // 30)
    
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
                camera_config = picam.create_still_configuration(main={"size": (3280, 2464)})
                picam.configure(camera_config)
                
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
        self.video_feed_widget = VideoFeedWidget()
        self.is_taking_picture = False
        self.initUI()
        self.process = None
        self.picameras = []
        self.button = Button(21)
        self.button.when_pressed = self.take_picture_gpio  # Connect GPIO button press event

    def initUI(self):
        self.setWindowTitle('MultiCam')
        self.setWindowIcon(QIcon('multicam.png'))
        self.setGeometry(0, 30, 460, 150)

        layout = QVBoxLayout(self)

        layout.addWidget(self.video_feed_widget)
        
        self.take_picture_button = QPushButton('Snap', self)
        self.take_picture_button.clicked.connect(self.take_picture_gui)  # Connect GUI button click event
        layout.addWidget(self.take_picture_button)

        self.status_label = QLabel('Camera is ready', self)
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        
        self.image_directory = '/home/sparky/multiimg'
        os.makedirs(self.image_directory, exist_ok=True)

    def take_picture_gui(self):
        if self.is_taking_picture:
            return
        
        self.is_taking_picture = True
        self.cleanup_cameras()
        self.status_label.setText("Taking images...")
        
        self.video_feed_widget.video_capture.release()
        self.video_feed_widget.timer.stop()
        
        self.capture_thread = ImageCaptureThread(self.image_directory)
        self.capture_thread.update_status.connect(self.update_status_label)
        self.capture_thread.finished.connect(self.reset_status_label)
        self.capture_thread.finished.connect(self.restart_live_view)
        self.capture_thread.start()

    def take_picture_gpio(self):
        if self.is_taking_picture:
            return
        
        self.is_taking_picture = True
        self.cleanup_cameras()
        self.status_label.setText("Taking images...")
        
        self.video_feed_widget.video_capture.release()
        self.video_feed_widget.timer.stop()
        
        self.capture_thread = ImageCaptureThread(self.image_directory)
        self.capture_thread.update_status.connect(self.update_status_label)
        self.capture_thread.finished.connect(self.reset_status_label)
        self.capture_thread.finished.connect(self.restart_live_view)
        self.capture_thread.start()

    def update_status_label(self, message):
        self.status_label.setText(message)

    def reset_status_label(self):
        QTimer.singleShot(1000, lambda: self.status_label.setText("Camera is ready"))
        self.is_taking_picture = False

    def restart_live_view(self):
        self.video_feed_widget.video_capture.open(0)
        self.video_feed_widget.timer.start()

    def cleanup_cameras(self):
        for picam in self.picameras:
            try:
                picam.stop()
                picam.close()
            except Exception as e:
                print(f"Error stopping camera: {str(e)}")
        self.picameras.clear()

    def closeEvent(self, event):
        self.cleanup_cameras()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DesktopFileCreator()
    window.show()
    sys.exit(app.exec_())


