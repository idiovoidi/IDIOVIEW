"""Service for handling image transformations"""

import logging
from pathlib import Path
from typing import Optional, Tuple

from ...domain.entities.image import Image as ImageEntity
from ...infrastructure.config.app_config import AppConfig
from ...infrastructure.utils.image_utils import open_image_efficient, save_image_optimized

logger = logging.getLogger(__name__)

class ImageTransformService:
    """Service for handling image transformations"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        
    def rotate_image(self, image: ImageEntity, degrees: int) -> bool:
        """Rotate an image by the specified degrees"""
        try:
            if img := open_image_efficient(image.path):
                with img:
                    # Rotate image
                    rotated = img.rotate(degrees, expand=True)
                    
                    # Save rotated image
                    if save_image_optimized(rotated, image.path):
                        # Update image metadata
                        image.metadata.width = rotated.width
                        image.metadata.height = rotated.height
                        return True
                        
            return False
                
        except Exception as e:
            logger.error(f"Error rotating image {image.path}: {e}")
            return False
            
    def mirror_image(self, image: ImageEntity, horizontal: bool = True) -> bool:
        """Mirror an image horizontally or vertically"""
        try:
            if img := open_image_efficient(image.path):
                with img:
                    # Mirror image
                    from PIL import Image
                    mirrored = img.transpose(
                        Image.Transpose.FLIP_LEFT_RIGHT if horizontal 
                        else Image.Transpose.FLIP_TOP_BOTTOM
                    )
                    
                    # Save mirrored image
                    return save_image_optimized(mirrored, image.path)
                    
            return False
                
        except Exception as e:
            logger.error(f"Error mirroring image {image.path}: {e}")
            return False
            
    def resize_image(self, 
                    image: ImageEntity, 
                    size: Tuple[int, int],
                    maintain_aspect: bool = True) -> bool:
        """Resize an image to the specified dimensions"""
        try:
            if img := open_image_efficient(image.path):
                with img:
                    from PIL import Image
                    # Calculate new size if maintaining aspect ratio
                    if maintain_aspect:
                        img.thumbnail(size, Image.Resampling.LANCZOS)
                        resized = img
                    else:
                        resized = img.resize(size, Image.Resampling.LANCZOS)
                    
                    # Save resized image
                    if save_image_optimized(resized, image.path):
                        # Update image metadata
                        image.metadata.width = resized.width
                        image.metadata.height = resized.height
                        return True
                        
            return False
                
        except Exception as e:
            logger.error(f"Error resizing image {image.path}: {e}")
            return False
            
    def crop_image(self, 
                   image: ImageEntity, 
                   box: Tuple[int, int, int, int]) -> bool:
        """Crop an image to the specified box (left, top, right, bottom)"""
        try:
            if img := open_image_efficient(image.path):
                with img:
                    # Crop image
                    cropped = img.crop(box)
                    
                    # Save cropped image
                    if save_image_optimized(cropped, image.path):
                        # Update image metadata
                        image.metadata.width = cropped.width
                        image.metadata.height = cropped.height
                        return True
                        
            return False
                
        except Exception as e:
            logger.error(f"Error cropping image {image.path}: {e}")
            return False
            
    def adjust_image(self, 
                    image: ImageEntity,
                    brightness: float = 1.0,
                    contrast: float = 1.0,
                    saturation: float = 1.0) -> bool:
        """Adjust image brightness, contrast, and saturation"""
        try:
            if img := open_image_efficient(image.path):
                with img:
                    from PIL import ImageEnhance
                    
                    # Apply adjustments
                    if brightness != 1.0:
                        img = ImageEnhance.Brightness(img).enhance(brightness)
                    if contrast != 1.0:
                        img = ImageEnhance.Contrast(img).enhance(contrast)
                    if saturation != 1.0:
                        img = ImageEnhance.Color(img).enhance(saturation)
                    
                    # Save adjusted image
                    return save_image_optimized(img, image.path)
                    
            return False
                
        except Exception as e:
            logger.error(f"Error adjusting image {image.path}: {e}")
            return False 