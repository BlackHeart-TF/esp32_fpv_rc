import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QSizePolicy
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt, QTimer
import numpy as np
import cv2
import struct
from lib.UDPReceiver import UDP

try:
    from ultralytics import YOLO
except Exception:
    YOLO = None


class YOLOController(QMainWindow):
    def __init__(self, targetIP, parent=None, model_path: str = 'yolov8n.pt'):
        super().__init__(parent=parent)
        self.setMinimumSize(400, 300)

        self.targetIP = targetIP
        UDP.Begin()
        self.udp = UDP(self.targetIP)
        self.udp.BeginStream()

        self.setWindowTitle("YOLO Controller")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.image_label = QLabel(self)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.central_widget.setLayout(layout)

        # Control params
        self.track_vertical = True
        self.x_gain = 0.8
        self.y_gain = 0.4
        self.invert_x = False
        self.invert_y = False
        self.target_class = 'person'  # track only people by default
        self.infer_every_n = 1  # run detector each frame (can increase if heavy)
        self._frame_count = 0
        self.min_conf = 0.5
        self.last_target_center = None
        self.smooth_x = 0.0
        self.smooth_y = 0.0
        self.last_servo_x = 1500
        self.last_servo_y = 1500

        # Face detection (prefer faces when available)
        self.use_face_detection = True
        self.fallback_to_person = False  # track only faces by default; set True to allow YOLO fallback
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            if self.face_cascade.empty():
                self.face_cascade = None
                print('Warning: Failed to load Haar face cascade')
        except Exception:
            self.face_cascade = None

        # Model
        self.model = None
        if YOLO is not None:
            try:
                self.model = YOLO(model_path)
            except Exception as e:
                print(f"YOLO load failed: {e}")
                self.model = None

        # Timers
        self.frame_width = 640
        self.frame_height = 480
        self.timer = QTimer()
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(20)  # ~50 FPS tick

    def showEvent(self, event):
        super().showEvent(event)
        if not self.udp.listening:
            UDP.Begin()

    def closeEvent(self, event):
        self.udp.EndStream()
        if len(UDP.frame_queues) <= 0:
            UDP.listening = False
        super().closeEvent(event)

    def _on_tick(self):
        frame = self._get_latest_frame()
        if frame is None:
            return

        img = self._decode_jpeg(frame)
        if img is None:
            return
        self.frame_height, self.frame_width = img.shape[:2]

        target_bbox = None
        # Try face first (if enabled)
        if self.use_face_detection and self.face_cascade is not None:
            try:
                target_bbox = self._detect_face_bbox(img)
            except Exception:
                target_bbox = None

        # Optional fallback to YOLO person detection
        if target_bbox is None and self.fallback_to_person and self.model is not None and (self._frame_count % self.infer_every_n == 0):
            try:
                results = self.model.predict(img, verbose=False, device='cpu')
                target_bbox = self._select_target(results)
            except Exception as e:
                print(f"YOLO inference error: {e}")
                target_bbox = None
        self._frame_count += 1

        if target_bbox is not None:
            x1, y1, x2, y2 = target_bbox
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            self.last_target_center = (cx, cy)

            dx = (cx - (self.frame_width / 2.0)) / (self.frame_width / 2.0)  # -1..1, left negative
            dy = (cy - (self.frame_height / 2.0)) / (self.frame_height / 2.0)  # -1..1, up negative

            if self.invert_x:
                dx = -dx
            if self.invert_y:
                dy = -dy

            x_norm = np.clip(-dx * self.x_gain, -1.0, 1.0)
            y_norm = np.clip(dy * self.y_gain, -1.0, 1.0) if self.track_vertical else 0.0

            alpha = 0.4
            self.smooth_x = (1 - alpha) * self.smooth_x + alpha * x_norm
            self.smooth_y = (1 - alpha) * self.smooth_y + alpha * y_norm

            servo_x = int((self.smooth_x + 1.0) * 500 + 1000)
            servo_y = int((self.smooth_y + 1.0) * 500 + 1000)
            servo_x = max(1000, min(2000, servo_x))
            servo_y = max(1000, min(2000, servo_y))

            self.last_servo_x = servo_x
            self.last_servo_y = servo_y
            self._send_servo(self.last_servo_x, self.last_servo_y)

            # draw bbox
            cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            cv2.circle(img, (int(cx), int(cy)), 4, (0, 0, 255), -1)

        else:
            # No detection this tick: keep sending the last command so device doesn't auto-center
            self._send_servo(self.last_servo_x, self.last_servo_y)

        self._show_frame(img)

    def _get_latest_frame(self):
        q = self.udp.frame_queue
        frame = None
        try:
            while True:
                frame = q.get_nowait()
        except Exception:
            pass
        return frame

    def _decode_jpeg(self, data: bytes):
        try:
            arr = np.frombuffer(data, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            return img
        except Exception:
            return None

    def _select_target(self, results):
        best = None
        best_score = 1e9
        best_conf = -1.0
        try:
            r = results[0]
            boxes = r.boxes
            names = r.names if hasattr(r, 'names') else None
            for b in boxes:
                conf = float(b.conf[0]) if hasattr(b, 'conf') else 0.0
                if conf < self.min_conf:
                    continue
                cls_id = int(b.cls[0]) if hasattr(b, 'cls') else None
                cls_name = names.get(cls_id, str(cls_id)) if names and cls_id is not None else None
                if self.target_class is not None and cls_name != self.target_class:
                    continue
                x1, y1, x2, y2 = map(float, b.xyxy[0])
                if self.last_target_center is not None:
                    cx = (x1 + x2) / 2.0
                    cy = (y1 + y2) / 2.0
                    dx = cx - self.last_target_center[0]
                    dy = cy - self.last_target_center[1]
                    dist2 = dx * dx + dy * dy
                    score = dist2 / max(conf, 1e-3)
                    if score < best_score:
                        best_score = score
                        best_conf = conf
                        best = (x1, y1, x2, y2)
                else:
                    area = (x2 - x1) * (y2 - y1)
                    score = -conf * 1e6 - area
                    if score < best_score:
                        best_score = score
                        best_conf = conf
                        best = (x1, y1, x2, y2)
        except Exception:
            return None
        return best

    def _detect_face_bbox(self, img_bgr):
        # Run Haar cascade on downscaled grayscale for speed
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape[:2]
        target_w = 320
        scale = w / float(target_w) if w > target_w else 1.0
        if scale > 1.0:
            small = cv2.resize(gray, (int(w / scale), int(h / scale)), interpolation=cv2.INTER_LINEAR)
        else:
            small = gray
        faces = self.face_cascade.detectMultiScale(small, scaleFactor=1.1, minNeighbors=6, minSize=(40, 40))
        if len(faces) == 0:
            return None
        best = None
        best_score = 1e18
        cx_frame = w / 2.0
        cy_frame = h / 2.0
        for (x, y, fw, fh) in faces:
            x1 = x * scale
            y1 = y * scale
            x2 = (x + fw) * scale
            y2 = (y + fh) * scale
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            # Prefer faces near the frame center and near last target; reward larger faces slightly
            dist_center2 = (cx - cx_frame) * (cx - cx_frame) + (cy - cy_frame) * (cy - cy_frame)
            if self.last_target_center is not None:
                dx = cx - self.last_target_center[0]
                dy = cy - self.last_target_center[1]
                dist_last2 = dx * dx + dy * dy
            else:
                dist_last2 = 0.0
            area = (x2 - x1) * (y2 - y1)
            score = 1.5 * dist_center2 + 1.0 * dist_last2 - 0.001 * area
            if score < best_score:
                best_score = score
                best = (x1, y1, x2, y2)
        return best

    def _show_frame(self, img_bgr):
        rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        qimg = qimg.scaled(self.image_label.width(), self.image_label.height(), Qt.KeepAspectRatio, Qt.FastTransformation)
        pixmap = QPixmap.fromImage(qimg)
        self.image_label.setPixmap(pixmap)

    def _send_servo(self, steering_scaled: int, throttle_scaled: int):
        payload = struct.pack('<hh', steering_scaled, throttle_scaled)
        self.udp.SendCommand(b'\x54' + payload)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.0.64"
    window = YOLOController(ip)
    window.show()
    sys.exit(app.exec())


