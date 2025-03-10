"""Base class for image views"""

from abc import ABC, abstractmethod
from PyQt6.QtWidgets import QScrollArea
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from typing import Optional, Set
import logging

from interface.qt.views.browser.thumbnails import ThumbnailWidget
from interface.qt.controllers.star_rating_controller import StarRatingController

from ...shared.metaclass import QtABCMeta, QtViewMixin
from core.application.services.rating_service import RatingService
from core.application.services.image_loader_service import ImageLoaderService
from core.domain.entities.image import Image

logger = logging.getLogger(__name__)

class BaseView(QScrollArea, QtViewMixin, ABC, metaclass=QtABCMeta):
    """Abstract base class for image views."""
    
    # Signals
    imageClicked = pyqtSignal(str, bool)  # Signals (image_path, shift_held)
    selectionChanged = pyqtSignal()  # Emitted when selection changes
    ratingChanged = pyqtSignal(str, int)  # Signals (image_path, new_rating)
    
    def __init__(self, 
                 rating_service: RatingService,
                 image_loader_service: ImageLoaderService,
                 parent: Optional[QScrollArea] = None):
        super().__init__(parent)
        
        # Store services
        self.rating_service = rating_service
        self.image_loader = image_loader_service
        
        # Initialize rating controller
        self.rating_controller = StarRatingController(rating_service)
        self.rating_controller.rating_changed.connect(self._on_controller_rating_changed)
        
        # Configure scroll area
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
    @abstractmethod
    def add_image(self, image: Image) -> None:
        """Add an image to the view"""
        pass
        
    @abstractmethod
    def clear(self) -> None:
        """Clear the view"""
        pass
        
    @abstractmethod
    def load_directory(self, path: str) -> None:
        """Load a directory of images"""
        pass
        
    @abstractmethod
    def reflow_layout(self) -> None:
        """Reflow the layout"""
        pass
        
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources"""
        pass
        
    def create_thumbnail(self, image: Image) -> ThumbnailWidget:
        """Create a thumbnail widget for an image"""
        thumbnail = ThumbnailWidget(
            image_path=image.path,
            initial_rating=image.rating,
            parent=self.container
        )
        
        # Connect signals
        thumbnail.clicked.connect(self._on_thumbnail_clicked)
        thumbnail.rating_changed.connect(self._on_rating_changed)
        
        # Store and return
        self.thumbnails[image.path] = thumbnail
        return thumbnail
        
    def _on_thumbnail_clicked(self, image_path: str, shift_held: bool) -> None:
        """Handle thumbnail click"""
        try:
            if not shift_held:
                # Single selection
                self.deselect_all()
                self._update_selection(image_path, True)
                self.last_selected_path = image_path
            else:
                # Shift selection
                if self.last_selected_path:
                    # Get range
                    all_paths = list(self.thumbnails.keys())
                    start_idx = all_paths.index(self.last_selected_path)
                    end_idx = all_paths.index(image_path)
                    
                    # Ensure correct order
                    if start_idx > end_idx:
                        start_idx, end_idx = end_idx, start_idx
                        
                    # Select range
                    for path in all_paths[start_idx:end_idx + 1]:
                        self._update_selection(path, True)
                else:
                    # No previous selection
                    self._update_selection(image_path, True)
                    self.last_selected_path = image_path
            
            # Emit signals
            self.imageClicked.emit(image_path, shift_held)
            self.selectionChanged.emit()
            
        except Exception as e:
            logger.error(f"Error handling thumbnail click: {e}")
            
    def _update_selection(self, image_path: str, selected: bool) -> None:
        """Update selection state of a thumbnail"""
        if thumbnail := self.thumbnails.get(image_path):
            if selected:
                self.selected_paths.add(image_path)
            else:
                self.selected_paths.discard(image_path)
                if self.last_selected_path == image_path:
                    self.last_selected_path = None
            thumbnail.setStyleSheet(self._get_thumbnail_style(selected))
            
    def _get_thumbnail_style(self, selected: bool) -> str:
        """Get thumbnail style based on selection state"""
        return """
            QLabel {
                background-color: #2d2d2d;
                border: 2px solid %s;
                border-radius: 3px;
                padding: 2px;
            }
        """ % ("#0078d4" if selected else "transparent")
        
    def _on_rating_changed(self, image_path: str, rating: int) -> None:
        """Handle rating changes"""
        try:
            if self.rating_service.update_rating(image_path, rating):
                self.ratingChanged.emit(image_path, rating)
        except Exception as e:
            logger.error(f"Error handling rating change: {e}")
            
    def deselect_all(self) -> None:
        """Deselect all thumbnails"""
        for path in list(self.selected_paths):
            self._update_selection(path, False)
            
    def get_selected_paths(self) -> Set[str]:
        """Get currently selected paths"""
        return self.selected_paths.copy()
        
    def resizeEvent(self, event) -> None:
        """Handle resize events."""
        super().resizeEvent(event)
        self.reflow_layout()
        
    def _handle_thumbnail_click(self, image_path: str, shift_held: bool) -> None:
        """Handle thumbnail click with selection logic"""
        try:
            if not shift_held:
                # Single selection
                self.deselect_all()
                self._select_thumbnail(image_path)
                self.last_selected_path = image_path
            else:
                # Shift selection
                if self.last_selected_path:
                    # Get range
                    all_paths = list(self.thumbnails.keys())
                    start_idx = all_paths.index(self.last_selected_path)
                    end_idx = all_paths.index(image_path)
                    
                    # Ensure correct order
                    if start_idx > end_idx:
                        start_idx, end_idx = end_idx, start_idx
                        
                    # Select range
                    for path in all_paths[start_idx:end_idx + 1]:
                        self._select_thumbnail(path)
                else:
                    # No previous selection
                    self._select_thumbnail(image_path)
                    self.last_selected_path = image_path
            
            # Emit signals
            self.imageClicked.emit(image_path, shift_held)
            self.selectionChanged.emit()
            
        except Exception as e:
            logger.error(f"Error handling thumbnail click: {e}")

    def _select_thumbnail(self, image_path: str) -> None:
        """Internal method to select a thumbnail"""
        if thumbnail := self.thumbnails.get(image_path):
            thumbnail.setStyleSheet(f"""
                QLabel {{
                    background-color: {thumbnail.config.background_color};
                    border: 2px solid {thumbnail.config.border_color};
                    border-radius: {thumbnail.config.border_radius}px;
                    padding: 2px;
                }}
            """)
            self.selected_paths.add(image_path)

    def _deselect_thumbnail(self, image_path: str) -> None:
        """Internal method to deselect a thumbnail"""
        if thumbnail := self.thumbnails.get(image_path):
            thumbnail._apply_style()  # Reset to default style
            self.selected_paths.discard(image_path)

    def deselect_image(self, image_path: str) -> None:
        """Deselect an image."""
        if thumbnail := self.thumbnails.get(image_path):
            thumbnail.deselect()
            self.selected_paths.discard(image_path)
            self.selectionChanged.emit()
            
    def _handle_rating_changed(self, image_path: str, rating: int) -> None:
        """Handle rating changes from thumbnails."""
        try:
            if self.rating_service.update_rating(image_path, rating):
                if thumbnail := self.thumbnails.get(image_path):
                    thumbnail.update_rating(rating)
                self.ratingChanged.emit(image_path, rating)
        except Exception as e:
            logger.error(f"Error updating rating: {e}")  

    def _on_controller_rating_changed(self, rating: int) -> None:
        """Handle rating changes from controller"""
        if path := self.rating_controller.current_image_path:
            self.ratingChanged.emit(path, rating)
            
    def update_current_image(self, image_path: str) -> None:
        """Update the current image in the rating controller"""
        self.rating_controller.set_current_image(image_path)
        
    def handle_rating_key(self, key: int) -> bool:
        """Handle rating key press"""
        return self.rating_controller.handle_key_press(key)  

    def navigate(self, dx: int, dy: int, extend_selection: bool = False) -> None:
        """Navigate in the grid by delta x and y"""
        try:
            if not self.thumbnails:
                return
                
            # Get current grid dimensions
            columns = self.grid_layout.columnCount()
            if columns == 0:
                return
                
            # Get current position
            current_index = -1
            if self.last_selected_path:
                current_index = list(self.thumbnails.keys()).index(self.last_selected_path)
            
            # Calculate new position
            if current_index == -1:
                # No selection, select first image
                new_index = 0
            else:
                current_row = current_index // columns
                current_col = current_index % columns
                
                # Calculate new position
                new_col = (current_col + dx) % columns
                new_row = current_row + dy
                
                # Handle row wrapping
                total_rows = (len(self.thumbnails) + columns - 1) // columns
                if new_row < 0:
                    new_row = total_rows - 1
                elif new_row >= total_rows:
                    new_row = 0
                    
                # Calculate new index
                new_index = new_row * columns + new_col
                
                # Ensure index is within bounds
                new_index = min(new_index, len(self.thumbnails) - 1)
            
            # Update selection
            if 0 <= new_index < len(self.thumbnails):
                new_path = list(self.thumbnails.keys())[new_index]
                if not extend_selection:
                    self.deselect_all()
                self._update_selection(new_path, True)
                self.last_selected_path = new_path
                self.selectionChanged.emit()
                
                # Ensure the selected thumbnail is visible and focused
                if thumbnail := self.thumbnails.get(new_path):
                    self.ensureWidgetVisible(thumbnail)
                    thumbnail.setFocus()
                    
        except Exception as e:
            logger.error(f"Error in navigate: {e}")

    def navigate_to_position(self, position: str, extend_selection: bool = False) -> None:
        """Navigate to a specific position in the grid"""
        try:
            if not self.thumbnails:
                return
                
            thumbnails = list(self.thumbnails.values())
            current_index = -1
            if self.last_selected_path:
                current_index = list(self.thumbnails.keys()).index(self.last_selected_path)
            
            # Calculate target index based on position
            if position == "first":
                target_index = 0
            elif position == "last":
                target_index = len(thumbnails) - 1
            elif position == "page_up":
                # Move up by number of visible rows
                columns = self.grid_layout.columnCount()
                visible_height = self.viewport().height()
                thumbnail_height = thumbnails[0].height() + self.grid_layout.spacing()
                visible_rows = max(1, visible_height // thumbnail_height)
                target_index = max(0, current_index - (columns * visible_rows))
            elif position == "page_down":
                # Move down by number of visible rows
                columns = self.grid_layout.columnCount()
                visible_height = self.viewport().height()
                thumbnail_height = thumbnails[0].height() + self.grid_layout.spacing()
                visible_rows = max(1, visible_height // thumbnail_height)
                target_index = min(len(thumbnails) - 1, current_index + (columns * visible_rows))
            else:
                return
            
            # Update selection
            if 0 <= target_index < len(thumbnails):
                target_path = thumbnails[target_index].image_path
                if not extend_selection:
                    self.deselect_all()
                self._update_selection(target_path, True)
                self.last_selected_path = target_path
                self.selectionChanged.emit()
                
                # Ensure target is visible and focused
                thumbnails[target_index].setFocus()
                self.ensureWidgetVisible(thumbnails[target_index])
                
        except Exception as e:
            logger.error(f"Error in navigate_to_position: {e}")

    def select_all(self) -> None:
        """Select all thumbnails"""
        try:
            for path in self.thumbnails.keys():
                self._update_selection(path, True)
            self.selectionChanged.emit()
        except Exception as e:
            logger.error(f"Error in select_all: {e}")

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle keyboard events"""
        try:
            key = event.key()
            logger.debug(f"BaseView received key press: {key}")
            
            # Handle navigation keys
            handled = True  # Assume we'll handle the event
            
            if key == Qt.Key.Key_Left:
                self.navigate(-1, 0)
            elif key == Qt.Key.Key_Right:
                self.navigate(1, 0)
            elif key == Qt.Key.Key_Up:
                self.navigate(0, -1)
            elif key == Qt.Key.Key_Down:
                self.navigate(0, 1)
            else:
                handled = False
                
            if handled:
                event.accept()
            else:
                super().keyPressEvent(event)
                
        except Exception as e:
            logger.error(f"Error handling key press: {e}")
            event.accept()  # Prevent event propagation on error  