from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, 
    QCheckBox, QPushButton, QSlider, QScrollArea, QFrame, QGroupBox, 
    QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QImage, QPixmap
import cv2
import time

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    connection_status_signal = pyqtSignal(bool, str)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self._run_flag = True

    def run(self):
        # Attempt to open the stream
        cap = cv2.VideoCapture(self.url)
        
        if not cap.isOpened():
            self.connection_status_signal.emit(False, "Failed to connect to stream URL.")
            return
        
        # Read one frame to confirm
        ret, frame = cap.read()
        if not ret:
            self.connection_status_signal.emit(False, "Connected, but no frames received.")
            cap.release()
            return

        self.connection_status_signal.emit(True, "Connection Successful!")

        while self._run_flag:
            ret, frame = cap.read()
            if ret:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                p = convert_to_Qt_format.scaled(640, 360, Qt.AspectRatioMode.KeepAspectRatio)
                self.change_pixmap_signal.emit(p)
            else:
                # If stream drops, try to reconnect or just stop? For preview, we stop.
                break
            
            # Limit fps to ~30 for preview to save resources
            time.sleep(0.03) 
            
        cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()

class CamerasWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.video_thread = None
        self.init_ui()

    def init_ui(self):
        # Main Layout (Scrollable)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(20)
        
        # --- Header ---
        header_label = QLabel("Add Camera / Camera Setup")
        header_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #E0E0E0;")
        self.content_layout.addWidget(header_label)
        
        sub_header = QLabel("Configure secure IP CCTV connection, test live stream, and enable AI monitoring.")
        sub_header.setStyleSheet("font-size: 14px; color: #888;")
        self.content_layout.addWidget(sub_header)
        
        # --- 1. Basic Information ---
        self.setup_basic_info()
        
        # --- 2. Connection Settings ---
        self.setup_connection_settings()
        
        # --- 3. Preview ---
        self.setup_preview()
        
        # --- 4. Recording Settings ---
        self.setup_recording_settings()
        
        # --- 5. AI Detection ---
        self.setup_ai_settings()
        
        # --- 6. Permissions ---
        self.setup_permissions()
        
        # --- Footer Actions ---
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedSize(120, 40)
        btn_cancel.setStyleSheet("background-color: transparent; border: 1px solid #444; color: #AAA;")
        btn_cancel.clicked.connect(self.stop_stream) # Stop stream on cancel
        
        btn_save = QPushButton("Save Camera")
        btn_save.setFixedSize(150, 40)
        btn_save.setStyleSheet("background-color: #007BFF; color: white; border: none; font-weight: bold;")
        btn_save.clicked.connect(self.save_camera)
        
        footer_layout.addWidget(btn_cancel)
        footer_layout.addWidget(btn_save)
        self.content_layout.addLayout(footer_layout)
        
        # Finish Setup
        self.content_layout.addStretch()
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def setup_basic_info(self):
        group = self.create_section("Camera Basic Information")
        layout = group.layout()
        
        # Grid for Name/Location
        row1 = QHBoxLayout()
        
        self.entry_name = self.create_input_field("Camera Name", "Entrance Gate Camera")
        row1.addLayout(self.entry_name)
        
        self.entry_location = self.create_input_field("Location Name", "Warehouse A - North Side")
        row1.addLayout(self.entry_location)
        
        layout.addLayout(row1)
        
        # Category
        self.combo_category = self.create_combo_field("Category", ["Indoor", "Outdoor", "Parking", "Entrance", "Restricted Area"])
        layout.addLayout(self.combo_category)
        
        self.content_layout.addWidget(group)

    def setup_connection_settings(self):
        group = self.create_section("Connection Settings")
        layout = group.layout()
        
        # Protocol / IP / Port
        row1 = QHBoxLayout()
        
        self.combo_protocol = self.create_combo_field("Protocol", ["RTSP", "HTTP", "HTTPS"])
        # Make protocol smaller
        self.combo_protocol.itemAt(1).widget().setFixedWidth(80) 
        row1.addLayout(self.combo_protocol)
        
        self.field_ip = self.create_input_field("IP Address / Domain", "192.168.1.50")
        row1.addLayout(self.field_ip)
        
        self.field_port = self.create_input_field("Port", "554")
        row1.addLayout(self.field_port)
        
        layout.addLayout(row1)
        
        row2 = QHBoxLayout()
        self.field_user = self.create_input_field("Username", "admin")
        row2.addLayout(self.field_user)
        
        pass_layout = QVBoxLayout()
        pass_lbl = QLabel("Password")
        pass_lbl.setStyleSheet("color: #AAA;")
        self.entry_pass = QLineEdit()
        self.entry_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.entry_pass.setStyleSheet("padding: 8px; background: #111; border: 1px solid #333; color: white;")
        pass_layout.addWidget(pass_lbl)
        pass_layout.addWidget(self.entry_pass)
        row2.addLayout(pass_layout)
        
        layout.addLayout(row2)
        
        self.field_path = self.create_input_field("Stream Path", "/stream1")
        layout.addLayout(self.field_path)
        
        # Buttons
        btn_row = QHBoxLayout()
        
        # ONVIF Toggle
        self.chk_onvif = QCheckBox("Enable ONVIF")
        self.chk_onvif.setStyleSheet("""
            QCheckBox { color: #AAA; spacing: 5px; }
            QCheckBox::indicator { width: 40px; height: 20px; border-radius: 10px; background: #333; }
            QCheckBox::indicator:checked { background: #238636; }
        """)
        
        btn_row.addWidget(self.chk_onvif)
        btn_row.addStretch()
        
        self.btn_test = QPushButton("Test Connection")
        self.btn_test.setStyleSheet("padding: 8px 16px; background: #007BFF; color: white; border: none;")
        self.btn_test.clicked.connect(self.test_connection)
        
        btn_row.addWidget(self.btn_test)
        layout.addLayout(btn_row)
        
        self.content_layout.addWidget(group)

    def setup_preview(self):
        group = self.create_section("Live Stream Preview")
        layout = group.layout()
        
        self.preview_frame = QFrame()
        self.preview_frame.setMinimumHeight(400)
        self.preview_frame.setStyleSheet("background-color: black; border: 1px solid #333;")
        
        # Layout for the preview frame
        self.preview_layout = QVBoxLayout(self.preview_frame)
        self.preview_layout.setContentsMargins(0,0,0,0)
        
        # Actual display label
        self.preview_label = QLabel("Live Stream Preview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("color: #555;")
        self.preview_layout.addWidget(self.preview_label)
        
        layout.addWidget(self.preview_frame)
        self.content_layout.addWidget(group)

    def setup_recording_settings(self):
        group = self.create_section("Recording Settings")
        layout = group.layout()
        
        row1 = QHBoxLayout()
        row1.addLayout(self.create_combo_field("Recording Mode", ["Continuous", "Event-Based Only"]))
        row1.addLayout(self.create_combo_field("Resolution Limit", ["Auto", "720p", "1080p"]))
        layout.addLayout(row1)
        
        # FPS Slider
        fps_layout = QVBoxLayout()
        fps_header = QHBoxLayout()
        fps_lbl = QLabel("FPS Limit")
        fps_lbl.setStyleSheet("color: #AAA;")
        self.fps_val_lbl = QLabel("15")
        self.fps_val_lbl.setStyleSheet("color: #007BFF; font-weight: bold;")
        fps_header.addWidget(fps_lbl)
        fps_header.addStretch()
        fps_header.addWidget(self.fps_val_lbl)
        
        self.fps_slider = QSlider(Qt.Orientation.Horizontal)
        self.fps_slider.setRange(1, 30)
        self.fps_slider.setValue(15)
        self.fps_slider.valueChanged.connect(lambda v: self.fps_val_lbl.setText(str(v)))
        
        fps_layout.addLayout(fps_header)
        fps_layout.addWidget(self.fps_slider)
        
        layout.addLayout(fps_layout)
        self.content_layout.addWidget(group)

    def setup_ai_settings(self):
        group = self.create_section("AI Detection Settings")
        layout = group.layout()
        
        self.chk_ai = QCheckBox("Enable AI Detection")
        self.chk_ai.setStyleSheet("color: #E0E0E0; font-size: 14px;")
        layout.addWidget(self.chk_ai)
        
        # Detection Types (Multi-select simulation via Checkboxes)
        det_lbl = QLabel("Detection Types")
        det_lbl.setStyleSheet("color: #AAA; margin-top: 10px;")
        layout.addWidget(det_lbl)
        
        types_layout = QHBoxLayout()
        for t in ["Person", "Vehicle", "Motion", "Intrusion Zone"]:
            types_layout.addWidget(QCheckBox(t))
        types_layout.addStretch()
        layout.addLayout(types_layout)
        
        self.content_layout.addWidget(group)

    def setup_permissions(self):
        group = self.create_section("Permissions & Access Control")
        layout = group.layout()
        
        row1 = QHBoxLayout()
        row1.addLayout(self.create_combo_field("Who can view this camera?", ["Admin Only", "Security Team", "All Staff"]))
        row1.addLayout(self.create_combo_field("Who can download recordings?", ["Admin Only", "Security Managers"]))
        layout.addLayout(row1)
        
        self.content_layout.addWidget(group)

    # --- Helpers ---
    def create_section(self, title):
        group = QFrame()
        group.setStyleSheet("background-color: #1A1A1A; border-radius: 8px;")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(20, 20, 20, 20)
        
        lbl = QLabel(title)
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFF; border-bottom: 1px solid #333; padding-bottom: 10px;")
        layout.addWidget(lbl)
        layout.addSpacing(10)
        
        return group
    
    # Helper to retrieve text from the layout wrapper I created
    def get_input_text(self, layout):
        # Index 1 is the QLineEdit (0 is Label)
        widget = layout.itemAt(1).widget()
        if isinstance(widget, QLineEdit):
            return widget.text()
        return ""

    def create_input_field(self, label_text, placeholder=""):
        layout = QVBoxLayout()
        lbl = QLabel(label_text)
        lbl.setStyleSheet("color: #AAA;")
        entry = QLineEdit()
        entry.setPlaceholderText(placeholder)
        entry.setStyleSheet("padding: 8px; background: #111; border: 1px solid #333; color: white;")
        layout.addWidget(lbl)
        layout.addWidget(entry)
        return layout

    def create_combo_field(self, label_text, options):
        layout = QVBoxLayout()
        lbl = QLabel(label_text)
        lbl.setStyleSheet("color: #AAA;")
        combo = QComboBox()
        combo.addItems(options)
        combo.setStyleSheet("padding: 8px; background: #111; border: 1px solid #333; color: white;")
        layout.addWidget(lbl)
        layout.addWidget(combo)
        return layout

    # --- Actions ---
    def test_connection(self):
        # 1. Gather Info
        protocol = self.combo_protocol.itemAt(1).widget().currentText().lower()
        ip = self.get_input_text(self.field_ip).strip()
        port = self.get_input_text(self.field_port).strip()
        username = self.get_input_text(self.field_user).strip()
        password = self.entry_pass.text().strip()
        path = self.get_input_text(self.field_path).strip()
        
        if not ip:
            QMessageBox.warning(self, "Missing Info", "Please enter at least an IP address.")
            return

        # 2. Construct URL
        # Logic: If 'ip' already has a port, don't append the 'Port' field.
        final_ip = ip
        final_port = port
        
        if ":" in ip:
            pass # IP has port
        else:
            if final_port:
                final_ip = f"{final_ip}:{final_port}"

        # Construction
        if "://" in final_ip:
             # User pasted full URL
             url = final_ip
        else:
            auth_part = f"{username}:{password}@" if username and password else ""
            
            # Ensure path starts with /
            if path and not path.startswith("/"):
                path = "/" + path
                
            url = f"{protocol}://{auth_part}{final_ip}{path}"
            
        print(f"Testing Stream URL: {url}")
        
        self.btn_test.setText("Connecting...")
        self.btn_test.setEnabled(False)
        
        # 3. Start Video Thread
        self.video_thread = VideoThread(url)
        self.video_thread.connection_status_signal.connect(self.on_connection_status)
        self.video_thread.change_pixmap_signal.connect(self.update_preview_image)
        self.video_thread.start()

    def on_connection_status(self, success, message):
        self.btn_test.setEnabled(True)
        if success:
            self.btn_test.setText("Connected")
            self.btn_test.setStyleSheet("padding: 8px 16px; background: #238636; color: white; border: none;")
        else:
            self.btn_test.setText("Test Connection")
            self.btn_test.setStyleSheet("padding: 8px 16px; background: #B00020; color: white; border: none;")
            QMessageBox.warning(self, "Connection Failed", f"{message}\n\nPlease check usage:\n- IP Webcam: try including port 8080 (e.g., 192.168.1.50:8080) and path /video or /h264\n- ONVIF: ensure port is correct (often 554 or 80)")

    def update_preview_image(self, qt_image):
        self.preview_label.setPixmap(QPixmap.fromImage(qt_image))
        self.preview_label.setText("") # Clear text once video starts

    def stop_stream(self):
        if self.video_thread:
            self.video_thread.stop()
            self.video_thread = None
            self.preview_label.setText("Stream Stopped")
            self.btn_test.setText("Test Connection")
            self.btn_test.setStyleSheet("padding: 8px 16px; background: #007BFF; color: white; border: none;")

    def save_camera(self):
        self.stop_stream()
        QMessageBox.information(self, "Success", "Camera saved successfully to the system.")
    
    def closeEvent(self, event):
        self.stop_stream()
        event.accept()
