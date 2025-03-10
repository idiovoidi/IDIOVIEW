"""Thumbnail widget for displaying image thumbnails"""

import logging
from typing import Optional, Protocol
from dataclasses import dataclass
from pathlib import Path
from PIL import ImageFile

from PyQt6.QtWidgets import QLabel, QProgressBar
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QPen, QColor, QImage, QPixmap
from PyQt6.QtWidgets import QWidget, QVBoxLayout

from core.domain.entities.image import Image
from core.infrastructure.cache.thumbnail_cache import ThumbnailCache
from interface.qt.views.browser.star_rating import StarRatingOverlay
from core.infrastructure.utils.qt_utils import load_qimage, scale_qimage, is_valid_qimage

# Configure PIL globally to prevent window creation
ImageFile.LOAD_TRUNCATED_IMAGES = True

logger = logging.getLogger(__name__)

@dataclass
class ThumbnailConfig:
    """Configuration for thumbnail appearance"""
    default_size: tuple[int, int] = (200, 150)  # More reasonable aspect ratio
    background_color: str = "#2d2d2d"
    border_color: str = "#0078d4"
    hover_color: str = "#2997ff"
    border_radius: int = 3
    use_cache: bool = True

class LoadingOverlay(QWidget):
    """Loading indicator overlay for thumbnails"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create progress bar
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 0)  # Indeterminate progress
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #1e1e1e;
                border: none;
                border-radius: 2px;
                height: 4px;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 2px;
            }
        """)
        
        layout.addStretch()
        layout.addWidget(self.progress)
        layout.addStretch()
        
        # Make background semi-transparent
        self.setStyleSheet("background-color: rgba(45, 45, 45, 180);")

class RatingOverlayProvider(Protocol):
    """Protocol for rating overlay providers"""
    def create_overlay(self, parent: QLabel) -> 'StarRatingOverlay':
        """Create a rating overlay for the thumbnail"""
        ...

class DefaultRatingOverlayProvider:
    """Default implementation of rating overlay provider"""
    def create_overlay(self, parent: QLabel) -> 'StarRatingOverlay':
        overlay = StarRatingOverlay(parent)
        overlay.move(5, 5)
        return overlay

