"""Application configuration management"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from .settings import AppSettings
from ..cache.metadata_cache import MetadataCache
import logging

logger = logging.getLogger(__name__)

@dataclass
class AppConfig:
    """Application configuration settings"""
    
    # Core settings
    settings: AppSettings
    base_dir: Path
    
    # Directory paths derived from settings
    user_data_dir: Path
    cache_dir: Path
    config_dir: Path
    themes_dir: Path
    
    # Cache instances
    metadata_cache: MetadataCache = field(init=False)
    
    def __post_init__(self):
        """Initialize caches after dataclass initialization"""
        try:
            # Initialize metadata cache
            metadata_cache_path = self.cache_dir / "metadata"
            self.metadata_cache = MetadataCache(
                cache_dir=metadata_cache_path,
                max_size_mb=self.settings.max_cache_size_mb  # Changed parameter name
            )
        except Exception as e:
            logger.error(f"Error initializing caches: {e}")
            raise
    
    @classmethod
    def create_default(cls, base_dir: Optional[Path] = None) -> 'AppConfig':
        """Create default configuration"""
        if base_dir is None:
            base_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent.parent.parent
            
        # Setup directory paths
        user_data_dir = base_dir / "user_data"
        config_dir = user_data_dir / "config"
        
        # Load settings from file or create default
        settings_path = config_dir / "settings.json"
        settings = AppSettings.load_from_file(settings_path)
        
        # Create configuration
        config = cls(
            settings=settings,
            base_dir=base_dir,
            user_data_dir=user_data_dir,
            cache_dir=user_data_dir / "cache",
            config_dir=config_dir,
            themes_dir=user_data_dir / "themes"
        )
        
        # Ensure directories exist
        config.ensure_directories()
        
        # Save settings if they were created from defaults
        if not settings_path.exists():
            settings.save_to_file(settings_path)
            
        return config
        
    def ensure_directories(self) -> None:
        """Ensure all required directories exist"""
        try:
            # Create core directories
            for dir_path in [
                self.user_data_dir,
                self.cache_dir,
                self.config_dir,
                self.themes_dir,
                self.cache_dir / "metadata"  # Add metadata cache directory
            ]:
                dir_path.mkdir(parents=True, exist_ok=True)
                
            # Create settings-based directories
            self.settings.ensure_directories()
            
        except Exception as e:
            logger.error(f"Error ensuring directories: {e}")
            raise
            
    def get_images_dir(self) -> Path:
        """Get the configured images directory"""
        return self.settings.get_images_dir()
        
    def set_images_dir(self, path: Path) -> None:
        """Set a new images directory"""
        self.settings.images_dir = path
        # Save settings to persist the change
        self.settings.save_to_file(self.config_dir / "settings.json")
        
    def validate_paths(self) -> Dict[str, bool]:
        """Validate existence of all configured paths"""
        try:
            core_paths = {
                'user_data_dir': self.user_data_dir.exists(),
                'cache_dir': self.cache_dir.exists(),
                'config_dir': self.config_dir.exists(),
                'themes_dir': self.themes_dir.exists(),
                'metadata_cache_dir': (self.cache_dir / "metadata").exists()
            }
            return {**core_paths, **self.settings.validate_paths()}
        except Exception as e:
            logger.error(f"Error validating paths: {e}")
            return {}
            
    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            # Clean up metadata cache
            if hasattr(self, 'metadata_cache'):
                self.metadata_cache.cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}") 