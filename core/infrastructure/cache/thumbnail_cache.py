from pathlib import Path
import hashlib
import logging
import time
import json
import os
from typing import Optional, Tuple, Dict, Any, Set, Union
from PIL import Image, ImageFile
from PIL.Image import DecompressionBombError
from queue import PriorityQueue, Empty, Queue
from threading import Thread, Event, Lock, Semaphore
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtGui import QImage
from collections import OrderedDict
import weakref

from core.domain.entities.image import Image as DomainImage
from core.domain.entities.image_metadata import ImageMetadata
from core.domain.entities.image_hash import ImageHash
from ...infrastructure.utils.image_utils import open_image_efficient, save_image_optimized
from ...infrastructure.utils.worker_pool import WorkerPool
from core.infrastructure.utils.qt_utils import load_qimage, scale_qimage, is_valid_qimage

# Configure PIL globally to prevent window creation
ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None  # Disable DecompressionBomb check

logger = logging.getLogger(__name__)

class ThumbnailCache(QObject):
    """Cache system for image thumbnails"""
    
    # Signals
    thumbnail_ready = pyqtSignal(str, str)  # Signals (original_path, thumbnail_path)
    thumbnail_error = pyqtSignal(str, str)  # Signals (original_path, error_message)
    
    def __init__(self, cache_dir: Path, max_size: Tuple[int, int] = (200, 200), num_workers: int = 4):
        super().__init__()
        
        # Store configuration
        self.cache_dir = Path(cache_dir)
        self.thumbnail_dir = self.cache_dir / "thumbnails"
        self.max_size = max_size
        
        # Initialize memory cache with LRU using OrderedDict
        self.memory_cache = OrderedDict()
        self.memory_cache_size = 200
        self.memory_cache_lock = Lock()
        
        # Track pending requests with regular dictionary and lock
        self.pending_requests = {}
        self.pending_lock = Lock()
        
        # Create cache directory
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize worker pool
        self.worker_pool = WorkerPool(
            process_func=self._generate_thumbnail_worker,
            num_workers=4,
            name="ThumbnailGenerator"
        )
        
    def _generate_thumbnail_worker(self, args: tuple):
        """Worker function for thumbnail generation"""
        image_path, original_path = args
        
        try:
            if thumbnail_path := self._generate_thumbnail(original_path, image_path):
                self.thumbnail_ready.emit(original_path, str(thumbnail_path))
                
                # Pre-load into memory cache
                try:
                    if image := load_qimage(str(thumbnail_path)):
                        self._add_to_memory_cache((original_path, self.max_size), image)
                except Exception as e:
                    logger.error(f"Error pre-loading thumbnail: {e}")
            else:
                self.thumbnail_error.emit(original_path, "Failed to generate thumbnail")
                
        except Exception as e:
            logger.error(f"Error processing thumbnail task: {e}")
        finally:
            # Clean up processing state
            with self.pending_lock:
                self.pending_requests.pop(original_path, None)

    def _generate_thumbnail(self, key: str, image_path: str) -> Optional[Path]:
        """Generate thumbnail for an image"""
        try:
            cache_path = self.thumbnail_dir / f"{self._get_cache_name(key)}.jpg"
            
            # Check if thumbnail already exists and is valid
            if cache_path.exists() and cache_path.stat().st_size > 0:
                return cache_path
                
            # Calculate target size for draft mode (2x final size for better quality)
            draft_size = (
                max(self.max_size[0] * 2, 400),
                max(self.max_size[1] * 2, 300)
            )
            
            # Open and process image in a single context
            img = None
            try:
                img = open_image_efficient(image_path, draft_size)
                if img is None:
                    logger.error(f"Failed to open image: {image_path}")
                    return None

                # Create thumbnail
                img.thumbnail(self.max_size, Image.Resampling.LANCZOS)
                
                # Save optimized JPEG
                if save_image_optimized(img, cache_path):
                    return cache_path
                return None

            except Exception as e:
                logger.error(f"Error processing image {image_path}: {e}", exc_info=True)
                return None
            finally:
                # Ensure image is closed
                if img is not None:
                    try:
                        img.close()
                    except Exception as e:
                        logger.error(f"Error closing image: {e}")
                        
        except Exception as e:
            logger.error(f"Error generating thumbnail for {image_path}: {str(e)}", exc_info=True)
            return None
            
    def _get_cache_name(self, key: str) -> str:
        """Generate cache filename using ImageHash"""
        return ImageHash.create_file_hash(key)
        
    def _add_to_memory_cache(self, cache_key: Tuple[str, Optional[Tuple[int, int]]], image: QImage) -> None:
        """Add to memory cache with LRU eviction"""
        try:
            with self.memory_cache_lock:
                # Remove oldest if at capacity
                while len(self.memory_cache) >= self.memory_cache_size:
                    self.memory_cache.popitem(last=False)
                    
                # Add new item (create a deep copy to ensure thread safety)
                self.memory_cache[cache_key] = image.copy()
                
        except Exception as e:
            logger.error(f"Error adding to memory cache: {e}")
            
    def cleanup(self):
        """Clean up resources"""
        try:
            logger.debug("Starting thumbnail cache cleanup")
            
            # Clean up worker pool
            self.worker_pool.cleanup()
            
            # Clear memory cache and pending requests
            with self.memory_cache_lock:
                self.memory_cache.clear()
            with self.pending_lock:
                self.pending_requests.clear()
                
            logger.debug("Completed thumbnail cache cleanup")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            
    def clear(self):
        """Clear all cached data"""
        try:
            logger.debug("Starting cache clear")
            self.cleanup()  # Stop processing first
            
            # Clear directories
            for file in self.thumbnail_dir.glob('*'):
                if file.is_file():
                    try:
                        file.unlink()
                    except Exception as e:
                        logger.error(f"Error deleting cache file {file}: {e}")
                        
            logger.debug("Completed cache clear")
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            
    def __del__(self):
        """Ensure cleanup on deletion"""
        try:
            self.cleanup()
        except:
            pass

    def get_thumbnail(self, key: str, size: Optional[tuple[int, int]] = None) -> Optional[QImage]:
        """Get thumbnail with improved caching"""
        try:
            # Check memory cache with size-specific key
            cache_key = (key, size) if size else (key, self.max_size)
            with self.memory_cache_lock:
                if cache_key in self.memory_cache:
                    image = self.memory_cache[cache_key]
                    if is_valid_qimage(image):
                        # Move to end (most recently used)
                        self.memory_cache.pop(cache_key)
                        self.memory_cache[cache_key] = image
                        return image
                    
            # Check disk cache
            cache_path = self.thumbnail_dir / f"{self._get_cache_name(key)}.jpg"
            if cache_path.exists() and cache_path.stat().st_size > 0:
                try:
                    if image := load_qimage(str(cache_path)):
                        # Scale if needed
                        if size and size != self.max_size:
                            if scaled := scale_qimage(image, size):
                                # Add to memory cache
                                self._add_to_memory_cache(cache_key, scaled)
                                return scaled
                        else:
                            # Add to memory cache
                            self._add_to_memory_cache(cache_key, image)
                            return image
                        
                    # Invalid thumbnail
                    cache_path.unlink(missing_ok=True)
                except Exception:
                    logger.warning(f"Invalid thumbnail for {key}, removing")
                    cache_path.unlink(missing_ok=True)
                    
            return None
            
        except Exception as e:
            logger.error(f"Error getting thumbnail for {key}: {e}")
            return None

    def put(self, image_path: str, original_path: str, priority: bool = False) -> None:
        """Queue thumbnail generation using worker pool"""
        try:
            # Check if already in memory cache
            cache_key = (original_path, self.max_size)
            with self.memory_cache_lock:
                if cache_key in self.memory_cache:
                    return

            # Check if already pending
            with self.pending_lock:
                if original_path in self.pending_requests:
                    return
                self.pending_requests[original_path] = True

            # Queue for processing
            self.worker_pool.put((image_path, original_path), priority=priority)
            
        except Exception as e:
            logger.error(f"Error queueing thumbnail generation: {e}")
            with self.pending_lock:
                self.pending_requests.pop(original_path, None) 