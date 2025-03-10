"""Fullscreen image viewer with navigation and rating support"""

from typing import List, Optional
from pathlib import Path

# Qt imports
from PyQt6.QtCore import (
    Qt, pyqtSignal, QSize, QPoint, QTimer
)
from PyQt6.QtGui import (
    QPixmap, QImage, QPainter, QColor,
    QKeyEvent, QWheelEvent, QResizeEvent, QTransform
)
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout,
    QHBoxLayout, QScrollArea, QScrollBar,
    QPushButton, QSizePolicy
)

# Dependency injection
from dependency_injector.wiring import inject, Provide

# Application layer
from core.application.services.image_loader_service import ImageLoaderService
from core.application.services.rating_service import RatingService
from core.application.services.metadata_service import MetadataService
from core.application.services.image_transform_service import ImageTransformService

# Domain layer
from core.domain.entities.image import Image
from core.domain.entities.image_hash import ImageHash

# Infrastructure layer
from core.infrastructure.config.app_config import AppConfig

# Local imports
from .base_view import BaseView
from interface.qt.widgets.metadata import StarRatingWidget
from interface.qt.widgets.controls import Toolbar
from interface.qt.controllers.star_rating_controller import StarRatingController
from interface.qt.components.star_rating_component import StarRatingComponent

# Container
from core.container.container import Container

# Logging
import logging
logger = logging.getLogger(__name__)

class ZoomableGraphicsView(QScrollArea):
    """Custom widget for zoomable image display"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Setup scrolling behavior
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWidget(self.image_label)
        
        # Initialize zoom state
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        
    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle mouse wheel for zooming"""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Calculate zoom
            delta = event.angleDelta().y()
            zoom_in = delta > 0
            
            # Update zoom factor
            factor = 1.1 if zoom_in else 0.9
            new_zoom = self.zoom_factor * factor
            
            # Apply zoom if within limits
            if self.min_zoom <= new_zoom <= self.max_zoom:
                self.zoom_factor = new_zoom
                self.update_zoom()
                
            event.accept()
        else:
            super().wheelEvent(event)
            
    def update_zoom(self):
        """Update image display with current zoom"""
        if pixmap := self.image_label.pixmap():
            scaled_pixmap = pixmap.scaled(
                pixmap.size() * self.zoom_factor,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)

