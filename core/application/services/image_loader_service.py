from typing import List, Optional, Dict, Any, Set
import logging
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QImage
from core.domain.repositories.image_repository import ImageRepository
from core.domain.entities.image import Image
from core.infrastructure.cache.thumbnail_cache import ThumbnailCache
from core.infrastructure.utils.worker_pool import WorkerPool
from core.infrastructure.utils.qt_utils import load_qimage, is_valid_qimage

logger = logging.getLogger(__name__)

class ImageLoaderService(QObject):
    """Application service for loading and managing images with background processing"""
    
    # Define signals
    directory_loaded = pyqtSignal(list)  # Emits list of loaded images
    load_error = pyqtSignal(str)  # Emits error message
    loading_progress = pyqtSignal(int, int)  # Emits (loaded_count, total_count)
    thumbnail_batch_ready = pyqtSignal(list)  # Emits list of processed images
    thumbnail_ready = pyqtSignal(str, QImage)  # Emits (image_path, thumbnail_image)
    
    def __init__(self, image_repository: ImageRepository, thumbnail_cache: ThumbnailCache):
        super().__init__()
        self.image_repository = image_repository
        self.thumbnail_cache = thumbnail_cache
        
        # Create worker pools
        self.directory_worker = WorkerPool(
            process_func=self._load_images_worker,
            num_workers=1,  # Single worker for directory loading
            name="DirectoryLoader"
        )
        
        self.thumbnail_worker = WorkerPool(
            process_func=self._process_thumbnail_batch,
            num_workers=4,
            name="ThumbnailProcessor"
        )
        
        # Connect to thumbnail cache signals
        self.thumbnail_cache.thumbnail_ready.connect(self._on_thumbnail_ready)
        
        # Initialize state
        self._pending_images = []
        self._batch_size = 50
        self._is_loading = False
        
    def _on_thumbnail_ready(self, original_path: str, thumbnail_path: str) -> None:
        """Handle thumbnail ready from cache"""
        try:
            # Load the thumbnail as QImage
            if image := load_qimage(thumbnail_path):
                # Emit the loaded thumbnail
                self.thumbnail_ready.emit(original_path, image)
        except Exception as e:
            logger.error(f"Error handling thumbnail ready: {e}")
            
    def load_directory(self, directory_path: str, batch_size: int = 50, include_subfolders: bool = False) -> None:
        """Start loading directory with batch processing"""
        try:
            self._batch_size = batch_size
            self._is_loading = True
            self._pending_images = []
            
            # Queue directory loading
            self.directory_worker.put((directory_path, include_subfolders))
            
        except Exception as e:
            logger.error(f"Error starting directory load: {e}")
            self.load_error.emit(str(e))
            self._is_loading = False
            
    def _load_images_worker(self, args) -> None:
        """Worker function for loading directory contents"""
        try:
            # Unpack arguments
            if isinstance(args, tuple):
                directory_path, include_subfolders = args
            else:
                directory_path = args
                include_subfolders = False
                
            # Load images from repository
            images = self.image_repository.list_images(directory_path, include_subfolders)
            if not images:
                self.load_error.emit(f"No images found in directory: {directory_path}")
                return
                
            # Store pending images and start batch processing
            self._pending_images = list(images)
            self._process_next_batch()
            
        except Exception as e:
            logger.error(f"Error loading directory {directory_path}: {e}")
            self.load_error.emit(str(e))
        finally:
            self._is_loading = False
            
    def _process_next_batch(self) -> None:
        """Process next batch of pending images"""
        try:
            if not self._pending_images:
                return
                
            # Get next batch
            batch = self._pending_images[:self._batch_size]
            self._pending_images = self._pending_images[self._batch_size:]
            
            # Queue batch processing
            self.thumbnail_worker.put(batch)
            
            # Update progress
            total = len(batch) + len(self._pending_images)
            self.loading_progress.emit(len(batch), total)
            
            # Emit batch
            self.thumbnail_batch_ready.emit(batch)
            
            # Continue processing if more pending
            if self._pending_images:
                self._process_next_batch()
                
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            
    def _process_thumbnail_batch(self, images: List[Image]) -> None:
        """Process a batch of images for thumbnails"""
        try:
            for image in images:
                # Check if thumbnail exists in cache
                if cached_image := self.thumbnail_cache.get_thumbnail(image.path):
                    if isinstance(cached_image, QImage):
                        # Emit immediately if we have a cached image
                        self.thumbnail_ready.emit(image.path, cached_image)
                    else:
                        # Load from cached path
                        self.thumbnail_cache.put(image.path, image.path)
                else:
                    # Queue for generation
                    self.thumbnail_cache.put(image.path, image.path)
        except Exception as e:
            logger.error(f"Error processing thumbnail batch: {e}")

    def cleanup(self):
        """Clean up resources"""
        try:
            self.directory_worker.cleanup()
            self.thumbnail_worker.cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def get_image(self, image_path: str) -> Optional[Image]:
        """Get a single image by path"""
        try:
            return self.image_repository.get_by_path(image_path)
        except Exception as e:
            logger.error(f"Error getting image {image_path}: {e}")
            return None
            
    def search_images(self, query: str) -> List[Image]:
        """Search for images based on query"""
        try:
            return self.image_repository.search_images(query)
        except Exception as e:
            logger.error(f"Error searching images: {e}")
            return []
            
    def get_thumbnail(self, image_path: str) -> Optional[QImage]:
        """Get thumbnail for an image, optionally generating if missing"""
        try:
            # Try to get from cache
            if cached := self.thumbnail_cache.get_thumbnail(image_path):
                if isinstance(cached, QImage):
                    return cached
                else:
                    # Load from cached path
                    if image := load_qimage(str(cached)):
                        return image
            
            # Queue generation if not found
            self.thumbnail_cache.put(image_path, image_path)
            return None
            
        except Exception as e:
            logger.error(f"Error getting thumbnail for {image_path}: {e}")
            return None
            
    def generate_thumbnail(self, image_path: str, priority: bool = False) -> None:
        """Generate thumbnail for an image"""
        try:
            self.thumbnail_cache.put(image_path, image_path, priority)
        except Exception as e:
            logger.error(f"Error generating thumbnail for {image_path}: {e}")
            
    def batch_generate_thumbnails(self, image_paths: List[str], priority: bool = False) -> None:
        """Generate thumbnails for multiple images"""
        for path in image_paths:
            self.generate_thumbnail(path, priority)
            
    def clear_cache(self) -> None:
        """Clear the thumbnail cache"""
        try:
            self.thumbnail_cache.clear()
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            
    def get_supported_extensions(self) -> Set[str]:
        """Get set of supported file extensions"""
        return self.image_repository.get_supported_extensions()
        
    def is_supported_extension(self, extension: str) -> bool:
        """Check if a file extension is supported"""
        return self.image_repository.is_supported_extension(extension)
        
    def validate_path(self, path: str) -> bool:
        """Validate if a path points to a supported image"""
        return self.image_repository.validate_path(path)

    def get_image_dimensions(self, image_path: str) -> tuple[int, int]:
        """Get image dimensions"""
        try:
            if image := self.get_image(image_path):
                return image.metadata.width, image.metadata.height
            return 0, 0
        except Exception as e:
            logger.error(f"Error getting dimensions for {image_path}: {e}")
            return 0, 0 