"""Repository interface for image loading and management"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Set
from pathlib import Path
from ..entities.image import Image
from ..entities.image_status import ImageStatus
from ..specifications.image_specifications import ImageSpecification

class ImageRepository(ABC):
    """Repository interface for loading and managing images"""
    
    @abstractmethod
    def list_images(self, directory: str) -> List[Image]:
        """List all images in a directory"""
        pass
        
    @abstractmethod
    def get_by_path(self, path: str) -> Optional[Image]:
        """Get a single image by path"""
        pass
        
    @abstractmethod
    def search_images(self, query: str) -> List[Image]:
        """Search for images based on query"""
        pass
        
    @abstractmethod
    def get_supported_extensions(self) -> Set[str]:
        """Get set of supported file extensions"""
        pass
        
    @abstractmethod
    def is_supported_extension(self, extension: str) -> bool:
        """Check if a file extension is supported"""
        pass
        
    @abstractmethod
    def validate_path(self, path: str) -> bool:
        """Validate if a path points to a supported image"""
        pass
        
    @abstractmethod
    def save(self, image: Image) -> bool:
        """Save an image and its metadata"""
        pass
        
    @abstractmethod
    def delete(self, path: str) -> bool:
        """Delete an image and its metadata"""
        pass
        
    @abstractmethod
    def find(self, specification: ImageSpecification) -> List[Image]:
        """Find images matching a specification"""
        pass
        
    @abstractmethod
    def update_rating(self, path: str, rating: int) -> bool:
        """Update rating for an image"""
        pass
        
    @abstractmethod
    def update_status(self, path: str, status: ImageStatus) -> bool:
        """Update status for an image"""
        pass
        
    @abstractmethod
    def update_tags(self, path: str, tags: set[str]) -> bool:
        """Update tags for an image"""
        pass
        
    @abstractmethod
    def update_metadata(self, path: str, metadata: Dict[str, Any]) -> bool:
        """Update custom metadata for an image"""
        pass
        
    @abstractmethod
    def get_metadata(self, path: str) -> Optional[Dict[str, Any]]:
        """Get metadata for an image"""
        pass
        
    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if an image exists"""
        pass 