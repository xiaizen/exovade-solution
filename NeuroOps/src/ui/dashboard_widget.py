from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QIcon, QPainterPath, QPen
from src.core.analytics import AnalyticsEngine

class BarChartWidget(QWidget):
    def __init__(self, data_dict, title="DISTRIBUTION", parent=None):
        super().__init__(parent)
        self.data = data_dict
        self.title = title
        self.setMinimumHeight(200)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # BG
        painter.fillRect(self.rect(), QColor("#121212"))
        
        if not self.data:
            painter.setPen(QColor("#666"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "NO DATA")
            return

        # Draw specific bars
        keys = list(self.data.keys())
        values = list(self.data.values())
        max_val = max(values) if values else 1
        
        margin = 40
        bar_width = (self.width() - 2 * margin) / len(keys)
        
        painter.setPen(QColor("#00FF88"))
        painter.drawText(10, 20, self.title)

        for i, (label, val) in enumerate(self.data.items()):
            h = (val / max_val) * (self.height() - 60)
            x = margin + i * bar_width
            y = self.height() - 30 - h
            
            # Gradient
            grad = QLinearGradient(x, y, x, self.height() - 30)
            grad.setColorAt(0, QColor(0, 255, 136, 180))
            grad.setColorAt(1, QColor(0, 255, 136, 20))
            painter.setBrush(grad)
            painter.setPen(Qt.PenStyle.NoPen)
            
            # Bar
            painter.drawRect(int(x + 5), int(y), int(bar_width - 10), int(h))
            
            # Label
            painter.setPen(QColor("#ccc"))
            painter.drawText(int(x), int(self.height() - 10), int(bar_width), 20, 
                           Qt.AlignmentFlag.AlignCenter, label[:5]) # Truncate

class LiveActivityChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(150)
        self.history = [] # List of detection counts
        self.max_points = 50
        
    def add_data_point(self, count):
        self.history.append(count)
        if len(self.history) > self.max_points:
            self.history.pop(0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#1A1A1A"))
        
        if not self.history:
            return

        # Draw Grid
        painter.setPen(QColor("#333"))
        w = self.width()
        h = self.height()
        painter.drawLine(0, h//2, w, h//2)
        
        # Draw Line
        path = QPainterPath()
        max_val = max(max(self.history), 10) # Minimum scale of 10
        
        step_x = w / (self.max_points - 1)
        
        for i, val in enumerate(self.history):
            x = i * step_x
            y = h - (val / max_val * h)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
                
        painter.setPen(QPen(QColor("#00FF88"), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        
        # Fill under
        path.lineTo(w, h)
        path.lineTo(0, h)
        painter.setBrush(QColor(0, 255, 136, 50))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)


class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.engine = AnalyticsEngine()
        self.video_id = None
        self.class_counts = {} # Local accumulator
        self.setup_ui()

    def set_video(self, video_id, filename=""):
        self.video_id = video_id
        self.class_counts = {}
        self.live_chart.history = []
        self.live_chart.update()
        
        # Update Header
        lbl = self.findChild(QLabel, "Header")
        if lbl:
            lbl.setText(f"MISSION DASHBOARD // ANALYTICS // {filename.upper()}")
            
        self.refresh_stats() # Clear UI

    def add_alert(self, severity, message):
        item = QListWidgetItem()
        timestamp = QDateTime.currentDateTime().toString("HH:mm:ss")
        item.setText(f"[{timestamp}] [{severity.upper()}] {message}")
        
        if severity == "critical":
            item.setForeground(QColor("#FF0055"))
        elif severity == "high":
            item.setForeground(QColor("#FF5500"))
        else:
            item.setForeground(QColor("#00FF88"))
            
        self.alert_list.insertItem(0, item)
        if self.alert_list.count() > 100:
            self.alert_list.takeItem(100)

    def handle_stats_update(self, stats):
        # Update Live Chart
        count = stats.get("detections", 0)
        self.live_chart.add_data_point(count)
        
        # Update Counters
        self.lbl_det_count.setText(str(count))
        self.lbl_fps_sim.setText(f"{stats.get('timestamp', 0):.2f}s")
        
        # Update Class Dist (Accumulate)
        current_classes = stats.get("classes", [])
        for c in current_classes:
            self.class_counts[c] = self.class_counts.get(c, 0) + 1
            
        # Force update bar chart every frame (or could throttle)
        if hasattr(self, 'bar_chart'):
            self.bar_chart.data = self.class_counts
            self.bar_chart.update()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        header = QLabel("MISSION DASHBOARD // ANALYTICS")
        header.setObjectName("Header")
        layout.addWidget(header)
        
        # Main Layout
        main_row = QHBoxLayout()
        layout.addLayout(main_row)
        
        # Left Col (Visuals)
        self.left_col = QWidget()
        self.left_layout = QVBoxLayout(self.left_col)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        main_row.addWidget(self.left_col, stretch=2)
        
        # 1. Real-time Activity Chart
        self.left_layout.addWidget(QLabel("LIVE DETECTION ACTIVITY"))
        self.live_chart = LiveActivityChart()
        self.left_layout.addWidget(self.live_chart)
        
        # 2. Live Stats Row
        stats_row = QHBoxLayout()
        
        def create_stat_card(title, value_lbl_obj_name):
            frame = QFrame()
            frame.setStyleSheet("background: #222; border-radius: 6px; padding: 10px;")
            l = QVBoxLayout(frame)
            t = QLabel(title)
            t.setStyleSheet("color: #888; font-size: 10px;")
            v = QLabel("0")
            v.setObjectName(value_lbl_obj_name)
            v.setStyleSheet("color: #FFF; font-size: 24px; font-weight: bold;")
            l.addWidget(t)
            l.addWidget(v)
            return frame, v
            
        f1, self.lbl_det_count = create_stat_card("OBJECTS (CURRENT)", "lbl_det")
        f2, self.lbl_fps_sim = create_stat_card("ANALYSIS TIME", "lbl_time")
        
        stats_row.addWidget(f1)
        stats_row.addWidget(f2)
        self.left_layout.addLayout(stats_row)
        
        # 3. Bar Chart (Historical/Overall)
        self.content_layout = QVBoxLayout() 
        self.left_layout.addLayout(self.content_layout)
        
        # Initialize Chart
        self.bar_chart = BarChartWidget({}, title="CUMULATIVE CLASSES")
        self.content_layout.addWidget(self.bar_chart)
        
        self.left_layout.addStretch()

        # Right Col (Alerts)
        right_col = QWidget()
        right_layout = QVBoxLayout(right_col)
        
        lbl_alerts = QLabel("LIVE ZEN ALERTS")
        lbl_alerts.setStyleSheet("color: #00FF88; font-weight: bold;")
        right_layout.addWidget(lbl_alerts)
        
        self.alert_list = QListWidget()
        self.alert_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(0, 0, 0, 0.3);
                border: 1px solid #333;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #222;
            }
        """)
        right_layout.addWidget(self.alert_list)
        
        main_row.addWidget(right_col, stretch=1)

    def refresh_stats(self):
        # Manually reset UI elements if needed
        if self.video_id:
            # Could fetch DB stats if reloading
            pass
        self.bar_chart.data = self.class_counts
        self.bar_chart.update()

