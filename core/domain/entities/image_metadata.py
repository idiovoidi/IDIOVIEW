"""Domain entity for image metadata"""

from dataclasses import dataclass, field
from typing import Dict, Any, Set
from datetime import datetime

@dataclass
class ImageMetadata:
    """Core domain entity representing image metadata"""
    
    # Basic properties
    width: int
    height: int
    format: str
    size_bytes: int
    created_at: datetime
    modified_at: datetime
    
    # Optional properties with defaults
    rating: int = field(default=0)
    tags: Set[str] = field(default_factory=set)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def size_mb(self) -> float:
        """Get file size in megabytes"""
        return self.size_bytes / (1024 * 1024)
        
    @property
    def aspect_ratio(self) -> float:
        """Get image aspect ratio"""
        return self.width / self.height if self.height > 0 else 0
        
    def update(self, metadata: Dict[str, Any]) -> None:
        """Update custom metadata"""
        self.custom_metadata.update(metadata)
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get custom metadata value"""
        return self.custom_metadata.get(key, default)
        
    def add_tag(self, tag: str) -> None:
        """Add a tag"""
        if tag and isinstance(tag, str):
            self.tags.add(tag.lower().strip())
        
    def remove_tag(self, tag: str) -> None:
        """Remove a tag"""
        if tag and isinstance(tag, str):
            self.tags.discard(tag.lower().strip())
        
    def has_tag(self, tag: str) -> bool:
        """Check if image has tag"""
        return tag.lower().strip() in self.tags if tag and isinstance(tag, str) else False
        
    def clear_tags(self) -> None:
        """Clear all tags"""
        self.tags.clear()
        
    def set_rating(self, rating: int) -> None:
        """Set image rating (0-5)"""
        if isinstance(rating, int) and 0 <= rating <= 5:
            self.rating = rating
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary"""
        return {
            'width': self.width,
            'height': self.height,
            'format': self.format,
            'size_bytes': self.size_bytes,
            'created_at': self.created_at.timestamp(),
            'modified_at': self.modified_at.timestamp(),
            'rating': self.rating,
            'tags': list(self.tags),
            'custom_metadata': self.custom_metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImageMetadata':
        """Create metadata from dictionary"""
        return cls(
            width=data['width'],
            height=data['height'],
            format=data['format'],
            size_bytes=data['size_bytes'],
            created_at=datetime.fromtimestamp(data['created_at']),
            modified_at=datetime.fromtimestamp(data['modified_at']),
            rating=data.get('rating', 0),
            tags=set(data.get('tags', [])),
            custom_metadata=data.get('custom_metadata', {})
        ) 