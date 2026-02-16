from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                             QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView)
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime, QSize, QTimer
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QIcon, QPainterPath, QPen, QFont
from src.core.analytics import AnalyticsEngine
from ui.styles.palette import Palette

class LiveActivityChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(220)
        self.history = [] # List of detection counts
        self.max_points = 50
        self.title = "LIVE DETECTION ACTIVITY"
        
    def add_data_point(self, count):
        self.history.append(count)
        if len(self.history) > self.max_points:
            self.history.pop(0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # BG - Slightly lighter than main bg, similar to card
        painter.fillRect(self.rect(), QColor(Palette.CARD))
        
        # Title
        painter.setPen(QColor(Palette.MUTED_FOREGROUND))
        painter.setFont(QFont("JetBrains Mono", 10))
        painter.drawText(20, 30, self.title)
        
        if not self.history:
            return

        w = self.width()
        h = self.height()
        
        # Draw Grid (Minimal)
        painter.setPen(QPen(QColor(Palette.BORDER), 1, Qt.PenStyle.DotLine))
        # Remove grid lines to match cleaner screenshot look or keep very faint
        # painter.drawLine(0, h//2, w, h//2)
        # painter.drawLine(0, h-40, w, h-40)

        # Content Area
        chart_h = h - 60
        chart_top = 40
        
        # Draw Line
        path = QPainterPath()
        max_val = max(max(self.history), 16) # Scale to at least 16 like screenshot
        
        # X-axis scale
        step_x = (w - 40) / (self.max_points - 1)
        start_x = 20
        
        for i, val in enumerate(self.history):
            x = start_x + i * step_x
            # Invert Y: higher value = lower y
            y = chart_top + chart_h - (val / max_val * chart_h)
            
            if i == 0:
                path.moveTo(x, y)
            else:
                # Smooth curve (QuadTo) or simple LineTo
                # Simple LineTo matches the sharp peaks in screenshot better than heavy smoothing
                path.lineTo(x, y)
                
        # Stroke
        painter.setPen(QPen(QColor(Palette.PRIMARY), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        
        # Fill Gradient
        path.lineTo(w - 20, chart_top + chart_h)
        path.lineTo(start_x, chart_top + chart_h)
        path.closeSubpath()
        
        grad = QLinearGradient(0, chart_top, 0, chart_top + chart_h)
        c1 = QColor(Palette.PRIMARY)
        c1.setAlpha(50)
        c2 = QColor(Palette.PRIMARY)
        c2.setAlpha(0)
        grad.setColorAt(0, c1)
        grad.setColorAt(1, c2)
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(grad)
        painter.drawPath(path)
        
        # Draw Time Labels (Mock)
        painter.setPen(QColor(Palette.MUTED_FOREGROUND))
        painter.setFont(QFont("Inter", 8))
        painter.drawText(20, h-10, "00:00")
        painter.drawText(w//2, h-10, "12:00")
        painter.drawText(w-50, h-10, "18:00")


class StatCard(QFrame):
    def __init__(self, title, initial_value, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Palette.CARD};
                border: none;
                border-radius: 6px;
                padding: 10px;
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        self.setMinimumHeight(140) # Match height to chart roughly or at least taller like screenshot
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet(f"color: {Palette.PRIMARY}; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        
        self.lbl_value = QLabel(initial_value)
        self.lbl_value.setStyleSheet(f"color: {Palette.FOREGROUND}; font-size: 36px; font-weight: bold; font-family: 'JetBrains Mono';")
        
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)
        layout.addStretch()
        
    def update_value(self, val):
        self.lbl_value.setText(str(val))


class DetectionTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(["TIMESTAMP", "OBJECT", "CONFIDENCE", "ZONE"])
        
        # Style
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Palette.CARD};
                border: none;
                gridline-color: transparent;
                color: {Palette.FOREGROUND};
                border-radius: 6px;
                font-family: 'JetBrains Mono', monospace;
            }}
            QHeaderView::section {{
                background-color: {Palette.CARD};
                color: {Palette.MUTED_FOREGROUND};
                border: none;
                padding: 12px;
                font-weight: bold;
                font-size: 11px;
                text-align: left;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            QTableWidget::item {{
                padding: 12px;
                border-bottom: none;
            }}
            QTableWidget::item:selected {{
                background-color: transparent;
                color: {Palette.FOREGROUND};
            }}
        """)
        
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setShowGrid(False)
        
    def add_entry(self, obj_name, conf, zone="Zone A"):
        row = 0
        self.insertRow(row)
        
        time_str = QDateTime.currentDateTime().toString("HH:mm:ss")
        
        # Items
        t_item = QTableWidgetItem(time_str)
        t_item.setForeground(QColor(Palette.FOREGROUND))
        
        o_item = QTableWidgetItem(obj_name)
        o_item.setForeground(QColor(Palette.PRIMARY)) # Cyan for object name
        
        c_item = QTableWidgetItem(f"{int(conf*100)}%")
        
        # Color code confidence
        if conf > 0.8:
            c_item.setForeground(QColor(Palette.PRIMARY)) # Green/Cyan
        elif conf > 0.5:
             c_item.setForeground(QColor(Palette.WARNING)) # Yellow
        else:
             c_item.setForeground(QColor(Palette.DESTRUCTIVE)) # Red
        
        z_item = QTableWidgetItem(zone)
        z_item.setForeground(QColor(Palette.MUTED_FOREGROUND))
        
        self.setItem(row, 0, t_item)
        self.setItem(row, 1, o_item)
        self.setItem(row, 2, c_item)
        self.setItem(row, 3, z_item)
        
        # Limit rows
        if self.rowCount() > 20:
            self.removeRow(20)


class AlertItemWidget(QWidget):
    def __init__(self, severity, message, timestamp, parent=None):
        super().__init__(parent)
        self.timestamp = timestamp
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Icon placeholder
        icon_lbl = QLabel("⚠️") 
        if severity == "critical":
            icon_lbl.setStyleSheet(f"color: {Palette.DESTRUCTIVE}; font-size: 16px;")
        else:
            icon_lbl.setStyleSheet(f"color: {Palette.WARNING}; font-size: 16px;")
            
        layout.addWidget(icon_lbl)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet(f"color: {Palette.FOREGROUND}; font-weight: 500;")
        msg_lbl.setWordWrap(True)
        
        self.time_lbl = QLabel()
        self.time_lbl.setStyleSheet(f"color: {Palette.MUTED_FOREGROUND}; font-size: 11px;")
        self.update_time_label()
        
        text_layout.addWidget(msg_lbl)
        text_layout.addWidget(self.time_lbl)
        
        layout.addLayout(text_layout)

    def update_time_label(self):
        now = QDateTime.currentDateTime()
        diff_secs = self.timestamp.secsTo(now)
        
        if diff_secs < 60:
            time_str = "Just now"
        elif diff_secs < 3600:
            mins = diff_secs // 60
            time_str = f"{mins}m ago"
        elif diff_secs < 86400:
            hours = diff_secs // 3600
            time_str = f"{hours}h ago"
        else:
            days = diff_secs // 86400
            time_str = f"{days}d ago"
            
        self.time_lbl.setText(f"🕒 {time_str}")


class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.engine = AnalyticsEngine()
        self.video_id = None
        self.setup_ui()
        
        # Timer to update "time ago" labels
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_alert_times)
        self.timer.start(60000) # Update every minute

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Workspace Header
        ws_label = QLabel("WORKSPACE")
        ws_label.setStyleSheet(f"color: {Palette.MUTED_FOREGROUND}; font-size: 10px; letter-spacing: 1px;")
        # layout.addWidget(ws_label) # Already in topbar of main window usually, but acceptable here
        
        header = QLabel("MISSION DASHBOARD // ANALYTICS")
        header = QLabel("MISSION DASHBOARD // ANALYTICS")
        header.setObjectName("Header")
        header.setStyleSheet(f"color: {Palette.PRIMARY}; font-size: 20px; font-weight: 800; font-family: 'JetBrains Mono'; letter-spacing: 1px;")
        layout.addWidget(header)
        
        # Main Content Row
        content_row = QHBoxLayout()
        content_row.setSpacing(20)
        layout.addLayout(content_row)
        
        # --- Left Column (Charts & Tables) [Stretch 2 or 3] ---
        left_col = QWidget()
        left_layout = QVBoxLayout(left_col)
        left_layout.setContentsMargins(0,0,0,0)
        left_layout.setSpacing(20)
        content_row.addWidget(left_col, stretch=3)
        
        # 1. Live Activity Chart
        self.live_chart = LiveActivityChart()
        left_layout.addWidget(self.live_chart)
        
        # 2. Stats Cards Row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(20)
        
        self.card_objects = StatCard("OBJECTS (CURRENT)", "0")
        self.card_time = StatCard("ANALYSIS TIME", "0.0s")
        
        stats_row.addWidget(self.card_objects)
        stats_row.addWidget(self.card_time)
        left_layout.addLayout(stats_row)
        
        # 3. Detection Table
        self.table = DetectionTableWidget()
        left_layout.addWidget(self.table)
        
        # --- Right Column (Alerts) [Stretch 1] ---
        right_col = QWidget()
        right_layout = QVBoxLayout(right_col)
        right_layout.setContentsMargins(0,0,0,0)
        right_layout.setSpacing(10)
        content_row.addWidget(right_col, stretch=1)
        
        lbl_alerts = QLabel("LIVE ZEN ALERTS")
        lbl_alerts.setStyleSheet(f"color: {Palette.PRIMARY}; font-family: 'JetBrains Mono'; font-weight: bold; letter-spacing: 1px; font-size: 14px;")
        right_layout.addWidget(lbl_alerts)
        
        self.alert_list = QListWidget()
        self.alert_list.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
            }}
            QListWidget::item {{
                background-color: {Palette.CARD};
                border: none;
                border-radius: 6px;
                margin-bottom: 10px;
            }}
            QListWidget::item:hover {{
                border: none;
            }}
        """)
        self.alert_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        right_layout.addWidget(self.alert_list)
        
        # Alerts will be added dynamically via signals

    def add_alert_item(self, message, timestamp, severity):
        item = QListWidgetItem(self.alert_list)
        widget = AlertItemWidget(severity, message, timestamp)
        item.setSizeHint(widget.sizeHint())
        self.alert_list.insertItem(0, item) # Insert at top
        self.alert_list.setItemWidget(item, widget)

    def set_video(self, video_id, filename=""):
        self.video_id = video_id
        # Reset charts/tables
        self.live_chart.history = []
        self.live_chart.update()
        self.table.setRowCount(0)
        
        lbl = self.findChild(QLabel, "Header")
        if lbl:
            lbl.setText(f"MISSION DASHBOARD // ANALYTICS // {filename.upper()}")

    def add_alert(self, severity, message):
        # Called by worker or internal logic
        timestamp = QDateTime.currentDateTime()
        self.add_alert_item(message, timestamp, severity)
        
    def update_alert_times(self):
        for i in range(self.alert_list.count()):
            item = self.alert_list.item(i)
            widget = self.alert_list.itemWidget(item)
            if widget and isinstance(widget, AlertItemWidget):
                widget.update_time_label()

    def handle_stats_update(self, stats):
        # Update Live Chart
        count = stats.get("detections", 0)
        self.live_chart.add_data_point(count)
        
        # Update Cards
        self.card_objects.update_value(count)
        self.card_time.update_value(f"{stats.get('timestamp', 0):.2f}s")
        
        # Update Table with new detections
        detections = stats.get("details", []) 
        
        if detections:
            for d in detections:
                 self.table.add_entry(d['class'], d.get('confidence', 0.0), "Zone A")
        else:
             # Fallback if details missing
             current_classes = stats.get("classes", [])
             for c in current_classes:
                 self.table.add_entry(c, 0.95, "Zone A")
        
    def refresh_stats(self):
        pass
