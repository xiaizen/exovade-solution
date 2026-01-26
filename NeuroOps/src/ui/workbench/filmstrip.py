import sys
import av
import numpy as np
from PyQt6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, 
                             QGraphicsObject, QApplication, QWidget, QVBoxLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QPixmap, QImage, QColor, QPen, QBrush, QPainter, QPainterPath

# -----------------------------------------------------------------------------
# WORKER: Extracts Thumbnails (Optimized for Segments)
# -----------------------------------------------------------------------------
class ThumbnailWorker(QThread):
    thumbnail_ready = pyqtSignal(int, QImage) # index, image
    
    def __init__(self, file_path, start_time=0.0, end_time=None, interval=1.0, width=160, height=90):
        super().__init__()
        self.file_path = file_path
        self.start_time = start_time
        self.end_time = end_time
        self.interval = interval
        self.thumb_w = width
        self.thumb_h = height
        self._is_running = True
        
    def run(self):
        try:
            container = av.open(self.file_path)
            stream = container.streams.video[0]
            stream.thread_type = 'AUTO'
            
            duration = float(stream.duration * stream.time_base)
            final_end = self.end_time if self.end_time else duration
            if final_end > duration: final_end = duration
            
            # Iterate
            for i, time_sec in enumerate(np.arange(self.start_time, final_end, self.interval)):
                if not self._is_running: break
                
                timestamp = int(time_sec / stream.time_base)
                container.seek(timestamp, stream=stream)
                
                for frame in container.decode(stream):
                    img = frame.to_image()
                    img = img.resize((self.thumb_w, self.thumb_h))
                    data = img.tobytes("raw", "RGB")
                    qimg = QImage(data, img.width, img.height, QImage.Format.Format_RGB888)
                    self.thumbnail_ready.emit(i, qimg)
                    break 
        except Exception as e:
            print(f"[THUMBNAIL] Error: {e}")

    def stop(self):
        self._is_running = False

