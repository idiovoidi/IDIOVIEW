from pathlib import Path
import json
import logging
import shutil
import time
from typing import Any, Dict, Optional, Set
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class CacheManager(ABC):
    """Base class for cache management"""
    
    def __init__(self, cache_dir: Path, max_age_days: int = 30):
        self.cache_dir = Path(cache_dir)
        self.max_age_seconds = max_age_days * 24 * 60 * 60
        self.index_file = self.cache_dir / "cache_index.json"
        self.cache_index: Dict[str, Dict[str, Any]] = {}
        
        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load cache index
        self._load_index()
        
    def _load_index(self):
        """Load cache index from file"""
        try:
            if self.index_file.exists():
                with open(self.index_file) as f:
                    self.cache_index = json.load(f)
        except Exception as e:
            logger.error(f"Error loading cache index: {e}")
            self.cache_index = {}
            
    def _save_index(self):
        """Save cache index to file"""
        try:
            with open(self.index_file, 'w') as f:
                json.dump(self.cache_index, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving cache index: {e}")
            
    def clear(self):
        """Clear all cached data"""
        try:
            # Remove all files
            shutil.rmtree(self.cache_dir)
            
            # Recreate directory
            self.cache_dir.mkdir(parents=True)
            
            # Reset index
            self.cache_index = {}
            self._save_index()
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            
    def cleanup(self):
        """Remove expired cache entries"""
        try:
            current_time = time.time()
            expired_keys = set()
            
            # Find expired entries
            for key, data in self.cache_index.items():
                if current_time - data['timestamp'] > self.max_age_seconds:
                    expired_keys.add(key)
                    
            # Remove expired entries
            for key in expired_keys:
                self.invalidate(key)
                
        except Exception as e:
            logger.error(f"Error cleaning cache: {e}")
            
    def invalidate(self, key: str):
        """Remove a specific cache entry"""
        try:
            if key in self.cache_index:
                # Get cache file path
                cache_path = self.cache_dir / self.cache_index[key]['filename']
                
                # Remove file if it exists
                if cache_path.exists():
                    cache_path.unlink()
                    
                # Remove from index
                del self.cache_index[key]
                self._save_index()
                
        except Exception as e:
            logger.error(f"Error invalidating cache entry: {e}")
            
    def get_size(self) -> int:
        """Get total size of cache in bytes"""
        try:
            total_size = 0
            for path in self.cache_dir.rglob('*'):
                if path.is_file():
                    total_size += path.stat().st_size
            return total_size
        except Exception as e:
            logger.error(f"Error calculating cache size: {e}")
            return 0
            
    def get_entry_count(self) -> int:
        """Get number of cache entries"""
        return len(self.cache_index)
        
    @abstractmethod
    def get(self, key: str) -> Optional[Path]:
        """Get path to cached file"""
        pass
        
    @abstractmethod
    def put(self, key: str, data: Any) -> bool:
        """Add entry to cache"""
        pass 