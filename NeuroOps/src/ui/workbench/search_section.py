from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QScrollArea, QPushButton, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap

from src.core.concurrency import ThreadController
from src.core.search_engine import SearchEngine
from src.ui.workbench.result_card import ResultCard

def execute_search_task(query, video_id, image_path=None):
    """
    Background search task.
    """
    engine = SearchEngine(collection_suffix=str(video_id)) 
    # TODO: Update Engine to support image path
    results = engine.search(query) 
    return results

class SearchSection(QWidget):
    """
    A self-contained search row.
    Displays the query query header and a horizontal scrollable list of results.
    """
    delete_requested = pyqtSignal()
    result_clicked = pyqtSignal(dict) # Relay card clicks up

    def __init__(self, query_text, video_id, image_path=None, parent=None):
        super().__init__(parent)
        self.query_text = query_text
        self.video_id = video_id
        self.image_path = image_path
        self.controller = None
        
        self.setup_ui()
        self.start_search()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 5, 0, 15)
        self.main_layout.setSpacing(10)
        
        # --- Header (Icon + Query + Delete) ---
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #222;
                border-radius: 6px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 8, 10, 8)
        
        # Icon / Image Preview
        if self.image_path:
            img_lbl = QLabel()
            pix = QPixmap(self.image_path)
            img_lbl.setPixmap(pix.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            img_lbl.setStyleSheet("background: #000; border: 1px solid #444; border-radius: 4px;")
            header_layout.addWidget(img_lbl)
        else:
            icon_lbl = QLabel("🔍") 
            icon_lbl.setStyleSheet("font-size: 16px; background: transparent;")
            header_layout.addWidget(icon_lbl)
        
        # Query Text
        disp_text = self.query_text if self.query_text else "[Image Query]"
        lbl_query = QLabel(disp_text)
        lbl_query.setStyleSheet("font-size: 14px; font-weight: bold; color: #EEE; background: transparent;")
        header_layout.addWidget(lbl_query)
        
        header_layout.addStretch()
        
        # Delete Button
        btn_del = QPushButton("✖")
        btn_del.setFixedSize(24, 24)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.clicked.connect(self.delete_requested.emit)
        btn_del.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #666;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #FF5555;
            }
        """)
        header_layout.addWidget(btn_del)
        
        self.main_layout.addWidget(header_frame)
        
        # --- Results Area (Horizontal Scroll) ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setFixedHeight(190) # Height of ResultCard (160) + margins
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:horizontal {
                height: 8px;
                background: #111;
            }
            QScrollBar::handle:horizontal {
                background: #444;
                border-radius: 4px;
            }
        """)
        
        self.results_container = QWidget()
        self.results_container.setStyleSheet("background: transparent;")
        self.results_layout = QHBoxLayout(self.results_container) # Horizontal!
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.results_layout.setContentsMargins(0,0,0,0)
        self.results_layout.setSpacing(10)
        
        self.scroll_area.setWidget(self.results_container)
        self.main_layout.addWidget(self.scroll_area)
        
        # Placeholder / Loading
        self.loading_lbl = QLabel("Searching...")
        self.loading_lbl.setStyleSheet("color: #666; margin-left: 10px; font-style: italic;")
        self.results_layout.addWidget(self.loading_lbl)

    def start_search(self):
        if self.video_id is None:
            self.show_error("No video context.")
            return

        self.controller = ThreadController(execute_search_task, self.query_text, self.video_id, self.image_path)
        self.controller.signals.result.connect(self.display_results)
        self.controller.start()

    def display_results(self, results):
        # Clear loading
        self.loading_lbl.deleteLater()
        
        if not results:
            lbl = QLabel("No matches found.")
            lbl.setStyleSheet("color: #666; margin-left: 10px;")
            self.results_layout.addWidget(lbl)
            return
            
        for res in results:
            card = ResultCard(res)
            # Add video_id to data for checking later
            res['video_id'] = self.video_id 
            card.clicked.connect(self.result_clicked.emit)
            self.results_layout.addWidget(card)
            
    def show_error(self, msg):
        self.loading_lbl.setText(msg)
        self.loading_lbl.setStyleSheet("color: #F55;")