# -----------------------------------------------------------------------------
# GRAPHICS ITEM: The "Blue Box" Selector via Handles + Scrim
# -----------------------------------------------------------------------------
class RangeGraphicsItem(QGraphicsObject):
    rangeChanged = pyqtSignal(float, float) # start_ratio, end_ratio (0.0 to 1.0)
    
    def __init__(self, height, scene_width):
        super().__init__()
        self.h = height
        self.scene_w = scene_width
        
        # Selection state (in pixels)
        # Default: Select middle 50%
        self.left_x = self.scene_w * 0.25
        self.right_x = self.scene_w * 0.75
        self.min_width = 20
        
        # Interaction state
        self.dragging_left = False
        self.dragging_right = False
        self.dragging_body = False
        self.drag_start_x = 0
        self.handle_width = 12
        
        self.setAcceptHoverEvents(True)
        # We handle mouse events manually for complex interaction
        
    def boundingRect(self):
        # We cover the full scene width because we draw the "scrim" (dimmer) outside selection
        return QRectF(0, 0, self.scene_w, self.h)
        
    def shape(self):
        # Hit test shape: clearly interactive parts + scrim
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def paint(self, painter, option, widget):
        # 1. Scrim (Dimmed Areas)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 180)) # Darker scrim
        
        # Left Scrim
        painter.drawRect(QRectF(0, 0, self.left_x, self.h))
        # Right Scrim
        painter.drawRect(QRectF(self.right_x, 0, self.scene_w - self.right_x, self.h))
        
        # 2. Selection Border (Blue Box)
        selection_rect = QRectF(self.left_x, 0, self.right_x - self.left_x, self.h)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        pen = QPen(QColor("#00FF88"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(QPointF(self.left_x, 0), QPointF(self.right_x, 0)) # Top line
        painter.drawLine(QPointF(self.left_x, self.h), QPointF(self.right_x, self.h)) # Bottom line
        
        # 3. Handles (Thick bars)
        handle_color = QColor("#00FF88")
        painter.setBrush(handle_color)
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Left Handle
        painter.drawRect(QRectF(self.left_x, 0, 4, self.h))
        # Right Handle
        painter.drawRect(QRectF(self.right_x - 4, 0, 4, self.h))

    # --- Interaction Logic ---
    
    def mousePressEvent(self, event):
        pos = event.pos()
        x = pos.x()
        
        # Hit test handles with tolerance
        if abs(x - self.left_x) < self.handle_width:
            self.dragging_left = True
        elif abs(x - self.right_x) < self.handle_width:
            self.dragging_right = True
        elif self.left_x < x < self.right_x:
            self.dragging_body = True
            self.drag_start_x = x
            self.initial_left = self.left_x
            self.initial_right = self.right_x
            
        event.accept()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        x = pos.x()
        
        if self.dragging_left:
            self.left_x = min(max(0, x), self.right_x - self.min_width)
            self.update()
        elif self.dragging_right:
            self.right_x = max(min(self.scene_w, x), self.left_x + self.min_width)
            self.update()
        elif self.dragging_body:
            delta = x - self.drag_start_x
            width = self.initial_right - self.initial_left
            
            # Proposed positions
            new_left = self.initial_left + delta
            new_right = self.initial_right + delta
            
            # Clamp
            if new_left < 0:
                new_left = 0
                new_right = width
            if new_right > self.scene_w:
                new_right = self.scene_w
                new_left = self.scene_w - width
                
            self.left_x = new_left
            self.right_x = new_right
            self.update()
            
        if self.dragging_left or self.dragging_right or self.dragging_body:
             # Emit normalized range
             self.rangeChanged.emit(self.left_x / self.scene_w, self.right_x / self.scene_w)

    def mouseReleaseEvent(self, event):
        self.dragging_left = False
        self.dragging_right = False
        self.dragging_body = False
        super().mouseReleaseEvent(event)
        
    def hoverMoveEvent(self, event):
        pos = event.pos()
        x = pos.x()
        
        if abs(x - self.left_x) < self.handle_width or abs(x - self.right_x) < self.handle_width:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif self.left_x < x < self.right_x:
             self.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().hoverMoveEvent(event)

# -----------------------------------------------------------------------------
# MAIN VIEW: FilmstripTimeline (QGraphicsView)
# -----------------------------------------------------------------------------
class FilmstripTimeline(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Appearance
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("background: #101010; border: none;")
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        
        # State
        self.thumb_w = 160
        self.thumb_h = 90
        self.worker = None
        self.range_item = None
        
        # Data
        self.worker_start_time = 0.0
        self.worker_duration = 0.0

    def load_video_segment(self, file_path, start_time, duration_sec=10.0):
        self.scene.clear()
        self.range_item = None
        self.worker_start_time = max(0, start_time - 5.0) # buffer
        self.worker_duration = duration_sec + 10.0 # total loaded duration
        
        self.cleanup()
            
        self.worker = ThumbnailWorker(
            file_path,
            start_time=self.worker_start_time,
            end_time=self.worker_start_time + self.worker_duration,
            width=self.thumb_w,
            height=self.thumb_h
        )
        self.worker.thumbnail_ready.connect(self.add_thumbnail)
        self.worker.start()

    def add_thumbnail(self, index, qimage):
        pixmap = QPixmap.fromImage(qimage)
        item = QGraphicsPixmapItem(pixmap)
        item.setPos(index * self.thumb_w, 0)
        self.scene.addItem(item)
        
        # Update scene rect
        total_width = (index + 1) * self.thumb_w
        self.scene.setSceneRect(0, 0, total_width, self.thumb_h)
        
        # Update Range Item
        if not self.range_item:
            self.range_item = RangeGraphicsItem(self.thumb_h, total_width)
            self.scene.addItem(self.range_item)
            self.range_item.setZValue(10)
        else:
            # Update width of range item so scrim works
            self.range_item.scene_w = total_width
            # Trigger repaint
            self.range_item.prepareGeometryChange()
            self.range_item.update()
            
    def cleanup(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait()
            self.worker = None

    def get_selection(self):
        """
        Returns (start_sec, end_sec)
        """
        if not self.range_item:
            return (0.0, 0.0)
            
        # Get pixels
        left_px = self.range_item.left_x
        right_px = self.range_item.right_x
        
        # Pixels per second
        # We assume 1 thumbnail = 1 second (default interval)
        px_per_sec = self.thumb_w / 1.0
        
        start = self.worker_start_time + (left_px / px_per_sec)
        end = self.worker_start_time + (right_px / px_per_sec)
        
        return (start, end)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    view = FilmstripTimeline()
    # Mock load
    # view.load_video_segment(...)
    view.show()
    sys.exit(app.exec())
