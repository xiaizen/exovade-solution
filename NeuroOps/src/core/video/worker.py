from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread, QMutex
from PyQt6.QtGui import QImage
import time
from .decoder import VideoDecoder

class VideoWorker(QObject):
    """
    Manages the video decoding loop in a background thread.
    Emits frame_ready signals for the GUI to render.
    """
    frame_ready = pyqtSignal(QImage, float) # Image, Timestamp (sec)
    metadata_ready = pyqtSignal(dict)
    finished = pyqtSignal()
    
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.decoder = None
        
        # State
        self.is_playing = False
        self.stop_requested = False
        self.seek_requested = None # Timestamp to seek to
        
        self.mutex = QMutex()
        
    def run(self):
        """Main Thread Loop"""
        try:
            self.decoder = VideoDecoder(self.file_path)
            self.metadata_ready.emit(self.decoder.get_metadata())
            
            frame_gen = self.decoder.decode_frames()
            
            while not self.stop_requested:
                
                # Check Seek
                if self.seek_requested is not None:
                    self.mutex.lock()
                    ts = self.seek_requested
                    self.seek_requested = None
                    self.mutex.unlock()
                    
                    self.decoder.seek(ts)
                    frame_gen = self.decoder.decode_frames() # Reset generator
                    
                if not self.is_playing:
                    time.sleep(0.01) # Idle wait
                    continue
                    
                try:
                    # Get Next Frame
                    frame, timestamp = next(frame_gen)
                    
                    # Pace Control (Simple Sleep - Production needs Audio Sync or QElapsedTimer)
                    # For "Workbench" trimming, visual scanning speed is often preferred over realtime audio sync.
                    # We will implement a basic FPS limiter.
                    target_delay = 1.0 / self.decoder.fps
                    time.sleep(target_delay * 0.9) # Slightly faster processing, let GUI catch up
                    
                    self.frame_ready.emit(frame, timestamp)
                    
                except StopIteration:
                    self.is_playing = False
                    # End of stream
                    
        except Exception as e:
            print(f"[WORKER] Critical Error: {e}")
        finally:
            if self.decoder:
                self.decoder.close()
            self.finished.emit()

    def play(self):
        self.is_playing = True
        
    def pause(self):
        self.is_playing = False
        
    def seek(self, timestamp):
        self.mutex.lock()
        self.seek_requested = timestamp
        self.mutex.unlock()
        
    def stop(self):
        self.stop_requested = True
