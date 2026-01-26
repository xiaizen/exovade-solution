from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QSlider, QLabel, QFileDialog, QStyle, QFrame, QSizePolicy)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import Qt, QUrl, QTime
from PyQt6.QtGui import QAction, QIcon, QFont
from src.ai.pipeline import VideoAnalysisWorker
from src.data.db_manager import DatabaseManager
from src.ui.workbench.filmstrip import FilmstripTimeline


class PlayerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # internal state
        self.duration = 0
        self.worker = None
        self.db_manager = DatabaseManager()
        self.is_playing = False
        
        # Search Result State
        self.current_search_result = None
        
        self.setup_ui()
        self.setup_player()
        
    def setup_player(self):
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        
        # Connect signals
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.playbackStateChanged.connect(self.media_state_changed)
        self.media_player.errorOccurred.connect(self.handle_errors)

    def setup_ui(self):
        # Main Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Video Area (Black Background)
        video_container = QFrame()
        video_container.setStyleSheet("background-color: #000; border-radius: 8px; border: 1px solid #333;")
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(1, 1, 1, 1) # Thin border
        
        self.video_widget = QVideoWidget()
        video_layout.addWidget(self.video_widget)
        
        layout.addWidget(video_container, stretch=1)

        # 2. Controls Area (Glassmorphism)
        controls = QFrame()
        controls.setObjectName("ContentPanel") # Reusing the glass panel style
        controls.setFixedHeight(220) # Increased height for new rows
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(15, 10, 15, 10)
        controls_layout.setSpacing(8)
        
        # --- ROW 1: Filmstrip Timeline ---
        self.timeline = FilmstripTimeline()
        self.timeline.setFixedHeight(95) # Approx 90px height
        controls_layout.addWidget(self.timeline)
        
        # Connect timeline range changes to labels
        # Note: We need to access the internal range item signal, or better, make FilmstripTimeline emit it.
        # For now, we'll assume FilmstripTimeline exposes the signal or we check it periodically? 
        # Actually, let's check filmstrip.py again. RangeGraphicsItem emits `rangeChanged`.
        # Implementing a bridge in update logic.
        
        # --- ROW 2: Time Controls & Search Info ---
        time_row = QHBoxLayout()
        
        # Start Label
        lbl_start = QLabel("Start")
        lbl_start.setStyleSheet("color: #888; font-size: 10px; font-weight: bold;")
        self.lbl_start_time = QLabel("00:00:00")
        self.lbl_start_time.setStyleSheet("background: #222; color: #EEE; padding: 4px 8px; border-radius: 4px; font-family: monospace;")
        
        # Search Result Info (Centered)
        self.lbl_search_info = QLabel("")
        self.lbl_search_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_search_info.setStyleSheet("color: #00FF88; font-weight: bold; font-size: 13px; letter-spacing: 1px;")
        
        # End Label
        lbl_end = QLabel("End")
        lbl_end.setStyleSheet("color: #888; font-size: 10px; font-weight: bold;")
        self.lbl_end_time = QLabel("00:00:00")
        self.lbl_end_time.setStyleSheet("background: #222; color: #EEE; padding: 4px 8px; border-radius: 4px; font-family: monospace;")

        time_row.addWidget(lbl_start)
        time_row.addWidget(self.lbl_start_time)
        time_row.addStretch()
        time_row.addWidget(self.lbl_search_info)
        time_row.addStretch()
        time_row.addWidget(lbl_end)
        time_row.addWidget(self.lbl_end_time)
        
        controls_layout.addLayout(time_row)
        
        # --- ROW 3: Playback Controls & Action Buttons ---
        action_row = QHBoxLayout()
        
        # Left Spacer to center playback controls
        
        # Open File Button
        self.btn_open = QPushButton("OPEN")
        self.btn_open.setFixedSize(60, 30)
        self.btn_open.setStyleSheet("background: #333; color: #AAA; border: 1px solid #444; border-radius: 4px; font-size: 10px; font-weight: bold;")
        self.btn_open.clicked.connect(self.open_file)
        action_row.addWidget(self.btn_open)

        action_row.addStretch()
        
        # Playback Controls (Rewind, Play, Forward)
        btn_rewind = QPushButton("◄◄")
        btn_rewind.setFixedSize(40, 30)
        btn_rewind.clicked.connect(lambda: self.seek_relative(-5000))
        
        self.btn_play = QPushButton()
        self.btn_play.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.btn_play.setFixedSize(40, 30)
        self.btn_play.clicked.connect(self.play_video)
        
        btn_forward = QPushButton("►►")
        btn_forward.setFixedSize(40, 30)
        btn_forward.clicked.connect(lambda: self.seek_relative(5000))

        # Current Time Label
        self.label_current_time = QLabel("00:00:00")
        self.label_current_time.setStyleSheet("color: #FFF; font-family: monospace; font-weight: bold; margin-left: 10px;")

        action_row.addWidget(btn_rewind)
        action_row.addWidget(self.btn_play)
        action_row.addWidget(btn_forward)
        action_row.addWidget(self.label_current_time)
        
        # Right aligned Action Buttons
        action_row.addStretch()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setFixedSize(80, 30)
        self.btn_cancel.setStyleSheet("background: transparent; color: #AAA; border: 1px solid #444; border-radius: 15px;")
        
        self.btn_save = QPushButton("Save")
        self.btn_save.setFixedSize(80, 30)
        self.btn_save.setStyleSheet("background: #007ACC; color: white; border-radius: 15px; font-weight: bold;")
        self.btn_save.clicked.connect(self.handle_save)

        action_row.addWidget(self.btn_cancel)
        action_row.addWidget(self.btn_save)
        
        controls_layout.addLayout(action_row)
        
        layout.addWidget(controls)
        
        # Timer for Timeline Sync (since we need to poll RangeItem if we don't hook signals directly)
        # Or better, hook signal in load_video
        
    def open_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilters(["Video files (*.mp4 *.avi *.mkv *.mov)", "All files (*)"])
        if file_dialog.exec():
            files = file_dialog.selectedFiles()
            if files:
                self.load_video(files[0])

    def load_video(self, file_path, analyze=True):
        self.media_player.setSource(QUrl.fromLocalFile(file_path))
        self.btn_play.setEnabled(True)
        self.play_video()
        
        # Load Timeline
        # For now, load first 60 seconds or full video if short?
        # Ideally, we should wait for durationChanged to know total duration.
        # But we can pass duration=600 for now or handle it in duration_changed
        self.current_video_path = file_path
        
        # Start AI Analysis in Background
        if analyze:
            self.start_analysis(file_path)

    def load_search_result(self, file_path, timestamp, metadata):
        """
        Loads video centered on timestamp with metadata display.
        """
        self.load_video(file_path, analyze=False) # Do not re-analyze search results
        
        # Wait for duration (async) - logic simpler here:
        # Seek to timestamp
        self.media_player.setPosition(int(timestamp * 1000))
        
        # Setup Timeline
        start_sec = max(0, timestamp - 15)
        self.timeline.load_video_segment(file_path, start_time=start_sec, duration_sec=30)
        
        # Connect Range Changed Signal
        if self.timeline.range_item:
            self.timeline.range_item.rangeChanged.connect(self.handle_range_changed)
            
        # Update Meta
        if metadata:
            cls_name = metadata.get('class_name', 'Unknown').upper()
            score = metadata.get('score', 0.0)
            self.lbl_search_info.setText(f"{cls_name} ({score:.2f})")
        else:
            self.lbl_search_info.setText("")

    def start_analysis(self, file_path):
        import os
        filename = os.path.basename(file_path)
        # Register video in DB
        video_id = self.db_manager.add_video(file_path, filename)
        if video_id:
            print(f"Starting Worker for Video ID: {video_id}")
            
            # Clear previous detections (SQL)
            self.db_manager.clear_detections_for_video(video_id)
            
            # Clear previous embeddings (Vector DB)
            from src.data.vector_store import VectorStore
            VectorStore(collection_suffix=str(video_id)).clear_collection()
            
            self.worker = VideoAnalysisWorker(file_path, video_id)
            self.worker.log_message.connect(lambda msg: print(f"[WORKER]: {msg}"))
            
            # Connect to MainWindow Dashboard if possible (Quick dirty way, ideal is EventBus)
            main_window = self.window()
            from ui.main_window import MainWindow
            if isinstance(main_window, MainWindow):
                 # Reset and Link Dashboard
                 try:
                    main_window.dashboard_widget.set_video(video_id, filename)
                    main_window.search_widget.set_active_video(video_id)
                    
                    self.worker.alert_triggered.connect(main_window.dashboard_widget.add_alert)
                    self.worker.stats_update.connect(main_window.dashboard_widget.handle_stats_update)
                 except AttributeError:
                     pass
            
            self.worker.start()

    def play_video(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def seek_relative(self, delta_ms):
        pos = self.media_player.position()
        self.media_player.setPosition(max(0, pos + delta_ms))

    def media_state_changed(self, state):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.btn_play.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
        else:
            self.btn_play.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))

    def position_changed(self, position):
        self.update_duration_label(position)
        # Sync playhead on timeline (if we had one)

    def duration_changed(self, duration):
        self.duration = duration
        self.update_duration_label(0)
        
        # Initial Timeline Load (Whole video if no search result)
        if hasattr(self, 'current_video_path') and self.current_video_path:
             # Just load first 60s for perf demo
             self.timeline.load_video_segment(self.current_video_path, start_time=0.0, duration_sec=60.0)
             # Hook signal
             if self.timeline.range_item:
                 self.timeline.range_item.rangeChanged.connect(self.handle_range_changed)
                 # Trigger initial label update
                 self.handle_range_changed(0.25, 0.75) # defaults

    def handle_range_changed(self, start_ratio, end_ratio):
        # We need to get actual seconds from timeline
        s_sec, e_sec = self.timeline.get_selection()
        self.lbl_start_time.setText(self.format_time(int(s_sec * 1000)))
        self.lbl_end_time.setText(self.format_time(int(e_sec * 1000)))

    def format_time(self, ms):
        seconds = (ms // 1000) % 60
        minutes = (ms // 60000) % 60
        hours = (ms // 3600000)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def update_duration_label(self, current_ms):
        self.label_current_time.setText(self.format_time(current_ms))

    def handle_errors(self):
        self.btn_play.setEnabled(False)
        err_msg = self.media_player.errorString()
        print(f"Error: {err_msg}")
        
    def handle_save(self):
        s_sec, e_sec = self.timeline.get_selection()
        print(f"SAVE REQUESTED: {s_sec:.2f} to {e_sec:.2f}")
        # Logic to save clip would go here
