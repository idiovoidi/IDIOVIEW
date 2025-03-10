from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Set
from ..entities.image import Image
from ..entities.image_status import ImageStatus

class ImageSpecification(ABC):
    """Base specification interface"""
    
    @abstractmethod
    def is_satisfied_by(self, image: Image) -> bool:
        """Check if image satisfies specification"""
        pass
        
    def and_(self, other: 'ImageSpecification') -> 'AndSpecification':
        """Combine with another specification using AND"""
        return AndSpecification(self, other)
        
    def or_(self, other: 'ImageSpecification') -> 'OrSpecification':
        """Combine with another specification using OR"""
        return OrSpecification(self, other)
        
    def not_(self) -> 'NotSpecification':
        """Negate this specification"""
        return NotSpecification(self)

class AndSpecification(ImageSpecification):
    """Combine specifications with AND"""
    
    def __init__(self, *specifications: ImageSpecification):
        self.specifications = specifications
        
    def is_satisfied_by(self, image: Image) -> bool:
        return all(spec.is_satisfied_by(image) for spec in self.specifications)

class OrSpecification(ImageSpecification):
    """Combine specifications with OR"""
    
    def __init__(self, *specifications: ImageSpecification):
        self.specifications = specifications
        
    def is_satisfied_by(self, image: Image) -> bool:
        return any(spec.is_satisfied_by(image) for spec in self.specifications)

class NotSpecification(ImageSpecification):
    """Negate a specification"""
    
    def __init__(self, specification: ImageSpecification):
        self.specification = specification
        
    def is_satisfied_by(self, image: Image) -> bool:
        return not self.specification.is_satisfied_by(image)

# Concrete specifications
class RatingSpecification(ImageSpecification):
    """Filter images by minimum rating"""
    
    def __init__(self, min_rating: int):
        self.min_rating = min_rating
        
    def is_satisfied_by(self, image: Image) -> bool:
        return image.rating >= self.min_rating

class StatusSpecification(ImageSpecification):
    """Filter images by status"""
    
    def __init__(self, status: ImageStatus):
        self.status = status
        
    def is_satisfied_by(self, image: Image) -> bool:
        return image.status == self.status

class TagsSpecification(ImageSpecification):
    """Filter images by tags"""
    
    def __init__(self, tags: Set[str], match_all: bool = True):
        self.tags = {tag.lower() for tag in tags}
        self.match_all = match_all
        
    def is_satisfied_by(self, image: Image) -> bool:
        if self.match_all:
            return self.tags.issubset(image.tags)
        return bool(self.tags.intersection(image.tags))

class FileExtensionSpecification(ImageSpecification):
    """Filter images by file extension"""
    
    def __init__(self, extensions: Set[str]):
        self.extensions = {ext.lower() for ext in extensions}
        
    def is_satisfied_by(self, image: Image) -> bool:
        return image.extension.lower() in self.extensions

class ImageSizeSpecification(ImageSpecification):
    """Filter images by size range"""
    
    def __init__(self, min_size: int = 0, max_size: int = float('inf')):
        self.min_size = min_size
        self.max_size = max_size
        
    def is_satisfied_by(self, image: Image) -> bool:
        return self.min_size <= image.metadata.size_bytes <= self.max_size

class DateRangeSpecification(ImageSpecification):
    """Filter images by date range"""
    
    def __init__(self, start_date: datetime = None, end_date: datetime = None):
        self.start_date = start_date
        self.end_date = end_date
        
    def is_satisfied_by(self, image: Image) -> bool:
        if self.start_date and image.metadata.modified_at < self.start_date:
            return False
        if self.end_date and image.metadata.modified_at > self.end_date:
            return False
        return True 