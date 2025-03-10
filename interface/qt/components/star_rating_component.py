"""Star rating component that can be used across different views"""

from typing import Optional
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt

from interface.qt.widgets.metadata import StarRatingWidget
from interface.qt.controllers.star_rating_controller import StarRatingController
from core.application.services.rating_service import RatingService

class StarRatingComponent(QWidget):
    """Component that combines StarRatingWidget with StarRatingController"""
    
    def __init__(self, 
                 rating_service: RatingService,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Create controller
        self.rating_controller = StarRatingController(rating_service)
        
        # Create widget
        self.star_rating = StarRatingWidget(self)
        
        # Setup layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.star_rating, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Connect signals
        self._connect_signals()
        
    def _connect_signals(self):
        """Connect controller and widget signals"""
        # Controller to widget
        self.rating_controller.rating_changed.connect(self.star_rating.set_rating)
        self.rating_controller.rating_preview.connect(self.star_rating.overlay.set_hover_rating)
        self.rating_controller.rating_preview_cleared.connect(self.star_rating.overlay.clear_hover_rating)
        
        # Widget to controller
        self.star_rating.rating_changed.connect(self.rating_controller.update_rating)
        self.star_rating.overlay.rating_preview.connect(self.rating_controller.preview_rating)
        self.star_rating.overlay.rating_preview_cleared.connect(self.rating_controller.clear_preview)
        
    def set_current_image(self, image_path: str) -> None:
        """Set the current image being rated"""
        self.rating_controller.set_current_image(image_path)
        
    def handle_key_press(self, key: int) -> bool:
        """Handle numeric key press for rating"""
        return self.rating_controller.handle_key_press(key) 