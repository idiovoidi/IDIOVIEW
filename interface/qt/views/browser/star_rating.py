"""Star rating overlay widget"""

import logging
import math
from typing import Optional
from PyQt6.QtWidgets import QWidget, QLabel , QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QPainterPath

logger = logging.getLogger(__name__)

class StarRatingOverlay(QWidget):
    """Overlay widget for displaying star ratings"""
    
    # Signals
    rating_changed = pyqtSignal(int)  # Emitted when rating changes
    rating_preview = pyqtSignal(int)  # Emitted during hover/preview
    rating_preview_cleared = pyqtSignal()  # Emitted when preview ends
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configure widget
        self.rating = 0
        self.max_stars = 5
        self.star_size = 16
        self.padding = 4
        self.hover_rating = 0
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
        # Calculate size based on stars and padding
        total_width = (self.star_size * self.max_stars) + (2 * self.padding) + ((self.max_stars - 1) * 2)
        self.setFixedSize(total_width, self.star_size + 2 * self.padding)
        
        # Apply dark theme style
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.5);
                border-radius: 3px;
            }
        """)
        
    def set_rating(self, rating: int) -> None:
        """Set the current rating"""
        self.rating = max(0, min(rating, self.max_stars))
        self.update()
        
    def set_hover_rating(self, rating: int) -> None:
        """Set hover preview rating"""
        self.hover_rating = rating
        self.update()
        
    def clear_hover_rating(self) -> None:
        """Clear hover preview rating"""
        self.hover_rating = 0
        self.update()
        
    def mousePressEvent(self, event) -> None:
        """Handle mouse press events"""
        try:
            x = event.position().x() - self.padding
            new_rating = min(self.max_stars, max(1, int(x / (self.star_size + 2)) + 1))
            self.rating_changed.emit(new_rating)
        except Exception as e:
            logger.error(f"Error handling mouse press: {e}")
        
    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move events"""
        try:
            x = event.position().x() - self.padding
            preview_rating = min(self.max_stars, max(0, int(x / (self.star_size + 2)) + 1))
            self.rating_preview.emit(preview_rating)
        except Exception as e:
            logger.error(f"Error handling mouse move: {e}")
        
    def leaveEvent(self, event) -> None:
        """Handle mouse leave events"""
        try:
            self.rating_preview_cleared.emit()
        except Exception as e:
            logger.error(f"Error handling mouse leave: {e}")
            
    def handle_key_press(self, event) -> bool:
        """Handle keyboard events"""
        try:
            # Convert key to rating (1-5)
            if 49 <= event.key() <= 53:  # Keys 1-5
                rating = event.key() - 48  # Convert ASCII to number
                self.rating_changed.emit(rating)
                return True
            elif event.key() == 48:  # Key 0
                self.rating_changed.emit(0)
                return True
            return False
        except Exception as e:
            logger.error(f"Error handling key press: {e}")
            return False
            
    def paintEvent(self, event) -> None:
        """Draw the star rating"""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw background
            painter.fillRect(self.rect(), QColor(0, 0, 0, 153))
            
            # Draw stars
            star_color = QColor("#FFD700")  # Gold color
            painter.setPen(QPen(star_color, 1))
            painter.setBrush(star_color)
            
            x = self.padding
            for i in range(self.max_stars):
                if i < (self.hover_rating or self.rating):
                    self.draw_star(painter, x, self.padding, self.star_size, filled=True)
                else:
                    self.draw_star(painter, x, self.padding, self.star_size, filled=False)
                x += self.star_size + 2
                
        except Exception as e:
            logger.error(f"Error painting star rating: {e}")
            
    def draw_star(self, painter: QPainter, x: float, y: float, size: float, filled: bool = True) -> None:
        """Draw a single star"""
        try:
            points = []
            center_x = x + size/2
            center_y = y + size/2
            outer_radius = size/2
            inner_radius = size/4
            
            for i in range(10):
                angle = i * 36 * math.pi / 180
                radius = outer_radius if i % 2 == 0 else inner_radius
                points.append((
                    center_x + radius * math.cos(angle),
                    center_y - radius * math.sin(angle)
                ))
            
            path = QPainterPath()
            path.moveTo(points[0][0], points[0][1])
            for px, py in points[1:]:
                path.lineTo(px, py)
            path.closeSubpath()
            
            if filled:
                painter.fillPath(path, painter.brush())
            painter.drawPath(path)
            
        except Exception as e:
            logger.error(f"Error drawing star: {e}")
            
    def resizeEvent(self, event) -> None:
        """Handle resize events"""
        try:
            if self.parent():
                new_x = (self.parent().width() - self.width()) // 2
                new_y = self.parent().height() - self.height() - 5
                self.move(new_x, new_y)
        except Exception as e:
            logger.error(f"Error handling resize: {e}") 
            
class StarRatingWidget(QWidget):
    """Widget for displaying and editing star ratings"""
    
    rating_changed = pyqtSignal(int)
    
    def __init__(self, 
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI components"""
        # Create star rating overlay
        self.overlay = StarRatingOverlay(self)
        
        # Create rating label
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 12px;
            }
        """)
        
        # Update label text
        self.update_label()
        
    def set_rating(self, rating: int):
        """Set the current rating"""
        self.overlay.set_rating(rating)
        self.update_label()
        self.rating_changed.emit(rating)
        
    def update_label(self):
        """Update the rating label text"""
        rating = self.overlay.rating
        self.label.setText(f"{rating} of {self.overlay.max_stars} stars")
        
    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        self.overlay.resize(event.size())
        
        # Position label below overlay
        label_y = self.overlay.height() + 5
        self.label.move(0, label_y)
        self.label.setFixedWidth(self.width()) 