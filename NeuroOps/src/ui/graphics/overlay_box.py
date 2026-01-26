from PyQt6.QtWidgets import QGraphicsObject
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPen, QBrush, QColor, QFont

class OverlayBox(QGraphicsObject):
    """
    A futuristic bounding box overlay for detections.
    Features: Corner bracket style, label with confidence score, and Cyberpunk aesthetics.
    """
    def __init__(self, rect, label, score, color="#00FF88", parent=None):
        super().__init__(parent)
        self.rect_geo = rect # QRectF (0-1 normalized if needed, but assuming pixel coords here)
        self.label = label
        self.score = score
        self.base_color = QColor(color)
        
        # Pen Styles
        self.pen = QPen(self.base_color)
        self.pen.setWidth(2)
        self.pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        
        # Brush for label bg
        self.label_bg = QBrush(self.base_color.darker(150))
        self.label_bg.setStyle(Qt.BrushStyle.SolidPattern)
        
        self.setAcceptHoverEvents(True)

    def boundingRect(self):
        # Slightly larger to accommodate pen width and label
        return self.rect_geo.adjusted(-5, -25, 5, 5)

    def paint(self, painter, option, widget):
        painter.setRenderHint(painter.RenderHint.Antialiasing)
        
        # 1. Draw Corners (Bracket Style) instead of full box for cleaner look
        r = self.rect_geo
        w, h = r.width(), r.height()
        corner_len = min(w, h) * 0.2
        
        painter.setPen(self.pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Top Left
        painter.drawLine(r.topLeft(), r.topLeft() + Qt.QPointF(corner_len, 0))
        painter.drawLine(r.topLeft(), r.topLeft() + Qt.QPointF(0, corner_len))
        
        # Top Right
        painter.drawLine(r.topRight(), r.topRight() - Qt.QPointF(corner_len, 0))
        painter.drawLine(r.topRight(), r.topRight() + Qt.QPointF(0, corner_len))
        
        # Bottom Left
        painter.drawLine(r.bottomLeft(), r.bottomLeft() + Qt.QPointF(corner_len, 0))
        painter.drawLine(r.bottomLeft(), r.bottomLeft() - Qt.QPointF(0, corner_len))
        
        # Bottom Right
        painter.drawLine(r.bottomRight(), r.bottomRight() - Qt.QPointF(corner_len, 0))
        painter.drawLine(r.bottomRight(), r.bottomRight() - Qt.QPointF(0, corner_len))
        
        # Low opacity fill?
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self.base_color.red(), self.base_color.green(), self.base_color.blue(), 30))
        painter.drawRect(r)
        
        # 2. Draw Label Tag
        if self.label:
            # Label Rect
            txt = f"{self.label.upper()} {int(self.score*100)}%"
            font = QFont("Consolas", 10, QFont.Weight.Bold)
            painter.setFont(font)
            fm = painter.fontMetrics()
            tw = fm.horizontalAdvance(txt)
            th = fm.height()
            
            # Draw bg
            label_rect = QRectF(r.left(), r.top() - th - 4, tw + 10, th + 4)
            painter.setBrush(self.base_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(label_rect)
            
            # Draw Text
            painter.setPen(QColor("#000000"))
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, txt)
