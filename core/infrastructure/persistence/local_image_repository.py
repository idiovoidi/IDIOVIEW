import os
from typing import List, Optional, Dict, Any, Set
import logging
from pathlib import Path
import json
from datetime import datetime

from core.domain.repositories.image_repository import ImageRepository
from core.domain.entities.image import Image
from core.domain.entities.image_status import ImageStatus
from core.domain.specifications.image_specifications import ImageSpecification
from core.domain.entities.image_metadata import ImageMetadata
from ...infrastructure.config.app_config import AppConfig
from ...infrastructure.utils.image_utils import open_image_efficient, get_image_dimensions

logger = logging.getLogger(__name__)

class LocalImageRepository(ImageRepository):
    """Local filesystem implementation of image repository"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.supported_extensions: Set[str] = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'
        }
        self.base_directory = config.get_images_dir()
        self._metadata_cache: Dict[str, Dict[str, Any]] = {}
        
    def get_by_path(self, path: str) -> Optional[Image]:
        """Retrieve an image by its path"""
        try:
            if not os.path.exists(path):
                return None
                
            # Get file stats
            stats = os.stat(path)
            
            # Create metadata
            metadata = ImageMetadata(
                width=0,  # Will be filled when needed
                height=0,  # Will be filled when needed
                format=os.path.splitext(path)[1][1:],
                size_bytes=stats.st_size,
                created_at=datetime.fromtimestamp(stats.st_ctime),
                modified_at=datetime.fromtimestamp(stats.st_mtime)
            )
            
            # Add cached metadata if available
            if cached_metadata := self._metadata_cache.get(path):
                metadata.custom_metadata.update(cached_metadata)
            
            return Image(
                path=path,
                name=os.path.basename(path),
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error retrieving image {path}: {e}")
            return None
            
    def save(self, image: Image) -> bool:
        """Save an image and its metadata"""
        try:
            if not image.exists:
                return False
                
            # Cache metadata
            self._metadata_cache[image.path] = image.metadata.custom_metadata
            return True
        except Exception as e:
            logger.error(f"Error saving image {image.path}: {e}")
            return False
            
    def delete(self, path: str) -> bool:
        """Delete an image and its metadata"""
        try:
            if not os.path.exists(path):
                return False
                
            # Remove file
            os.remove(path)
            
            # Remove from cache
            self._metadata_cache.pop(path, None)
            
            return True
        except Exception as e:
            logger.error(f"Error deleting image {path}: {e}")
            return False
            
    def exists(self, path: str) -> bool:
        """Check if an image exists"""
        return os.path.exists(path)
            
    def list_images(self, directory: str, include_subfolders: bool = False) -> List[Image]:
        """List all images in a directory"""
        try:
            images = []
            if isinstance(directory, tuple):
                # Handle case where directory is passed as tuple
                directory = directory[0]
                
            directory_path = Path(directory)
            
            logger.debug(f"Scanning directory: {directory} (include_subfolders: {include_subfolders})")
            logger.debug(f"Supported extensions: {self.supported_extensions}")
            
            if not directory_path.exists():
                logger.error(f"Directory does not exist: {directory}")
                return []
                
            # Function to process a single directory
            def process_directory(dir_path: Path) -> None:
                try:
                    entries = list(dir_path.iterdir())
                    logger.debug(f"Found {len(entries)} entries in {dir_path}")
                    
                    for entry in entries:
                        if entry.is_file() and entry.suffix.lower() in self.supported_extensions:
                            logger.debug(f"Found supported image file: {entry}")
                            if image := self._load_image(entry):
                                logger.debug(f"Successfully loaded image: {entry}")
                                images.append(image)
                            else:
                                logger.warning(f"Failed to load image: {entry}")
                        elif include_subfolders and entry.is_dir():
                            logger.debug(f"Processing subdirectory: {entry}")
                            process_directory(entry)
                        else:
                            logger.debug(f"Skipping non-image entry: {entry}")
                except Exception as e:
                    logger.error(f"Error processing directory {dir_path}: {e}")
            
            # Start processing from the root directory
            process_directory(directory_path)
            
            logger.debug(f"Found {len(images)} valid images in {directory}")
            return images
            
        except Exception as e:
            logger.error(f"Error loading directory {directory}: {e}", exc_info=True)
            return []
            
    def find(self, specification: ImageSpecification) -> List[Image]:
        """Find images matching a specification"""
        try:
            # Get all images in base directory
            all_images = []
            for root, _, files in os.walk(self.base_directory):
                for file in files:
                    if self._is_image_file(file):
                        path = os.path.join(root, file)
                        if image := self.get_by_path(path):
                            all_images.append(image)
            
            # Filter by specification
            return [img for img in all_images if specification.is_satisfied_by(img)]
            
        except Exception as e:
            logger.error(f"Error finding images: {e}")
            return []
            
    def update_rating(self, path: str, rating: int) -> bool:
        """Update rating for an image"""
        try:
            # Update directly in metadata cache
            metadata = self._metadata_cache.setdefault(path, {})
            metadata['rating'] = rating
            return True
        except Exception as e:
            logger.error(f"Error updating rating for {path}: {e}")
            return False
            
    def update_status(self, path: str, status: ImageStatus) -> bool:
        """Update status for an image"""
        try:
            metadata = self.get_metadata(path) or {}
            metadata['status'] = status.name.lower()
            return self.update_metadata(path, metadata)
        except Exception as e:
            logger.error(f"Error updating status for {path}: {e}")
            return False
            
    def update_tags(self, path: str, tags: Set[str]) -> bool:
        """Update tags for an image"""
        try:
            metadata = self.get_metadata(path) or {}
            metadata['tags'] = list(tags)
            return self.update_metadata(path, metadata)
        except Exception as e:
            logger.error(f"Error updating tags for {path}: {e}")
            return False
            
    def update_metadata(self, path: str, metadata: Dict[str, Any]) -> bool:
        """Update metadata for an image"""
        try:
            current = self._metadata_cache.get(path, {})
            current.update(metadata)
            self._metadata_cache[path] = current
            return True
        except Exception as e:
            logger.error(f"Error updating metadata for {path}: {e}")
            return False
            
    def get_metadata(self, path: str) -> Optional[Dict[str, Any]]:
        """Get metadata for an image"""
        try:
            # Return a copy of the metadata to prevent modification
            if path in self._metadata_cache:
                return dict(self._metadata_cache[path])
            return {}
        except Exception as e:
            logger.error(f"Error getting metadata for {path}: {e}")
            return {}
            
    def save_rating(self, path: str, rating: int) -> bool:
        """Save rating for an image"""
        return self.update_metadata(path, {'rating': str(rating)})
        
    def search_images(self, query: str) -> List[Image]:
        """Search for images based on query"""
        # TODO: Implement image search
        return []
            
    def get_supported_extensions(self) -> Set[str]:
        """Get set of supported file extensions"""
        return self.supported_extensions.copy()
        
    def is_supported_extension(self, extension: str) -> bool:
        """Check if a file extension is supported"""
        return extension.lower() in self.supported_extensions
        
    def validate_path(self, path: str) -> bool:
        """Validate if a path points to a supported image"""
        try:
            path_obj = Path(path)
            return (
                path_obj.exists() and
                path_obj.is_file() and
                path_obj.suffix.lower() in self.supported_extensions
            )
        except Exception:
            return False
            
    def _load_image(self, path: Path) -> Optional[Image]:
        """Load image and extract metadata"""
        try:
            logger.debug(f"Attempting to load image: {path}")
            
            # First verify the file exists and is readable
            if not path.exists():
                logger.error(f"Image file does not exist: {path}")
                return None
            
            if not os.access(path, os.R_OK):
                logger.error(f"Image file is not readable: {path}")
                return None
            
            # Get dimensions efficiently
            if dimensions := get_image_dimensions(path):
                width, height = dimensions
                
                # Validate dimensions
                if width <= 0 or height <= 0:
                    logger.error(f"Invalid image dimensions for {path}: {width}x{height}")
                    return None
                
                logger.debug(f"Image dimensions valid: {width}x{height}")
                
                # Extract basic metadata
                metadata = ImageMetadata(
                    width=width,
                    height=height,
                    format=path.suffix[1:],
                    size_bytes=path.stat().st_size,
                    created_at=datetime.fromtimestamp(path.stat().st_ctime),
                    modified_at=datetime.fromtimestamp(path.stat().st_mtime)
                )
                
                # Extract InvokeAI metadata if available
                if img := open_image_efficient(path):
                    with img:
                        if 'invokeai_metadata' in img.info:
                            try:
                                invoke_metadata = json.loads(img.info['invokeai_metadata'])
                                metadata.custom_metadata.update(invoke_metadata)
                            except Exception as e:
                                logger.debug(f"Error parsing InvokeAI metadata for {path}: {e}")
                
                # Create image entity
                image = Image(
                    path=str(path),
                    name=path.name,
                    metadata=metadata
                )
                
                logger.debug(f"Successfully loaded image: {path}")
                return image
                
            return None
            
        except Exception as e:
            logger.error(f"Error loading image {path}: {e}")
            return None
        
    def _validate_image_entity(self, image: Image) -> bool:
        """Validate an image entity has all required properties"""
        try:
            # Check required attributes
            if not all([image.path, image.name, image.metadata]):
                return False
            
            # Validate dimensions
            if not (isinstance(image.metadata.width, int) and 
                    isinstance(image.metadata.height, int) and
                    image.metadata.width > 0 and 
                    image.metadata.height > 0):
                return False
            
            # Validate file exists
            if not Path(image.path).exists():
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating image entity: {e}")
            return False
        
    @staticmethod
    def _is_image_file(filename: str) -> bool:
        """Check if file is an image based on extension"""
        extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        return os.path.splitext(filename)[1].lower() in extensions 