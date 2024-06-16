import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,QSizePolicy
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt, QTimer
import pygame,threading,receiver,struct
from pygame.joystick import Joystick
from queue import Queue
from lib.UDPReceiver import UDP

class QtController(QMainWindow):
    def __init__(self, targetIP,parent=None):
        super().__init__(parent=parent)

        self.targetIP = targetIP
        #self.udp = receiver.udp_transitter(self.targetIP)
        UDP.Begin()
        self.udp = UDP(self.targetIP)
        self.udp.BeginStream()
        self.label_width = 640
        self.label_height = 480
        self.setWindowTitle("QT Viewer")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.image_label = QLabel(self)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setAlignment(Qt.AlignCenter)
        
        self.clayout = QVBoxLayout()
        self.clayout.addWidget(self.image_label)
        self.central_widget.setLayout(self.clayout)

        pygame.init()
        pygame.joystick.init()
        self.joystick_count = pygame.joystick.get_count()
        self.joysticks = [Joystick(x) for x in range(self.joystick_count)]
        self.previous_input = {}

        self.screentimer = QTimer()
        self.screentimer.timeout.connect(self.new_update_frame)
        self.screentimer.start(5)  # Update frame every 5 milliseconds

        self.joytimer = QTimer()
        self.joytimer.timeout.connect(self.updateInput)
        self.joytimer.start(5)  # Update frame every 5 milliseconds

    def showEvent(self,event):
        super().showEvent(event)
        if not self.udp.listening:
            self.udp.Begin()

    def updateInput(self):
        if not self.joysticks:
            return
        pygame.event.pump()
        for joystick in self.joysticks:
            current_input = self.get_current_input(joystick)

            # if not self.previous_input or current_input!= self.previous_input:
            #     self.previous_input = current_input
            self.send_input(current_input)

    def get_current_input(self,joystick:Joystick):
        axiscount = joystick.get_numaxes()
        LstickX = joystick.get_axis(0)
        #RStickX = joystick.get_axis(3)
        Ltrigger = joystick.get_axis(2)
        Rtrigger = joystick.get_axis(5)
        
        # Scale the axis values to the range 1000-2000
        LstickX_scaled = int((LstickX + 1) * 500+1000)  # Map -1 to 1 to 1000-2000
    
        # Calculate the throttle/break axis value, negating each other
        throttle_break = ((1+Rtrigger) - (1+Ltrigger))/2
        throttle_break_scaled = int((throttle_break + 1) * 500+1000)
        #print(f"lx:{LstickX} lt:{Ltrigger} rt:{Rtrigger} thr:{throttle_break} thsc:{throttle_break_scaled}")
        # Pack the scaled value into a little endian byte array
        byte_array = struct.pack('<h', throttle_break_scaled)
        # Pack the scaled values into a little endian byte array
        byte_array = struct.pack('<hh', LstickX_scaled, throttle_break_scaled)
        
        return byte_array

    def send_input(self,input):
        self.udp.SendCommand(b'\x54'+input)

    # def showEvent(self,sevent):
    #     super().showEvent(event)

    def showEvent(self,event):
        super().showEvent(event)
        self.label_width = 640
        self.label_height = 480

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.label_width = self.image_label.width()
        self.label_height = self.image_label.height()
        

    def new_update_frame(self):
        frame = self.udp.frame_queue.get(timeout=1)
        if frame:
            image = QImage.fromData(frame)
            image =image.scaled(self.label_width, self.label_height, Qt.KeepAspectRatio,Qt.FastTransformation)
            pixmap = QPixmap.fromImage(image)
            self.image_label.setPixmap(pixmap)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        pygame.quit()
        self.udp.EndStream()
        if len(UDP.frame_queues) <= 0:
            UDP.listening = False
        self.joytimer.stop()
        self.screentimer.stop()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)


    window = QtController("192.168.0.64")
    window.show()
    exitc = app.exec()
    
    sys.exit(exitc)
