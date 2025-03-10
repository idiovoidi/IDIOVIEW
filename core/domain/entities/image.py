"""Domain entity for images"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Set
from datetime import datetime
from pathlib import Path

from ...infrastructure.utils.image_utils import open_image_efficient, get_image_dimensions
from .image_metadata import ImageMetadata
from .image_status import ImageStatus

logger = logging.getLogger(__name__)

@dataclass
class Image:
    """Core domain entity representing an image"""
    
    # Basic properties
    path: str
    name: str
    metadata: ImageMetadata
    
    # Optional properties
    status: ImageStatus = field(default=ImageStatus.PENDING)
    selected: bool = field(default=False)
    
    def __post_init__(self):
        """Validate image properties"""
        if not self.path or not isinstance(self.path, str):
            raise ValueError("Invalid image path")
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Invalid image name")
        if not isinstance(self.metadata, ImageMetadata):
            raise ValueError("Invalid metadata type")
        if not isinstance(self.status, ImageStatus):
            raise ValueError("Invalid status type")
    
    @property
    def width(self) -> int:
        """Get image width"""
        return self.metadata.width
        
    @property
    def height(self) -> int:
        """Get image height"""
        return self.metadata.height
        
    @property
    def exists(self) -> bool:
        """Check if image file exists"""
        return os.path.exists(self.path)
        
    @property
    def extension(self) -> str:
        """Get file extension"""
        return Path(self.path).suffix.lower()
        
    @property
    def directory(self) -> str:
        """Get parent directory"""
        return str(Path(self.path).parent)
        
    @property
    def rating(self) -> int:
        """Get image rating"""
        return self.metadata.rating
        
    @property
    def tags(self) -> Set[str]:
        """Get image tags"""
        return self.metadata.tags.copy()
        
    @property
    def size_mb(self) -> float:
        """Get file size in megabytes"""
        return self.metadata.size_mb
        
    def update_dimensions(self, width: int, height: int) -> None:
        """Update image dimensions"""
        if width <= 0 or height <= 0:
            raise ValueError(f"Invalid dimensions: {width}x{height}")
        self.metadata.width = width
        self.metadata.height = height
        
    def update_rating(self, rating: int) -> None:
        """Update image rating"""
        self.metadata.set_rating(rating)
            
    def update_status(self, status: ImageStatus) -> None:
        """Update review status"""
        if not isinstance(status, ImageStatus):
            raise ValueError("Invalid status type")
        self.status = status
        
    def add_tag(self, tag: str) -> None:
        """Add a tag"""
        self.metadata.add_tag(tag)
        
    def remove_tag(self, tag: str) -> None:
        """Remove a tag"""
        self.metadata.remove_tag(tag)
        
    def has_tag(self, tag: str) -> bool:
        """Check if image has tag"""
        return self.metadata.has_tag(tag)
        
    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """Update custom metadata"""
        self.metadata.update(metadata)
        
    def get_metadata_value(self, key: str) -> Optional[Any]:
        """Get custom metadata value"""
        return self.metadata.get(key)
        
    def select(self) -> None:
        """Select the image"""
        self.selected = True
        
    def deselect(self) -> None:
        """Deselect the image"""
        self.selected = False
        
    def toggle_selection(self) -> None:
        """Toggle selection state"""
        self.selected = not self.selected
        
    def delete(self) -> bool:
        """Delete the image file"""
        try:
            if self.exists:
                os.remove(self.path)
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting image {self.path}: {e}")
            return False
            
    def move_to(self, destination: str) -> bool:
        """Move image to new location"""
        try:
            if not self.exists:
                return False
                
            # Create destination directory if needed
            dest_dir = os.path.dirname(destination)
            os.makedirs(dest_dir, exist_ok=True)
            
            # Move file
            os.rename(self.path, destination)
            
            # Update path
            self.path = destination
            self.name = os.path.basename(destination)
            
            return True
            
        except Exception as e:
            logger.error(f"Error moving image {self.path}: {e}")
            return False
            
    def copy_to(self, destination: str) -> bool:
        """Copy image to new location"""
        try:
            if not self.exists:
                return False
                
            # Create destination directory if needed
            dest_dir = os.path.dirname(destination)
            os.makedirs(dest_dir, exist_ok=True)
            
            # Copy file efficiently
            if img := open_image_efficient(self.path):
                with img:
                    img.save(destination, quality=95, optimize=True)
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error copying image {self.path}: {e}")
            return False
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert image to dictionary"""
        return {
            'path': self.path,
            'name': self.name,
            'metadata': self.metadata.to_dict(),
            'status': self.status.name,
            'selected': self.selected
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Image':
        """Create image from dictionary"""
        return cls(
            path=data['path'],
            name=data['name'],
            metadata=ImageMetadata.from_dict(data['metadata']),
            status=ImageStatus.from_string(data['status']),
            selected=data.get('selected', False)
        )
            
    @classmethod
    def from_file(cls, file_path: str) -> Optional['Image']:
        """Create Image instance from file path"""
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"File not found: {file_path}")
                return None
                
            # Get basic file info
            stats = path.stat()
            
            # Get image dimensions efficiently
            if dimensions := get_image_dimensions(file_path):
                width, height = dimensions
                
                # Create metadata
                metadata = ImageMetadata(
                    width=width,
                    height=height,
                    format=path.suffix[1:].lower(),
                    size_bytes=stats.st_size,
                    created_at=datetime.fromtimestamp(stats.st_ctime),
                    modified_at=datetime.fromtimestamp(stats.st_mtime)
                )
                
                # Create image instance
                return cls(
                    path=str(path),
                    name=path.name,
                    metadata=metadata
                )
                
            return None
            
        except Exception as e:
            logger.error(f"Error creating image from file: {e}")
            return None 