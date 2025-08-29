import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QSizePolicy
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt, QTimer
import numpy as np
import cv2
from lib.UDPReceiver import UDP


class DriveAnalyzer(QMainWindow):
    def __init__(self, targetIP, parent=None):
        super().__init__(parent=parent)

        self.targetIP = targetIP
        UDP.Begin()
        self.udp = UDP(self.targetIP)
        self.udp.BeginStream()

        self.setWindowTitle("Drive Analyzer")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.image_label = QLabel(self)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.central_widget.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(20)

        self.frame_width = 640
        self.frame_height = 480

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

        vis = img.copy()
        roi = self._road_roi(img)
        edges = self._edges(roi)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=50, minLineLength=40, maxLineGap=50)

        left_lines, right_lines = self._classify_lines(lines, roi.shape[1])
        left_lane = self._average_slope_intercept(left_lines)
        right_lane = self._average_slope_intercept(right_lines)

        offset_px, heading_deg = self._compute_pose(left_lane, right_lane, roi.shape)

        self._draw_overlay(vis, roi, left_lane, right_lane, offset_px, heading_deg)
        self._show_frame(vis)

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
            return cv2.imdecode(arr, cv2.IMREAD_COLOR)
        except Exception:
            return None

    def _road_roi(self, img_bgr):
        h, w = img_bgr.shape[:2]
        # Use bottom 45% as road ROI
        y0 = int(h * 0.55)
        return img_bgr[y0:h, 0:w]

    def _edges(self, roi_bgr):
        gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 60, 180)
        return edges

    def _classify_lines(self, lines, width):
        left, right = [], []
        if lines is None:
            return left, right
        center_x = width / 2.0
        for l in lines:
            x1, y1, x2, y2 = l[0]
            if x2 == x1:
                continue
            slope = (y2 - y1) / float(x2 - x1)
            if abs(slope) < 0.3:
                continue
            # classify by x position and sign of slope
            if slope < 0 and (x1 < center_x or x2 < center_x):
                left.append((slope, y1 - slope * x1))
            elif slope > 0 and (x1 > center_x or x2 > center_x):
                right.append((slope, y1 - slope * x1))
        return left, right

    def _average_slope_intercept(self, line_params):
        if not line_params:
            return None
        slopes, intercepts = zip(*line_params)
        m = float(np.mean(slopes))
        b = float(np.mean(intercepts))
        return (m, b)

    def _compute_pose(self, left_lane, right_lane, roi_shape):
        h, w = roi_shape[:2]
        y_eval = h - 1
        lanes = []
        for lane in (left_lane, right_lane):
            if lane is None:
                continue
            m, b = lane
            if abs(m) < 1e-3:
                continue
            x = (y_eval - b) / m
            lanes.append(x)
        if len(lanes) == 2:
            lane_center = (lanes[0] + lanes[1]) / 2.0
        elif len(lanes) == 1:
            # assume lane width ~ 3.7m -> proportional px estimate; here just bias toward center
            lane_center = lanes[0]
        else:
            return 0.0, 0.0
        frame_center = w / 2.0
        offset_px = lane_center - frame_center

        heading_deg = 0.0
        if left_lane and right_lane:
            heading_deg = np.degrees(np.arctan((left_lane[0] + right_lane[0]) / 2.0))
        elif left_lane:
            heading_deg = np.degrees(np.arctan(left_lane[0]))
        elif right_lane:
            heading_deg = np.degrees(np.arctan(right_lane[0]))
        return offset_px, heading_deg

    def _draw_overlay(self, vis_bgr, roi_bgr, left_lane, right_lane, offset_px, heading_deg):
        h, w = vis_bgr.shape[:2]
        y0 = int(h * 0.55)
        # draw lanes
        for lane, color in ((left_lane, (0, 255, 0)), (right_lane, (0, 255, 0))):
            if lane is None:
                continue
            m, b = lane
            y1 = 0
            y2 = roi_bgr.shape[0]
            x1 = int((y1 - b) / m)
            x2 = int((y2 - b) / m)
            cv2.line(vis_bgr, (x1, y0 + y1), (x2, y0 + y2), color, 2)

        # draw center and metrics
        cv2.line(vis_bgr, (w // 2, y0), (w // 2, h), (255, 0, 0), 1)
        text = f"offset_px: {offset_px:.1f}  heading_deg: {heading_deg:.1f}"
        cv2.putText(vis_bgr, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 220, 50), 2, cv2.LINE_AA)

    def _show_frame(self, img_bgr):
        rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        qimg = qimg.scaled(self.image_label.width(), self.image_label.height(), Qt.KeepAspectRatio, Qt.FastTransformation)
        pixmap = QPixmap.fromImage(qimg)
        self.image_label.setPixmap(pixmap)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.0.64"
    window = DriveAnalyzer(ip)
    window.show()
    sys.exit(app.exec())


