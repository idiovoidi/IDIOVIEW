"""Utility module for image handling and PIL configuration"""

import logging
from typing import Optional, Tuple, Union
from pathlib import Path
from PIL import Image, ImageFile

# Configure PIL globally to prevent window creation and handle large images
ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None  # Disable DecompressionBomb check
Image.warnings.simplefilter('ignore')  # Suppress PIL warnings

logger = logging.getLogger(__name__)

def open_image_efficient(image_path: str, draft_size: Optional[Tuple[int, int]] = None) -> Optional[Image.Image]:
    """Open an image efficiently using PIL's draft mode if size is provided
    
    Args:
        image_path: Path to the image file
        draft_size: Optional target size for draft mode
        
    Returns:
        PIL Image object or None if opening fails
    """
    try:
        # Open image
        img = Image.open(image_path)
        
        # Use draft mode if size provided
        if draft_size is not None:
            try:
                img.draft('RGB', draft_size)
            except Exception as e:
                logger.warning(f"Draft mode failed for {image_path}: {e}")
        
        # Force load image data
        img.load()
        return img
        
    except Exception as e:
        logger.error(f"Error opening image {image_path}: {e}", exc_info=True)
        return None

def get_image_dimensions(path: Union[str, Path]) -> Optional[Tuple[int, int]]:
    """
    Get image dimensions efficiently without loading the full image.
    
    Args:
        path: Path to the image file
        
    Returns:
        Tuple of (width, height) or None if failed
    """
    try:
        with open(str(path), 'rb') as f:
            img = Image.open(f)
            img.draft('RGB', img.size)  # Use draft mode for efficiency
            return img.size
    except Exception as e:
        logger.error(f"Error getting image dimensions for {path}: {e}")
        return None

def convert_to_rgb(img: Image.Image) -> Image.Image:
    """
    Convert image to RGB mode efficiently.
    
    Args:
        img: PIL Image object
        
    Returns:
        RGB version of the image
    """
    if img.mode in ('RGBA', 'LA'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if 'A' in img.mode:
            alpha = img.split()[-1]
            background.paste(img, mask=alpha)
        return background
    elif img.mode != 'RGB':
        return img.convert('RGB')
    return img

def save_image_optimized(img: Image.Image, output_path: Path, quality: int = 85) -> bool:
    """Save image with optimization
    
    Args:
        img: PIL Image to save
        output_path: Path to save to
        quality: JPEG quality (0-100)
        
    Returns:
        True if save successful, False otherwise
    """
    try:
        # Ensure RGB mode
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        # Save with optimization
        img.save(
            output_path,
            'JPEG',
            quality=quality,
            optimize=True,
            progressive=True
        )
        return True
        
    except Exception as e:
        logger.error(f"Error saving image to {output_path}: {e}", exc_info=True)
        return False 