"""Service for managing image metadata"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
import json

from ...domain.entities.image import Image as ImageEntity
from ...domain.entities.image_metadata import ImageMetadata
from ...infrastructure.config.app_config import AppConfig
from ...infrastructure.utils.image_utils import open_image_efficient, save_image_optimized

logger = logging.getLogger(__name__)

class MetadataService:
    """Service for managing image metadata"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        
    def get_metadata(self, image: ImageEntity) -> Dict[str, Any]:
        """Get metadata for an image"""
        try:
            # Return cached metadata if available
            if cached := self.config.metadata_cache.get(image.path):
                return cached
                
            # Extract metadata from image
            if img := open_image_efficient(image.path):
                with img:
                    metadata = {
                        'width': img.width,
                        'height': img.height,
                        'format': img.format,
                        'mode': img.mode,
                        'size': Path(image.path).stat().st_size
                    }
                    
                    # Extract InvokeAI metadata if available
                    if 'invokeai_metadata' in img.info:
                        try:
                            invoke_metadata = json.loads(img.info['invokeai_metadata'])
                            metadata.update(invoke_metadata)
                        except Exception as e:
                            logger.debug(f"Error parsing InvokeAI metadata: {e}")
                            
                    # Cache metadata
                    self.config.metadata_cache.put(image.path, metadata)
                    
                    return metadata
                    
            return {}
                
        except Exception as e:
            logger.error(f"Error getting metadata for {image.path}: {e}")
            return {}
            
    def update_metadata(self, image: ImageEntity, metadata: Dict[str, Any]) -> bool:
        """Update metadata for an image"""
        try:
            if img := open_image_efficient(image.path):
                with img:
                    # Convert metadata to string
                    metadata_str = json.dumps(metadata)
                    
                    # Update image metadata
                    img.info['invokeai_metadata'] = metadata_str
                    
                    # Save image with updated metadata
                    if save_image_optimized(img, image.path):
                        # Update cache
                        self.config.metadata_cache.put(image.path, metadata)
                        
                        # Update entity metadata
                        image.metadata.custom_metadata.update(metadata)
                        
                        return True
                        
            return False
                
        except Exception as e:
            logger.error(f"Error updating metadata for {image.path}: {e}")
            return False
            
    def get_metadata_field(self, 
                          image: ImageEntity, 
                          field: str, 
                          default: Any = None) -> Any:
        """Get a specific metadata field"""
        try:
            metadata = self.get_metadata(image)
            return metadata.get(field, default)
        except Exception as e:
            logger.error(f"Error getting metadata field {field}: {e}")
            return default
            
    def set_metadata_field(self, 
                          image: ImageEntity, 
                          field: str, 
                          value: Any) -> bool:
        """Set a specific metadata field"""
        try:
            metadata = self.get_metadata(image)
            metadata[field] = value
            return self.update_metadata(image, metadata)
        except Exception as e:
            logger.error(f"Error setting metadata field {field}: {e}")
            return False
            
    def clear_metadata(self, image: ImageEntity) -> bool:
        """Clear all metadata for an image"""
        try:
            if img := open_image_efficient(image.path):
                with img:
                    img.info.clear()
                    if save_image_optimized(img, image.path):
                        # Clear cache
                        self.config.metadata_cache.invalidate(image.path)
                        
                        # Clear entity metadata
                        image.metadata.custom_metadata.clear()
                        
                        return True
                        
            return False
                
        except Exception as e:
            logger.error(f"Error clearing metadata for {image.path}: {e}")
            return False 