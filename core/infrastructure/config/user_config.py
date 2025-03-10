from pathlib import Path
import json
import logging
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, asdict
import os

logger = logging.getLogger(__name__)

@dataclass
class UserSettings:
    """User configuration settings"""
    last_directory: str = ""
    default_directory: str = ""  # Default directory to load on startup
    recent_directories: List[str] = None
    default_view: str = "grid"  # grid or masonry
    thumbnail_size: int = 200
    show_ratings: bool = True
    show_tags: bool = True
    theme: str = "default"
    auto_generate_thumbnails: bool = True
    cache_thumbnails: bool = True
    max_recent_dirs: int = 10
    show_subfolders: bool = False  # Default to not showing subfolders
    
    def __post_init__(self):
        if self.recent_directories is None:
            self.recent_directories = []

class UserConfigManager:
    """Manages user configuration and settings"""
    
    def __init__(self, app_dir: Path):
        self.app_dir = app_dir
        self.user_data_dir = app_dir / "user_data"
        self.config_dir = self.user_data_dir / "config"
        self.themes_dir = self.user_data_dir / "themes"
        self.cache_dir = self.user_data_dir / "cache"
        
        # Create directories
        self._ensure_directories()
        
        # Load settings
        self.settings = self._load_settings()
        
    def _ensure_directories(self):
        """Create necessary directories"""
        try:
            for directory in [
                self.user_data_dir,
                self.config_dir,
                self.themes_dir,
                self.cache_dir
            ]:
                directory.mkdir(parents=True, exist_ok=True)
            
            # Create .gitignore if it doesn't exist
            gitignore_path = self.user_data_dir / ".gitignore"
            if not gitignore_path.exists():
                gitignore_path.write_text("*\n!.gitignore\n")
                
        except Exception as e:
            logger.error(f"Error creating directories: {e}")
            raise
            
    def _load_settings(self) -> UserSettings:
        """Load user settings from file"""
        settings_path = self.config_dir / "user_settings.json"
        
        try:
            if settings_path.exists():
                with open(settings_path) as f:
                    data = json.load(f)
                return UserSettings(**data)
            return UserSettings()
            
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            return UserSettings()
            
    def save_settings(self):
        """Save current settings to file"""
        settings_path = self.config_dir / "user_settings.json"
        
        try:
            with open(settings_path, 'w') as f:
                json.dump(asdict(self.settings), f, indent=4)
                
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            
    def add_recent_directory(self, directory: str):
        """Add directory to recent list"""
        try:
            if directory not in self.settings.recent_directories:
                self.settings.recent_directories.insert(0, directory)
                self.settings.recent_directories = \
                    self.settings.recent_directories[:self.settings.max_recent_dirs]
                self.settings.last_directory = directory
                self.save_settings()
        except Exception as e:
            logger.error(f"Error adding recent directory: {e}")
            
    def get_theme_path(self, theme_name: str) -> Optional[Path]:
        """Get path to theme file"""
        if theme_name == "default":
            return None
            
        theme_file = self.themes_dir / f"{theme_name}.qss"
        return theme_file if theme_file.exists() else None
        
    def get_cache_dir(self) -> Path:
        """Get cache directory path"""
        return self.cache_dir
        
    def get_state_file(self) -> Path:
        """Get path to app state file"""
        return self.config_dir / "app_state.ini"
        
    def set_show_subfolders(self, enabled: bool):
        """Update show subfolders setting"""
        try:
            self.settings.show_subfolders = enabled
            self.save_settings()
        except Exception as e:
            logger.error(f"Error updating show subfolders setting: {e}")
            
    def get_show_subfolders(self) -> bool:
        """Get show subfolders setting"""
        return self.settings.show_subfolders 