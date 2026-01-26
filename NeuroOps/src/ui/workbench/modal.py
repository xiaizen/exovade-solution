from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QMessageBox, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem)
# ... imports ...
from PyQt6.QtCore import Qt, QUrl, QThread, QRectF
from PyQt6.QtGui import QPixmap, QImage

from .filmstrip import FilmstripTimeline
from src.core.video.worker import VideoWorker
from src.ui.graphics.overlay_box import OverlayBox

class PrecisionEditorModal(QDialog):
    def __init__(self, video_path, result_data=None, parent=None, initial_timestamp=0.0):
        super().__init__(parent)
        self.setWindowTitle("PRECISION EDITOR // WORKBENCH")
        self.resize(1000, 700)
        self.setStyleSheet("background-color: #121212; color: #EEE;")
        
        self.video_path = video_path
        self.initial_timestamp = initial_timestamp
        self.target_data = result_data # Store full result for bbox
        
        self.worker_thread = None
        self.worker = None
        self.video_item = None
        self.overlay_items = []
        
        self.setup_ui()
        self.setup_player()
        
        # Load filmstrip
        start_t = max(0, initial_timestamp - 5.0)
        self.filmstrip.load_video_segment(video_path, start_time=start_t, duration_sec=20.0)

    # ... setup_ui ... (unchanged)

    # ... setup_player ... (unchanged)

    def update_frame(self, qimage, timestamp):
        """Render frame from worker"""
        pixmap = QPixmap.fromImage(qimage)
        
        if not self.video_item:
            self.video_item = QGraphicsPixmapItem(pixmap)
            self.scene.addItem(self.video_item)
        else:
            self.video_item.setPixmap(pixmap)
            
        # Fit in view (maintain Aspect Ratio)
        self.view.fitInView(self.video_item, Qt.AspectRatioMode.KeepAspectRatio)
        
        # Draw Overlay if close to timestamp (Simple visual check)
        # In a real system, we'd query DB for detections at 'timestamp'
        # Here we just show the TARGET box if we are near the logical event
        self.draw_overlays(timestamp)

    def draw_overlays(self, current_time):
        # Clear old
        for item in self.overlay_items:
            self.scene.removeItem(item)
        self.overlay_items = []
        
        if not self.target_data:
            return
            
        # Check time window (show for 1 second duration around impact)
        # Note: 'timestamp' in data is a point.
        target_ts = self.target_data.get('timestamp', -1)
        if abs(current_time - target_ts) < 1.5:
            # Draw Box
            # Data format expected: normalized [x1, y1, x2, y2] or similar
            # For now, let's fake/hardcode or try to read 'bbox' if present
            bbox = self.target_data.get('bbox', [0.3, 0.3, 0.5, 0.6]) # Default dummy
            
            # Map normalized to pixels
            if self.video_item:
                pw = self.video_item.pixmap().width()
                ph = self.video_item.pixmap().height()
                
                # Assume [x_min, y_min, x_max, y_max] normalized
                x1, y1, x2, y2 = bbox
                rect = QRectF(x1 * pw, y1 * ph, (x2-x1)*pw, (y2-y1)*ph)
                
                ov = OverlayBox(rect, self.target_data.get('class_name', 'TARGET'), 
                                self.target_data.get('score', 0.99))
                self.scene.addItem(ov)
                self.overlay_items.append(ov)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel("EDIT SEARCH RESULT (PyAV ENGINE)"))
        layout.addLayout(header)
        
        # Video Player Area (QGraphicsView for future Overlays)
        self.view = QGraphicsView()
        self.view.setStyleSheet("border: 1px solid #333; background: #000;")
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.view.setMinimumHeight(400)
        layout.addWidget(self.view)
        
        # Filmstrip Area
        self.filmstrip = FilmstripTimeline()
        self.filmstrip.setFixedHeight(120)
        layout.addWidget(self.filmstrip)
        
        # Footer / Controls
        footer = QHBoxLayout()
        btn_save = QPushButton("SAVE CLIP")
        btn_save.setStyleSheet("background-color: #00FF88; color: #000; padding: 10px; font-weight: bold;")
        btn_save.clicked.connect(self.export_clip)
        
        btn_cancel = QPushButton("CANCEL")
        btn_cancel.setStyleSheet("border: 1px solid #555; padding: 10px;")
        btn_cancel.clicked.connect(self.reject)
        
        footer.addStretch()
        footer.addWidget(btn_cancel)
        footer.addWidget(btn_save)
        layout.addLayout(footer)

    def setup_player(self):
        # Thread Setup
        self.worker_thread = QThread()
        self.worker = VideoWorker(self.video_path)
        self.worker.moveToThread(self.worker_thread)
        
        # Connections
        self.worker.frame_ready.connect(self.update_frame)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        
        # Start
        self.worker_thread.start()
        
        # Initial Seek and Play
        self.worker.play()
        if self.initial_timestamp > 0:
            # Short delay to ensure decoder is ready (rudimentary)
            # Better approach: wait for metadata_ready signal.
            pass
            self.worker.seek(self.initial_timestamp)

    def update_frame(self, qimage, timestamp):
        """Render frame from worker"""
        pixmap = QPixmap.fromImage(qimage)
        
        if not self.video_item:
            self.video_item = QGraphicsPixmapItem(pixmap)
            self.scene.addItem(self.video_item)
        else:
            self.video_item.setPixmap(pixmap)
            
        # Fit in view (maintain Aspect Ratio)
        self.view.fitInView(self.video_item, Qt.AspectRatioMode.KeepAspectRatio)

    def export_clip(self):
        start, end = self.filmstrip.get_selection()
        duration = end - start
        
        if duration <= 0:
            return

        print(f"[EXPORT] Saving clip from {start:.2f} to {end:.2f}")
        
        # Construct output path
        base, ext = os.path.splitext(self.video_path)
        output_path = f"{base}_cut_{int(start)}_{int(end)}{ext}"
        
        # Resolve FFmpeg path dynamically
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        
        cmd = [
            ffmpeg_exe,
            '-y', # Overwrite
            '-ss', str(start),
            '-i', self.video_path,
            '-t', str(duration),
            '-c', 'copy',
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True)
            QMessageBox.information(self, "Export Success", f"Clip saved to:\n{output_path}")
            self.accept()
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Export Failed", f"FFmpeg Error:\n{e}")
        except FileNotFoundError:
             QMessageBox.critical(self, "Error", "FFmpeg not found in PATH.")

    def closeEvent(self, event):
        # Stop Worker
        if self.worker:
            self.worker.stop()
            
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()
        
        # Cleanup Filmstrip
        if self.filmstrip:
            self.filmstrip.cleanup()
            
        super().closeEvent(event)