class ThumbnailWidget(QLabel):
    """Widget for displaying image thumbnails"""
    
    # Signals
    clicked = pyqtSignal(str, bool)  # Signals (image_path, shift_held)
    rating_changed = pyqtSignal(str, int)  # Signals (image_path, new_rating)
    thumbnail_loaded = pyqtSignal(bool)  # Emitted when thumbnail loads (success)
    
    def __init__(self, 
                 image_path: str,
                 initial_rating: int = 0,
                 rating_provider: Optional[RatingOverlayProvider] = None,
                 config: Optional[ThumbnailConfig] = None,
                 parent: Optional[QLabel] = None,
                 initial_size: Optional[tuple[int, int]] = None):
        """Initialize thumbnail widget"""
        super().__init__(parent)
        
        # Store basic properties
        self.image_path = str(image_path)
        self.current_rating = initial_rating
        self.config = config or ThumbnailConfig()
        self._rating_provider = rating_provider or DefaultRatingOverlayProvider()
        
        # Initialize state
        self.is_loading = False
        self.loading_overlay = None
        self._current_size = None
        self._load_attempted = False
        self._load_succeeded = False
        
        # Configure widget
        self._setup_widget(initial_size)
        self._setup_rating_overlay()
        self._setup_loading_overlay()
        self._apply_style()
        
        # Show loading state
        self.show_loading(True)
        
    def _apply_style(self) -> None:
        """Apply widget styling"""
        style = f"""
            QLabel {{
                background-color: {self.config.background_color};
                border-radius: {self.config.border_radius}px;
                border: 2px solid transparent;
                padding: 2px;
            }}
            QLabel:focus {{
                border: 2px solid {self.config.border_color};
                background-color: {self.config.background_color};
            }}
        """
        self.setStyleSheet(style)
        
    def _setup_widget(self, initial_size: Optional[tuple[int, int]] = None) -> None:
        """Setup basic widget configuration"""
        # Set size
        size = initial_size or self.config.default_size
        self.setFixedSize(*size)
        logger.debug(f"Set thumbnail size to {size} for {self.image_path}")
        
        # Configure widget
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Set placeholder
        self.set_placeholder()
        
    def _setup_rating_overlay(self) -> None:
        """Setup rating overlay"""
        self.star_rating = self._rating_provider.create_overlay(self)
        self.star_rating.rating_changed.connect(self._on_rating_changed)
        self.star_rating.set_rating(self.current_rating)
        
    def _setup_loading_overlay(self):
        """Setup loading overlay"""
        self.loading_overlay = LoadingOverlay(self)
        self.loading_overlay.hide()
        self.loading_overlay.resize(self.size())
        
    def show_loading(self, show: bool = True):
        """Show or hide loading overlay"""
        if show and not self.is_loading:
            self.is_loading = True
            self.loading_overlay.show()
            self.loading_overlay.raise_()
        elif not show and self.is_loading:
            self.is_loading = False
            self.loading_overlay.hide()
        
    def set_placeholder(self) -> None:
        """Set placeholder image using QImage"""
        try:
            logger.debug(f"Setting placeholder for {self.image_path}")
            placeholder = QImage(self.width(), self.height(), QImage.Format.Format_RGB32)
            placeholder.fill(QColor(self.config.background_color))
            self.setPixmap(QPixmap.fromImage(placeholder))  # Fixed conversion
            logger.debug(f"Placeholder set for {self.image_path}")
        except Exception as e:
            logger.error(f"Error setting placeholder for {self.image_path}: {e}", exc_info=True)
        
    def mousePressEvent(self, event) -> None:
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            shift_held = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
            self.clicked.emit(self.image_path, shift_held)
        event.accept()
        
    def keyPressEvent(self, event) -> None:
        """Handle keyboard events"""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Space:
            # Emit clicked signal on Enter/Space
            shift_held = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
            self.clicked.emit(self.image_path, shift_held)
            event.accept()
        elif event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down):
            # Let parent handle arrow key navigation
            event.ignore()
        elif hasattr(self, 'star_rating'):
            # Let star rating handle other keys (like number keys for rating)
            self.star_rating.handle_key_press(event)
        else:
            super().keyPressEvent(event)
            
    def paintEvent(self, event) -> None:
        """Custom paint event"""
        try:
            super().paintEvent(event)
        except Exception as e:
            logger.error(f"Error in paint event: {e}")
            
    def resizeEvent(self, event) -> None:
        """Handle resize events"""
        try:
            super().resizeEvent(event)
            if self.loading_overlay:
                self.loading_overlay.resize(self.size())
        except Exception as e:
            logger.error(f"Error in resize event: {e}")
            
    def showEvent(self, event) -> None:
        """Handle show events"""
        try:
            super().showEvent(event)
        except Exception as e:
            logger.error(f"Error in show event: {e}")
        
    def _on_rating_changed(self, rating: int) -> None:
        """Handle rating changes from overlay"""
        if rating != self.current_rating:
            self.current_rating = rating
            self.rating_changed.emit(self.image_path, rating)
        
    def set_thumbnail(self, image: QImage) -> None:
        """Set the thumbnail from QImage with proper scaling"""
        try:
            if is_valid_qimage(image):
                # Scale the QImage using utility function
                if scaled := scale_qimage(image, (self.width(), self.height())):
                    self.setPixmap(QPixmap.fromImage(scaled))
                    self._current_size = self.size()
                    self._load_succeeded = True
                    self.show_loading(False)
                    self.thumbnail_loaded.emit(True)
                    
                    if hasattr(self, 'star_rating'):
                        self.star_rating.raise_()
            else:
                self.show_loading(False)
                self.thumbnail_loaded.emit(False)
        except Exception as e:
            logger.error(f"Error setting thumbnail: {e}")
            self.show_loading(False)
        
    def get_rating(self) -> int:
        """Get current rating"""
        return self.current_rating
        
    def set_rating(self, rating: int) -> None:
        """Set rating value"""
        if self.current_rating != rating:
            self.current_rating = rating
            if hasattr(self, 'star_rating'):
                self.star_rating.set_rating(rating)
        
    def get_current_size(self) -> tuple[int, int]:
        """Get the current size of the thumbnail"""
        return self._current_size
        
    def get_load_attempted(self) -> bool:
        """Get whether the thumbnail load was attempted"""
        return self._load_attempted
        
    def get_load_succeeded(self) -> bool:
        """Get whether the thumbnail load succeeded"""
        return self._load_succeeded
        
    def set_load_attempted(self, attempted: bool) -> None:
        """Set whether the thumbnail load was attempted"""
        self._load_attempted = attempted
        
    def set_load_succeeded(self, succeeded: bool) -> None:
        """Set whether the thumbnail load succeeded"""
        self._load_succeeded = succeeded
        
    def get_image_path(self) -> str:
        """Get the image path"""
        return self.image_path
        
    def get_rating_provider(self) -> RatingOverlayProvider:
        """Get the rating overlay provider"""
        return self._rating_provider
        
    def get_config(self) -> ThumbnailConfig:
        """Get the configuration for the thumbnail"""
        return self.config
        
    def get_loading_overlay(self) -> LoadingOverlay:
        """Get the loading overlay"""
        return self.loading_overlay
        
    def get_star_rating(self) -> StarRatingOverlay:
        """Get the star rating overlay"""
        return self.star_rating 