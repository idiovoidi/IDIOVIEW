from PyQt6.QtCore import QObject, pyqtSignal
import logging
from core.application.services.rating_service import RatingService

logger = logging.getLogger(__name__)

class StarRatingController(QObject):
    """Qt controller for star rating UI interactions"""
    
    rating_changed = pyqtSignal(int)  # Emitted when rating changes
    rating_preview = pyqtSignal(int)  # Emitted during hover/preview
    rating_preview_cleared = pyqtSignal()  # Emitted when preview ends
    
    def __init__(self, rating_service: RatingService):
        super().__init__()
        self.rating_service = rating_service
        self.current_image_path = None
        
    def set_current_image(self, image_path: str) -> None:
        """Set the current image being rated"""
        self.current_image_path = image_path
        if image_path:
            rating = self.rating_service.get_image_rating(image_path)
            self.rating_changed.emit(rating)
    
    def update_rating(self, rating: int) -> None:
        """Update the rating for the current image"""
        if not self.current_image_path:
            return
            
        try:
            if self.rating_service.update_rating(self.current_image_path, rating):
                self.rating_changed.emit(rating)
            
        except Exception as e:
            logger.error(f"Error updating rating: {e}")
    
    def preview_rating(self, rating: int) -> None:
        """Show preview of rating (e.g. during hover)"""
        if rating > 0:
            self.rating_preview.emit(rating)
        else:
            self.clear_preview()
    
    def clear_preview(self) -> None:
        """Clear rating preview"""
        self.rating_preview_cleared.emit()
    
    def handle_key_press(self, key: int) -> bool:
        """Handle numeric key press for rating"""
        try:
            # Convert key to rating (1-5)
            if 49 <= key <= 53:  # Keys 1-5
                rating = key - 48  # Convert ASCII to number
                self.update_rating(rating)
                return True
            elif key == 48:  # Key 0
                self.update_rating(0)
                return True
            return False
        except Exception as e:
            logger.error(f"Error handling key press: {e}")
            return False 