class FullScreenViewer(BaseView):
    """Full screen image viewer with navigation and rating support"""
    
    # Signals
    image_deleted = pyqtSignal(str)  # Emitted when image is deleted
    closed = pyqtSignal(str)  # Emitted when viewer is closed with last path
    rating_changed = pyqtSignal(str, int)  # Emitted when rating changes
    image_changed = pyqtSignal(str)  # Emitted when current image changes
    
    # Key mappings
    KEY_ACTIONS = {
        Qt.Key.Key_Left: lambda self: self.navigate(-1, 0),
        Qt.Key.Key_Right: lambda self: self.navigate(1, 0),
        Qt.Key.Key_Up: lambda self: self.navigate(-1, 0),
        Qt.Key.Key_Down: lambda self: self.navigate(1, 0),
        Qt.Key.Key_Home: lambda self: self.navigate_to_position("first"),
        Qt.Key.Key_End: lambda self: self.navigate_to_position("last"),
        Qt.Key.Key_PageUp: lambda self: self.navigate_to_position("page_up"),
        Qt.Key.Key_PageDown: lambda self: self.navigate_to_position("page_down"),
        Qt.Key.Key_Escape: lambda self: self.close(),
        Qt.Key.Key_R: lambda self: self.rotate_image(),
        Qt.Key.Key_M: lambda self: self.toggle_mirror_mode(),
        Qt.Key.Key_F: lambda self: self.toggle_fit_mode(),
    }
    
    # Modifier keys to ignore
    MODIFIER_KEYS = {Qt.Key.Key_Shift, Qt.Key.Key_Control, Qt.Key.Key_Alt, Qt.Key.Key_Meta}
    
    @inject
    def __init__(
        self,
        image_data: dict,  # Contains paths, current_index, and hashes
        image_loader: ImageLoaderService = Provide[Container.image_loader],
        rating_service: RatingService = Provide[Container.rating_service],
        metadata_service: MetadataService = Provide[Container.metadata_service],
        image_transform: ImageTransformService = Provide[Container.image_transform],
        parent: Optional[QWidget] = None
    ):
        # Initialize BaseView first
        super().__init__(rating_service, image_loader, parent)
        
        # Store additional services
        self.metadata_service = metadata_service
        self.image_transform = image_transform
        
        # Store image data
        self.image_paths = image_data['paths']
        self.current_index = image_data['current_index']
        self.image_hashes = image_data['hashes']
        
        # Initialize state
        self.is_fullscreen = False
        self.rotation = 0
        self.is_mirror_mode = False
        self.fit_to_window = True
        
        # Initialize thumbnails dict for BaseView compatibility
        self.thumbnails = {path: None for path in self.image_paths}
        self.selected_paths = {self.image_paths[self.current_index]} if self.image_paths else set()
        self.last_selected_path = self.image_paths[self.current_index] if self.image_paths else None
        
        # Create container widget for BaseView
        self.container = QWidget()
        self.setWidget(self.container)
        
        # Setup UI
        self.setup_ui()
        
        # Load initial image
        self.load_current_image()

    def add_image(self, image: Image) -> None:
        """Add an image to the view. Required by BaseView."""
        path = image.path
        if path not in self.thumbnails:
            self.image_paths.append(path)
            self.thumbnails[path] = None
            self.image_hashes[path] = image.hash_value
            
    def clear(self) -> None:
        """Clear the view. Required by BaseView."""
        self.image_paths.clear()
        self.thumbnails.clear()
        self.image_hashes.clear()
        self.current_index = -1
        self.selected_paths.clear()
        self.last_selected_path = None
        if hasattr(self, 'image_view'):
            self.image_view.image_label.clear()
            
    def load_directory(self, path: str) -> None:
        """Load a directory of images. Required by BaseView but not used in fullscreen."""
        logger.warning("load_directory called on FullScreenViewer - operation not supported")
        pass
        
    def reflow_layout(self) -> None:
        """Reflow the layout. Required by BaseView but not used in fullscreen."""
        # In fullscreen view, we just need to handle resize
        if self.fit_to_window:
            self.fit_to_screen()
            
    def cleanup(self) -> None:
        """Clean up resources. Required by BaseView."""
        self.clear()
        if hasattr(self, 'image_view'):
            self.image_view.deleteLater()
        if hasattr(self, 'star_rating_component'):
            self.star_rating_component.deleteLater()
        
    def setup_ui(self):
        """Initialize the user interface"""
        # Set window properties
        self.setWindowTitle("Image Viewer")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.resize(800, 600)
        
        # Create main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create toolbar
        self.toolbar = Toolbar(self)
        layout.addWidget(self.toolbar)
        
        # Create image view
        self.image_view = ZoomableGraphicsView(self)
        layout.addWidget(self.image_view)
        
        # Create star rating component
        self.star_rating_component = StarRatingComponent(self.rating_service, self)
        layout.addWidget(self.star_rating_component)
        
        # Create status bar
        self.status_bar = QLabel(self)
        self.status_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_bar)
        
    def load_current_image(self):
        """Load and display the current image"""
        try:
            if not (0 <= self.current_index < len(self.image_paths)):
                return
                
            path = self.image_paths[self.current_index]
            
            # Update selection in BaseView without triggering additional events
            if path != self.last_selected_path:
                self.selected_paths = {path}
                self.last_selected_path = path
                
                # Update rating component with current image
                if hasattr(self, 'star_rating_component'):
                    self.star_rating_component.set_current_image(path)
                
                # Load and display image
                pixmap = QPixmap(path)
                if pixmap.isNull():
                    logger.error(f"Failed to load image: {path}")
                    return
                    
                # Apply transformations
                if self.rotation or self.is_mirror_mode:
                    transformed = self.image_transform.apply_transforms(
                        pixmap,
                        rotation=self.rotation,
                        mirror=self.is_mirror_mode
                    )
                    if transformed:
                        pixmap = transformed
                        
                # Update display based on fit mode
                if self.fit_to_window:
                    view_size = self.image_view.size()
                    scaled_pixmap = pixmap.scaled(
                        view_size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.image_view.image_label.setPixmap(scaled_pixmap)
                else:
                    self.image_view.image_label.setPixmap(pixmap)
                    
                # Update status and emit signals
                self.update_status()
                self.image_changed.emit(path)
                
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard events"""
        key = event.key()
        
        # Skip handling of pure modifier key presses
        if key in self.MODIFIER_KEYS:
            event.accept()
            return
            
        # Try handling rating keys first
        if self.star_rating_component.handle_key_press(key):
            return
            
        # Handle mapped actions
        if action := self.KEY_ACTIONS.get(key):
            action(self)
            event.accept()
        else:
            super().keyPressEvent(event)
            
    def wheelEvent(self, event) -> None:
        """Handle mouse wheel events for navigation"""
        try:
            # If Ctrl is held, let the ZoomableGraphicsView handle zooming
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                if hasattr(self, 'image_view'):
                    self.image_view.wheelEvent(event)
                return

            # Otherwise use wheel for navigation
            delta = event.angleDelta().y()
            if delta > 0:  # Scroll up
                self.navigate(-1, 0)  # Go to previous image
            else:  # Scroll down
                self.navigate(1, 0)  # Go to next image
            event.accept()
            
        except Exception as e:
            logger.error(f"Error handling wheel event: {e}")
            event.accept()

    def navigate(self, dx: int, dy: int, extend_selection: bool = False) -> None:
        """Override BaseView's navigate to handle linear navigation"""
        try:
            if not self.image_paths:
                return
                
            # Calculate new index based on either horizontal or vertical movement
            new_index = self.current_index + (dx or dy)  # Use either dx or dy, prioritize dx
                
            # Handle wrapping
            if new_index < 0:
                new_index = len(self.image_paths) - 1
            elif new_index >= len(self.image_paths):
                new_index = 0
                
            # Only update if index actually changed
            if new_index != self.current_index:
                self.current_index = new_index
                self.load_current_image()
                
        except Exception as e:
            logger.error(f"Error in navigate: {e}")
            
    def navigate_to_position(self, position: str, extend_selection: bool = False) -> None:
        """Override BaseView's navigate_to_position for fullscreen view"""
        try:
            if not self.image_paths:
                return
                
            if position == "first":
                self.current_index = 0
            elif position == "last":
                self.current_index = len(self.image_paths) - 1
            elif position == "page_up":
                self.current_index = max(0, self.current_index - 10)
            elif position == "page_down":
                self.current_index = min(len(self.image_paths) - 1, self.current_index + 10)
                
            self.load_current_image()
            
        except Exception as e:
            logger.error(f"Error in navigate_to_position: {e}")
            
    def closeEvent(self, event):
        """Handle window close"""
        if 0 <= self.current_index < len(self.image_paths):
            self.closed.emit(self.image_paths[self.current_index])
        super().closeEvent(event)

    def rotate_image(self) -> None:
        """Rotate image 90 degrees clockwise"""
        self.rotation = (self.rotation + 90) % 360
        self.load_current_image()
        
    def toggle_mirror_mode(self) -> None:
        """Toggle horizontal mirror mode"""
        self.is_mirror_mode = not self.is_mirror_mode
        self.load_current_image()
        
    def toggle_fit_mode(self) -> None:
        """Toggle between fit to window and actual size"""
        self.fit_to_window = not self.fit_to_window
        self.load_current_image()
        
    def fit_to_screen(self) -> None:
        """Scale image to fit screen while maintaining aspect ratio"""
        if 0 <= self.current_index < len(self.image_paths):
            path = self.image_paths[self.current_index]
            pixmap = QPixmap(path)
            
            if not pixmap.isNull():
                # Apply transformations
                if self.rotation:
                    pixmap = pixmap.transformed(QTransform().rotate(self.rotation))
                if self.is_mirror_mode:
                    pixmap = pixmap.transformed(QTransform().scale(-1, 1))
                
                # Get available size
                view_size = self.image_view.size()
                scaled_pixmap = pixmap.scaled(
                    view_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_view.image_label.setPixmap(scaled_pixmap)
                
    def update_status(self) -> None:
        """Update status bar with current image info"""
        if 0 <= self.current_index < len(self.image_paths):
            path = self.image_paths[self.current_index]
            filename = Path(path).name
            status = f"Image {self.current_index + 1} of {len(self.image_paths)} - {filename}"
            if self.rotation:
                status += f" (Rotated {self.rotation}°)"
            if self.is_mirror_mode:
                status += " (Mirrored)"
            self.status_bar.setText(status)
            
    def resizeEvent(self, event: QResizeEvent) -> None:
        """Handle window resize"""
        super().resizeEvent(event)
        if self.fit_to_window:
            self.fit_to_screen()

    def setup_shortcuts(self):
        """Setup keyboard shortcuts for fullscreen viewer"""
        # Navigation shortcuts are handled in keyPressEvent
        # Rating shortcuts are handled by star_rating_component
        # No additional shortcuts needed at this time
        pass
