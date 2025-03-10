from typing import Optional, Dict
import logging

from core.domain.repositories.image_repository import ImageRepository
from core.domain.entities.image import Image

logger = logging.getLogger(__name__)

class RatingService:
    """Application service for managing image ratings"""
    
    def __init__(self, image_repository: ImageRepository):
        self.image_repository = image_repository
        self.max_rating = 5
        
    def get_image_rating(self, path: str) -> int:
        """Get the rating for an image"""
        try:
            if image := self.image_repository.get_by_path(path):
                return image.metadata.rating
            return 0
        except Exception as e:
            logger.error(f"Error getting rating for {path}: {e}")
            return 0
        
    def update_rating(self, path: str, rating: int) -> bool:
        """Update the rating for an image"""
        try:
            # Validate rating
            rating = max(0, min(rating, self.max_rating))
            
            # Update rating
            return self.image_repository.update_rating(path, rating)
            
        except Exception as e:
            logger.error(f"Error updating rating for {path}: {e}")
            return False
        
    def batch_update_ratings(self, ratings: Dict[str, int]) -> Dict[str, bool]:
        """Update ratings for multiple images"""
        results = {}
        for path, rating in ratings.items():
            results[path] = self.update_rating(path, rating)
        return results 