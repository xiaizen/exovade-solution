from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QLabel, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal

class ResultCard(QFrame):
    clicked = pyqtSignal(dict) # emits result data

    def __init__(self, result_data, parent=None):
        super().__init__(parent)
        self.data = result_data
        self.setFixedSize(200, 160)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #252525;
                border: 1px solid #333;
                border-radius: 12px;
            }
            QFrame:hover {
                background-color: #2F2F2F;
                border: 1px solid #00FF88;
                box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
            }
            QLabel {
                border: none;
                background: transparent;
                color: #EEE;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        # 1. Thumbnail Placeholder
        # Container style
        self.thumb = QLabel()
        self.thumb.setStyleSheet("""
            background-color: #101010;
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
            border-bottom: 1px solid #333;
            font-weight: bold;
            color: #555;
            font-size: 20px;
        """)
        self.thumb.setFixedHeight(100)
        self.thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb.setText(self.data.get('class_name', 'OBJ').upper())
        layout.addWidget(self.thumb)
        
        # 2. Meta Data Container
        meta_container = QFrame()
        meta_container.setStyleSheet("background: transparent; border: none; padding: 8px;")
        meta_layout = QVBoxLayout(meta_container)
        meta_layout.setContentsMargins(4,4,4,4)
        meta_layout.setSpacing(4)
        
        # Top Row: Time + Score Badge
        row = QVBoxLayout()
        row.setContentsMargins(0,0,0,0)
        
        # Timestamp
        ts = self.data.get('timestamp', 0)
        minutes = int(ts // 60)
        seconds = int(ts % 60)
        time_str = f"{minutes:02d}:{seconds:02d}"
        
        lbl_time = QLabel(f"⏱ {time_str}")
        lbl_time.setStyleSheet("color: #AAA; font-size: 11px; font-family: monospace;")
        row.addWidget(lbl_time)
        
        meta_layout.addLayout(row)
        
        # Confidence Bar (Slim)
        score = self.data.get('score', 0)
        bar = QProgressBar()
        bar.setFixedHeight(3)
        bar.setTextVisible(False)
        bar.setRange(0, 100)
        bar.setValue(int(score * 100))
        
        # Dynamic Color
        color = "#00FF88" # Green
        if score < 0.6: color = "#FF4444" # Red
        elif score < 0.8: color = "#FFCC00" # Yellow
            
        bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #444;
                border-radius: 1px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 1px;
            }}
        """)
        
        meta_layout.addWidget(bar)
        
        # Bottom Label (Class Name with high contrast)
        lbl_cls = QLabel(self.data.get('class_name', 'Unknown').upper())
        lbl_cls.setStyleSheet("color: #FFF; font-weight: 800; font-size: 13px; letter-spacing: 1px;")
        meta_layout.addWidget(lbl_cls)
        
        layout.addWidget(meta_container)

    def mousePressEvent(self, event):
        self.clicked.emit(self.data)
        super().mousePressEvent(event)
