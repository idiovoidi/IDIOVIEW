"""Utility functions for Qt image operations"""

import logging
from pathlib import Path
from typing import Optional, Tuple, Union
from PyQt6.QtGui import QImage
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)

def load_qimage(image_path: Union[str, Path]) -> Optional[QImage]:
    """
    Safely load a QImage from a file path.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        QImage if successfully loaded, None otherwise
    """
    try:
        image = QImage(str(image_path))
        if not image.isNull():
            return image
        logger.warning(f"Failed to load valid image from {image_path}")
        return None
    except Exception as e:
        logger.error(f"Error loading image {image_path}: {e}")
        return None

def scale_qimage(image: QImage, size: Tuple[int, int], keep_aspect: bool = True) -> Optional[QImage]:
    """
    Safely scale a QImage to the target size.
    
    Args:
        image: Source QImage
        size: Target size as (width, height)
        keep_aspect: Whether to maintain aspect ratio
        
    Returns:
        Scaled QImage if successful, None otherwise
    """
    try:
        if image.isNull():
            return None
            
        aspect_mode = Qt.AspectRatioMode.KeepAspectRatio if keep_aspect else Qt.AspectRatioMode.IgnoreAspectRatio
        return image.scaled(
            size[0], size[1],
            aspect_mode,
            Qt.TransformationMode.SmoothTransformation
        )
    except Exception as e:
        logger.error(f"Error scaling image: {e}")
        return None

def is_valid_qimage(image: Optional[QImage]) -> bool:
    """
    Check if a QImage is valid and usable.
    
    Args:
        image: QImage to validate
        
    Returns:
        True if image is valid, False otherwise
    """
    return image is not None and not image.isNull() 