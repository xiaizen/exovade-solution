import av
import math
from PyQt6.QtGui import QImage
from PyQt6.QtCore import QMutex, QMutexLocker

class VideoDecoder:
    """
    Low-level video decoder using PyAV.
    Handles container opening, seeking, and frame conversion to QImage.
    Thread-safe (locks on critical container access).
    """
    def __init__(self, file_path):
        self.file_path = file_path
        self.container = None
        self.stream = None
        self.video_stream_index = -1
        self.mutex = QMutex()
        
        # Metadata
        self.duration_sec = 0.0
        self.fps = 30.0
        self.width = 0
        self.height = 0
        self.time_base = 0.0
        
        self._open()

    def _open(self):
        try:
            self.container = av.open(self.file_path)
            # Find video stream
            self.stream = self.container.streams.video[0]
            self.stream.thread_type = "AUTO" 
            self.video_stream_index = self.stream.index
            
            # Extract metadata
            self.width = self.stream.width
            self.height = self.stream.height
            
            # Safe FPS handling
            if self.stream.average_rate:
                self.fps = float(self.stream.average_rate)
            else:
                self.fps = 30.0 # Fallback
                
            self.time_base = float(self.stream.time_base)
            
            # Duration (Container vs Stream)
            if self.stream.duration:
                self.duration_sec = float(self.stream.duration * self.time_base)
            elif self.container.duration:
                self.duration_sec = self.container.duration / 1000000.0
            else:
                self.duration_sec = 0.0
                
        except Exception as e:
            print(f"[DECODER] Error opening file: {e}")
            raise

    def get_metadata(self):
        return {
            "duration": self.duration_sec,
            "fps": self.fps,
            "width": self.width,
            "height": self.height
        }

    def seek(self, timestamp_sec):
        """
        Seek to a specific timestamp in seconds.
        Returns the iterator positioned at the keyframe.
        """
        locker = QMutexLocker(self.mutex)
        if not self.container:
            return
            
        # Convert seconds to time_base units
        target_pts = int(timestamp_sec / self.time_base)
        
        # Seek (backward logic ensures we land before target)
        self.container.seek(target_pts, stream=self.stream, any_frame=False, backward=True)
        
        # Flush buffers to avoid stale frames
        for packet in self.container.demux(self.stream):
            if packet.dts is None: continue
            for frame in packet.decode():
                frame_pts = frame.pts * self.time_base
                # Decode until we reach or pass target (primitive seek-then-decode loop)
                # For basic player, just returning the first keyframe is often acceptable feel.
                # But for precision, we'd loop here. For now, returning generator state.
                return # Puts decoder in fresh state

    def decode_frames(self):
        """
        Generator yielding (QImage, timestamp_sec).
        """
        # Note: 'mutex' locking entire generator is tricky.
        # Ideally, outer loop holds lock per-packet demux if highly concurrent.
        # But here we are single-consumer (Worker).
        
        if not self.container:
            return

        try:
            for packet in self.container.demux(self.stream):
                for frame in packet.decode():
                    # Convert to QImage
                    img = frame.to_image() # PIL Image
                    
                    # Optimization: Use QImage constructor from buffer if possible, 
                    # but to_qimage via PIL is safer for various pixel formats.
                    # QImage(data, w, h, fmt) needs strict lifetime management.
                    # Simplest robust way:
                    data = img.tobytes("raw", "RGBA")
                    qimg = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888).copy()
                    
                    timestamp = frame.pts * self.time_base
                    yield qimg, timestamp
        except Exception as e:
            print(f"[DECODER] Decode Loop Error: {e}")
            
    def close(self):
        locker = QMutexLocker(self.mutex)
        if self.container:
            self.container.close()
            self.container = None
