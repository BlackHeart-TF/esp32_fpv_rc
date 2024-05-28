import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt, QTimer
import pygame,threading,receiver
from queue import Queue

class QtController(QMainWindow):
    def __init__(self, targetIP,parent=None):
        super().__init__(parent=parent)

        self.targetIP = targetIP
        self.udp = receiver.udp_transitter(self.targetIP)
        self.setWindowTitle("QT Viewer")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)

        self.clayout = QVBoxLayout()
        self.clayout.addWidget(self.image_label)
        self.central_widget.setLayout(self.clayout)

        pygame.init()
        pygame.joystick.init()
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

        self.thread = None

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(5)  # Update frame every 50 milliseconds

    def showEvent(self,event):
        super().showEvent(event)
        if not self.udp.running:
            self.udp.Begin()

    def update_frame(self):
        if not self.udp.frame_q.empty():
            frame = self.udp.frame_q.get(timeout=1)
            image = QImage.fromData(frame)
            pixmap = QPixmap.fromImage(image)
            self.image_label.setPixmap(pixmap)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        pygame.quit()
        self.udp.running = False
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)


    window = QtController("192.168.2.206")
    window.show()

    sys.exit(app.exec())
