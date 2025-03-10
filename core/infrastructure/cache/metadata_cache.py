"""Metadata cache implementation"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from threading import Lock

logger = logging.getLogger(__name__)

class MetadataCache:
    """Cache for storing and retrieving image metadata"""
    
    def __init__(self, cache_dir: Path, max_size_mb: int = 1000):
        """Initialize metadata cache
        
        Args:
            cache_dir: Directory to store cached metadata
            max_size_mb: Maximum cache size in megabytes (default 1GB)
        """
        self.cache_dir = Path(cache_dir)
        self.max_size = max_size_mb * 1024 * 1024  # Convert to bytes
        self.cache_lock = Lock()
        self._ensure_cache_dir()
        
    def _ensure_cache_dir(self) -> None:
        """Ensure cache directory exists"""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Error creating cache directory: {e}")
            raise
            
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get metadata from cache"""
        try:
            with self.cache_lock:
                cache_file = self.cache_dir / f"{hash(key)}.json"
                if cache_file.exists():
                    with open(cache_file, 'r') as f:
                        return json.load(f)
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
        return None
        
    def put(self, key: str, metadata: Dict[str, Any]) -> bool:
        """Put metadata into cache"""
        try:
            with self.cache_lock:
                cache_file = self.cache_dir / f"{hash(key)}.json"
                with open(cache_file, 'w') as f:
                    json.dump(metadata, f)
                return True
        except Exception as e:
            logger.error(f"Error putting to cache: {e}")
            return False
            
    def invalidate(self, key: str) -> None:
        """Remove item from cache"""
        try:
            with self.cache_lock:
                cache_file = self.cache_dir / f"{hash(key)}.json"
                if cache_file.exists():
                    cache_file.unlink()
        except Exception as e:
            logger.error(f"Error invalidating cache item: {e}")
            
    def clear(self) -> None:
        """Clear all cached items"""
        try:
            with self.cache_lock:
                for cache_file in self.cache_dir.glob("*.json"):
                    cache_file.unlink()
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            
    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            # Implement cleanup if needed
            pass
        except Exception as e:
            logger.error(f"Error during cleanup: {e}") 