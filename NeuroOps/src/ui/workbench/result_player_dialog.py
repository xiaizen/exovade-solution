from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, QSize
from src.ui.player_widget import PlayerWidget

class ResultPlayerDialog(QDialog):
    def __init__(self, video_path, result_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RESULT VIEWER // " + result_data.get('class_name', 'UNK').upper())
        self.resize(1024, 600)
        self.setStyleSheet("background-color: #1a1a1a; color: #EEE;")
        
        self.video_path = video_path
        self.result_data = result_data
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QHBoxLayout()
        header.setContentsMargins(15, 10, 15, 10)
        header.addWidget(QLabel("SEARCH RESULT REPLAY"))
        header.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("background: transparent; color: #AAA; border: none; font-size: 16px;")
        close_btn.clicked.connect(self.reject)
        header.addWidget(close_btn)
        
        layout.addLayout(header)
        
        # Player Widget (Embedded)
        self.player = PlayerWidget()
        # Hide the "Open" button since this is a result view
        self.player.btn_open.setVisible(False)
        layout.addWidget(self.player)
        
        # Start Loading
        timestamp = float(self.result_data.get('timestamp', 0.0))
        self.player.load_search_result(self.video_path, timestamp, self.result_data)

    def closeEvent(self, event):
        self.player.media_player.stop()
        super().closeEvent(event)
