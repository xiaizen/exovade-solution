from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QScrollArea, QLabel, QFrame, QFileDialog)
from PyQt6.QtCore import Qt, pyqtSignal

from src.data.db_manager import DatabaseManager
from src.data.db_manager import DatabaseManager
from src.ui.workbench.search_section import SearchSection

class SearchWidget(QWidget):
    jump_to_timestamp = pyqtSignal(int, float) # video_id, timestamp
    search_result_selected = pyqtSignal(dict) # result_data (includes video_id, timestamp, etc)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_video_id = None 
        self.db = DatabaseManager()
        self.sections = [] 
        self.selected_image_path = None # Store ref image
        self.setup_ui()

    def set_active_video(self, video_id):
        self.current_video_id = video_id
        print(f"[SEARCH] Active Video Context set to: {video_id}")
        self.clear_all_sections() # Wipe UI on new video load

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("NEURAL_SEARCH //")
        header.setObjectName("Header")
        layout.addWidget(header)
        
        # Search Bar (New Query Creator)
        search_row = QHBoxLayout()
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Add a new query (e.g. 'red car')...")
        self.input_search.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                border: none;
                border-radius: 4px;
                padding: 10px;
                color: #fff;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: none;
            }
        """)
        self.input_search.returnPressed.connect(self.add_query_section)
        search_row.addWidget(self.input_search)
        
        # Image Reference Button
        self.btn_img = QPushButton("IMG")
        self.btn_img.setFixedSize(40, 40)
        self.btn_img.setStyleSheet("""
            QPushButton {
                background-color: #222;
                border: none;
                border-radius: 4px;
                color: #aaa;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                border-color: #00FF88;
                color: #00FF88;
            }
        """)
        self.btn_img.clicked.connect(self.select_reference_image)
        search_row.addWidget(self.btn_img)
        
        # Add Button (Simplified)
        btn_add = QPushButton("+")
        btn_add.setFixedSize(40, 40)
        btn_add.setStyleSheet("""
            QPushButton {
                background-color: #00FF88;
                border: none;
                border-radius: 4px;
                color: #000;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00CC66;
            }
        """)
        btn_add.clicked.connect(self.add_query_section)
        search_row.addWidget(btn_add)
        
        layout.addLayout(search_row)
        
        # ... (rest of setup_ui) ...
        # Sections Container (Vertical Scroll)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.sections_container = QWidget()
        self.sections_layout = QVBoxLayout(self.sections_container)
        self.sections_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.sections_layout.setSpacing(10)
        
        self.scroll.setWidget(self.sections_container)
        layout.addWidget(self.scroll)

    def select_reference_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Reference Image", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.selected_image_path = path
            self.btn_img.setStyleSheet("background-color: #00FF88; color: #000; border: none;")
            self.btn_img.setText("✔")
            print(f"[SEARCH] Reference Image Selected: {path}")

    def add_query_section(self):
        if self.current_video_id is None:
            # ... (existing check) ...
            if self.sections_layout.count() == 0:
                 lbl = QLabel("Please upload a video to start searching.")
                 lbl.setStyleSheet("color: #FF5555; font-weight: bold; padding: 20px;")
                 self.sections_layout.addWidget(lbl)
            return

        query = self.input_search.text().strip()
        # Allow empty text if image is selected
        if not query and not self.selected_image_path:
            return

        # Clear any initial warning labels
        for i in reversed(range(self.sections_layout.count())):
            item = self.sections_layout.itemAt(i)
            if item.widget() and isinstance(item.widget(), QLabel):
                item.widget().deleteLater()

        # Create Section
        section = SearchSection(query, self.current_video_id, image_path=self.selected_image_path)
        section.result_clicked.connect(self.handle_result_click)
        section.delete_requested.connect(lambda: self.remove_section(section))
        
        self.sections_layout.insertWidget(0, section) # Add to top
        self.sections.append(section)
        
        # Reset Input
        self.input_search.clear()
        self.selected_image_path = None
        self.btn_img.setText("IMG")
        self.btn_img.setStyleSheet("""
            QPushButton {
                background-color: #222;
                border: none;
                border-radius: 4px;
                color: #aaa;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                border-color: #00FF88;
                color: #00FF88;
            }
        """)

    def remove_section(self, section):
        if section in self.sections:
            self.sections.remove(section)
            section.deleteLater()

    def clear_all_sections(self):
        for s in self.sections:
            s.deleteLater()
        self.sections = []
        
        # Clear layout explicitly just in case
        while self.sections_layout.count():
            child = self.sections_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.input_search.clear()

    def handle_result_click(self, data):
        # Emit signal to Main Window to handle in Player
        print(f"[SEARCH] Result Clicked: {data}")
        self.search_result_selected.emit(data)
