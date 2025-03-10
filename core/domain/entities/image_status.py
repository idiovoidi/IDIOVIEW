"""Domain entity for image status"""

from enum import Enum, auto
from typing import Optional, Dict, List

class ImageStatus(Enum):
    """Review status for images"""
    PENDING = auto()
    APPROVED = auto()
    REJECTED = auto()
    NEEDS_WORK = auto()
    
    @classmethod
    def from_string(cls, status: str) -> 'ImageStatus':
        """Convert string to status enum"""
        status_map = {
            'pending': cls.PENDING,
            'approved': cls.APPROVED,
            'rejected': cls.REJECTED,
            'needs_work': cls.NEEDS_WORK
        }
        return status_map.get(status.lower(), cls.PENDING)
        
    def __str__(self) -> str:
        """Convert status to string"""
        return self.name.lower().replace('_', ' ')
        
    @property
    def display_name(self) -> str:
        """Get formatted display name"""
        return self.name.title().replace('_', ' ')
        
    @property
    def color(self) -> str:
        """Get color code for status"""
        color_map = {
            ImageStatus.PENDING: '#808080',     # Gray
            ImageStatus.APPROVED: '#00C853',    # Green
            ImageStatus.REJECTED: '#D50000',    # Red
            ImageStatus.NEEDS_WORK: '#FF6D00'   # Orange
        }
        return color_map[self]
        
    @property
    def description(self) -> str:
        """Get status description"""
        desc_map = {
            ImageStatus.PENDING: "Not yet reviewed",
            ImageStatus.APPROVED: "Approved for use",
            ImageStatus.REJECTED: "Rejected from use",
            ImageStatus.NEEDS_WORK: "Requires modifications"
        }
        return desc_map[self]
        
    @classmethod
    def get_all_statuses(cls) -> List['ImageStatus']:
        """Get list of all available statuses"""
        return list(cls)
        
    @classmethod
    def get_active_statuses(cls) -> List['ImageStatus']:
        """Get list of active statuses (excluding rejected)"""
        return [s for s in cls if s != cls.REJECTED]
        
    def is_active(self) -> bool:
        """Check if status is active"""
        return self != ImageStatus.REJECTED
        
    def is_final(self) -> bool:
        """Check if status is final"""
        return self in (ImageStatus.APPROVED, ImageStatus.REJECTED) 