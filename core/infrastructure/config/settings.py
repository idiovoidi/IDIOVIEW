"""Application settings management"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import json
import logging
from .user_config import UserConfigManager
from .savedfolders import SavedFoldersManager

from .constants import DEFAULT_PATHS, THUMBNAIL_SIZE

logger = logging.getLogger(__name__)

@dataclass
class AppSettings:
    """Application settings with environment variable support"""
    
    # Directory paths with environment variable fallbacks
    base_dir: Path = field(default_factory=lambda: Path(
        os.getenv('INVOKEGALLERY_BASE_DIR', os.path.expanduser('~/.invokegallery'))
    ))
    
    # Subdirectories - all relative to base_dir
    images_dir: Path = field(default_factory=lambda: Path(DEFAULT_PATHS['images']))
    thumbnails_dir: Path = field(default_factory=lambda: Path(DEFAULT_PATHS['thumbnails']))
    collections_dir: Path = field(default_factory=lambda: Path(DEFAULT_PATHS['collections']))
    favorites_dir: Path = field(default_factory=lambda: Path(DEFAULT_PATHS['favorites']))
    boards_dir: Path = field(default_factory=lambda: Path(DEFAULT_PATHS['boards']))
    cache_dir: Path = field(default_factory=lambda: Path(DEFAULT_PATHS['cache']))
    config_dir: Path = field(default_factory=lambda: Path(DEFAULT_PATHS['config']))
    
    # Cache settings
    cache_enabled: bool = True
    max_cache_size_mb: int = 1000
    cache_ttl_days: int = 30
    
    # UI settings
    theme: str = "default"
    thumbnail_size: int = THUMBNAIL_SIZE
    default_view: str = "grid"
    
    def __post_init__(self):
        """Ensure all paths are relative to base_dir"""
        # Make paths absolute relative to base_dir if they're not already absolute
        for path_attr in ['images_dir', 'thumbnails_dir', 'collections_dir',
                         'favorites_dir', 'boards_dir', 'cache_dir', 'config_dir']:
            path = getattr(self, path_attr)
            if not path.is_absolute():
                setattr(self, path_attr, self.base_dir / path)
    
    @classmethod
    def load_from_file(cls, config_path: Path) -> 'AppSettings':
        """Load settings from a JSON configuration file"""
        try:
            if config_path.exists():
                with open(config_path) as f:
                    data = json.load(f)
                    
                # Convert path strings to Path objects
                path_keys = [
                    'base_dir', 'images_dir', 'thumbnails_dir', 'collections_dir',
                    'favorites_dir', 'boards_dir', 'cache_dir', 'config_dir'
                ]
                
                # Ensure all path keys exist with default values if not in data
                for key in path_keys:
                    if key not in data:
                        data[key] = str(getattr(cls(), key))  # Get default from class
                    if isinstance(data[key], str):  # Only convert if it's a string
                        data[key] = Path(data[key])
                    
                return cls(**data)
            
        except Exception as e:
            logger.error(f"Error loading settings from {config_path}: {e}")
            
        # Return default settings if loading fails
        return cls()
        
    def save_to_file(self, config_path: Path) -> None:
        """Save settings to a JSON configuration file"""
        try:
            # Convert paths to strings for JSON serialization
            data = {
                'base_dir': str(self.base_dir),
                'images_dir': str(self.images_dir),
                'thumbnails_dir': str(self.thumbnails_dir),
                'collections_dir': str(self.collections_dir),
                'favorites_dir': str(self.favorites_dir),
                'boards_dir': str(self.boards_dir),
                'cache_dir': str(self.cache_dir),
                'config_dir': str(self.config_dir),
                'cache_enabled': self.cache_enabled,
                'max_cache_size_mb': self.max_cache_size_mb,
                'cache_ttl_days': self.cache_ttl_days,
                'theme': self.theme,
                'thumbnail_size': self.thumbnail_size,
                'default_view': self.default_view
            }
            
            # Create parent directories if they don't exist
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(data, f, indent=4)
                
        except Exception as e:
            print(f"Error saving settings: {e}")
            
    def ensure_directories(self) -> None:
        """Ensure all required directories exist"""
        # Create all required directories
        for path in [self.base_dir, self.images_dir, self.thumbnails_dir,
                    self.collections_dir, self.favorites_dir, self.boards_dir,
                    self.cache_dir, self.config_dir]:
            path.mkdir(parents=True, exist_ok=True)
            
    def validate_paths(self) -> Dict[str, bool]:
        """Validate existence of configured paths"""
        return {
            'base_dir': self.base_dir.exists(),
            'images_dir': self.images_dir.exists(),
            'thumbnails_dir': self.thumbnails_dir.exists(),
            'collections_dir': self.collections_dir.exists(),
            'favorites_dir': self.favorites_dir.exists(),
            'boards_dir': self.boards_dir.exists(),
            'cache_dir': self.cache_dir.exists(),
            'config_dir': self.config_dir.exists()
        }
        
    def get_images_dir(self) -> Path:
        """Get the configured images directory, ensuring it exists"""
        self.images_dir.mkdir(parents=True, exist_ok=True)
        return self.images_dir
        
    def get_favorites_dir(self) -> Path:
        """Get the configured favorites directory, ensuring it exists"""
        self.favorites_dir.mkdir(parents=True, exist_ok=True)
        return self.favorites_dir

class AppSettingsManager:
    """Application settings manager"""
    
    def __init__(self, app_dir: Path):
        """Initialize settings with app directory"""
        self.app_dir = app_dir
        self.user_config = UserConfigManager(app_dir)
        self.saved_folders = SavedFoldersManager(self.user_config)
        
    def get_last_directory(self) -> Optional[str]:
        """Get last accessed directory"""
        return self.user_config.settings.last_directory
        
    def get_show_subfolders(self) -> bool:
        """Get show subfolders setting"""
        return self.user_config.get_show_subfolders()
        
    def set_show_subfolders(self, enabled: bool):
        """Update show subfolders setting"""
        self.user_config.set_show_subfolders(enabled)
        
    def get_theme_path(self, theme_name: str) -> Optional[Path]:
        """Get theme file path"""
        return self.user_config.get_theme_path(theme_name)
        
    def get_cache_dir(self) -> Path:
        """Get cache directory path"""
        return self.user_config.get_cache_dir()
        
    def get_state_file(self) -> Path:
        """Get app state file path"""
        return self.user_config.get_state_file() 