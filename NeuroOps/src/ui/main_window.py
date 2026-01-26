import sys
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame, QApplication, QStackedWidget)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPalette, QColor
from ui.player_widget import PlayerWidget
from ui.search_widget import SearchWidget
from ui.dashboard_widget import DashboardWidget
from ui.rule_editor import RuleEditorWidget
from ui.rule_editor import RuleEditorWidget
from ui.workbench.modal import PrecisionEditorModal # Workbench
from ui.workbench.result_player_dialog import ResultPlayerDialog
from PyQt6.QtWidgets import QMessageBox

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NEURO_OPS // VISUAL_INTELLIGENCE")
        self.resize(1280, 800)
        self.setMinimumSize(1024, 768)

        # Setup Central Widget & Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 1. Sidebar (Navigation)
        self.setup_sidebar()

        # 2. Main Content Area (Top Bar + Stacked Pages)
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(20)
        self.main_layout.addWidget(self.content_container, stretch=1)

        # Top Bar
        self.setup_topbar()

        # Page Stack
        self.page_stack = QStackedWidget()
        self.content_layout.addWidget(self.page_stack)

        self.dashboard_widget = DashboardWidget()
        self.page_stack.addWidget(self.dashboard_widget) # Real Dashboard
        self.player_widget = PlayerWidget()
        self.page_stack.addWidget(self.player_widget) # Real Player Page
        
        self.search_widget = SearchWidget()
        self.search_widget.jump_to_timestamp.connect(self.on_search_jump)
        self.search_widget.search_result_selected.connect(self.on_search_result_selected)
        self.page_stack.addWidget(self.search_widget) # Real Search Page

        self.rule_editor = RuleEditorWidget()
        self.page_stack.addWidget(self.rule_editor) # Real Rule Editor

    def on_search_jump(self, video_id, timestamp):
        # Switch to player and seek
        # Note: In a full app, we need to handle loading the specific video_id.
        # For now, we assume the user is searching the currently loaded video or we just jump.
        self.page_stack.setCurrentIndex(1) # Player Page
        self.nav_buttons[1].setChecked(True)
        self.nav_buttons[2].setChecked(False)
        
        # Convert seconds to ms
        self.player_widget.media_player.setPosition(int(timestamp * 1000))
        self.player_widget.play_video()

    def on_search_result_selected(self, data):
        print(f"[MAIN] Search Result Selected: {data}")
        
        # Resolve Path
        vid_id = data.get('video_id')
        
        # Use player's DB manager (or main DB manager if we had one here)
        path = self.player_widget.db_manager.get_path_by_id(vid_id)
        
        if path:
            # Open Modal
            dialog = ResultPlayerDialog(path, data, self)
            dialog.exec()
        else:
            print(f"[MAIN] Error: Video path not found for ID {vid_id}")
            QMessageBox.warning(self, "Error", f"Could not find video file for ID {vid_id}")

    def connect_worker_signals(self):
        # Helper to connect player's worker to dashboard
        if self.player_widget.worker:
            self.player_widget.worker.alert_triggered.connect(self.dashboard_widget.add_alert)

    def setup_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(240)
        self.sidebar.setStyleSheet("background-color: #080808; border-right: 1px solid #1A1A1A;")
        
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Branding
        branding = QLabel("NEURO_OPS")
        branding.setObjectName("Header")
        branding.setAlignment(Qt.AlignmentFlag.AlignCenter)
        branding.setFixedHeight(60)
        layout.addWidget(branding)

        # Navigation Buttons
        self.nav_buttons = []
        self.add_nav_button("DASHBOARD", 0, layout)
        self.add_nav_button("VIDEO PLAYER", 1, layout)
        self.add_nav_button("NEURAL SEARCH", 2, layout)
        self.add_nav_button("RULE EDITOR", 3, layout)

        layout.addStretch()
        


        # System Status
        status = QLabel("SYSTEM: ONLINE\nGPU: ACTIVE")
        status.setStyleSheet("color: #444; font-size: 10px; padding: 20px;")
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status)

        self.main_layout.addWidget(self.sidebar)

    def add_nav_button(self, text, index, layout):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setFixedHeight(45)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-left: 3px solid transparent;
                color: #666;
                text-align: left;
                padding-left: 20px;
            }
            QPushButton:checked {
                color: #00FF88;
                border-left: 3px solid #00FF88;
                background-color: rgba(0, 255, 136, 0.05);
            }
            QPushButton:hover {
                color: #E0E0E0;
            }
        """)
        btn.clicked.connect(lambda: self.switch_page(index, btn))
        layout.addWidget(btn)
        self.nav_buttons.append(btn)
        
        # Set first button active by default
        if index == 0:
            btn.setChecked(True)

    def setup_topbar(self):
        topbar = QHBoxLayout()
        
        title = QLabel("WORKSPACE")
        title.setStyleSheet("color: #888; font-size: 12px;")
        
        topbar.addWidget(title)
        topbar.addStretch()
        
        # Window controls could go here
        
        self.content_layout.addLayout(topbar)

    def create_placeholder_page(self, title):
        page = QFrame()
        page.setObjectName("ContentPanel")
        layout = QVBoxLayout(page)
        
        label = QLabel(f"[{title}]")
        label.setStyleSheet("color: #333; font-size: 24px; font-weight: bold;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(label)
        return page

    def switch_page(self, index, sender_btn):
        self.page_stack.setCurrentIndex(index)
        for btn in self.nav_buttons:
            btn.setChecked(False)
        sender_btn.setChecked(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Load Theme
    theme_path = os.path.join(os.path.dirname(__file__), '../../assets/themes/cyberpunk.qss')
    if os.path.exists(theme_path):
        with open(theme_path, 'r') as f:
            app.setStyleSheet(f.read())
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
