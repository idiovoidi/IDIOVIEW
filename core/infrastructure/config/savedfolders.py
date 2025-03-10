import json
import os
from pathlib import Path
import logging
from typing import Dict, List, Optional
from .user_config import UserConfigManager

logger = logging.getLogger(__name__)

class DefaultFolderManager:
    """Manages default folder functionality"""
    
    def __init__(self, parent_manager):
        self.parent = parent_manager
        self.default_folder: Optional[str] = None
        logger.debug("DefaultFolderManager initialized")
        
        # Set up default upload folder if no default exists
        self._ensure_default_upload_folder()
        
    def _ensure_default_upload_folder(self):
        """Ensure the default upload folder is set up"""
        try:
            default_path = r"C:\Users\Mitchell\Desktop\Temp Upload Folder"
            if not self.default_folder and not self.parent.user_config.settings.default_directory:
                logger.debug("No default folder set, setting up default upload folder")
                if os.path.exists(default_path):
                    self.setup_folder("Default Upload Folder", default_path)
                    logger.debug(f"Default upload folder set to: {default_path}")
                else:
                    logger.warning(f"Default upload folder path does not exist: {default_path}")
        except Exception as e:
            logger.error(f"Error ensuring default upload folder: {e}")
            
    def load_from_data(self, data: dict):
        """Load default folder from data dictionary"""
        self.default_folder = data.get("default_folder")
        logger.debug(f"Loaded default folder from data: {self.default_folder}")
        # Ensure default folder exists after loading
        self._ensure_default_upload_folder()
        
    def save_to_data(self, data: dict):
        """Save default folder to data dictionary"""
        data["default_folder"] = self.default_folder
        logger.debug(f"Saved default folder to data: {self.default_folder}")
        
    def set_folder(self, path: Optional[str]):
        """Set or clear the default folder"""
        try:
            logger.debug(f"Setting default folder to: {path}")
            # Validate path exists in saved folders if setting
            if path is not None and not any(p == path for p in self.parent.saved_folders.values()):
                logger.error(f"Cannot set default folder - path not in saved folders: {path}")
                return
                
            self.default_folder = path
            # Also update the user config default directory
            self.parent.user_config.settings.default_directory = path if path else ""
            self.parent.user_config.save_settings()
            self.parent.save_settings()
            logger.debug(f"Default folder set to: {self.default_folder}")
                
        except Exception as e:
            logger.error(f"Error setting default folder: {e}")
            
    def get_folder(self) -> Optional[str]:
        """Get the default folder path"""
        try:
            logger.debug("Getting default folder")
            # First check our saved default
            if self.default_folder and any(p == self.default_folder for p in self.parent.saved_folders.values()):
                logger.debug(f"Returning saved default folder: {self.default_folder}")
                return self.default_folder
                
            # Then check user config default directory
            default_dir = self.parent.user_config.settings.default_directory
            if default_dir and any(p == default_dir for p in self.parent.saved_folders.values()):
                logger.debug(f"Returning user config default directory: {default_dir}")
                return default_dir
                
            # Fall back to last directory from user config
            last_dir = self.parent.user_config.settings.last_directory
            logger.debug(f"Falling back to last directory: {last_dir}")
            return last_dir
            
        except Exception as e:
            logger.error(f"Error getting default folder: {e}")
            return None
            
    def setup_folder(self, name: str, path: str):
        """Add a folder and set it as default in one operation"""
        try:
            logger.debug(f"Setting up default folder - name: {name}, path: {path}")
            # First add the folder if it's not already saved
            if not any(p == path for p in self.parent.saved_folders.values()):
                logger.debug("Adding folder to saved folders")
                self.parent.add_saved_folder(name, path)
                
            # Then set it as default
            logger.debug("Setting as default folder")
            self.set_folder(path)
                
        except Exception as e:
            logger.error(f"Error setting up default folder: {e}")

class SavedFoldersManager:
    """Manages saved and recent folders"""
    
    def __init__(self, user_config: UserConfigManager):
        self.user_config = user_config
        self.settings_file = user_config.config_dir / "saved_folders.json"
        self.saved_folders: Dict[str, str] = {}  # name -> path mapping
        self.default = DefaultFolderManager(self)
        logger.debug(f"SavedFoldersManager initialized with settings file: {self.settings_file}")
        self.load_settings()
        
    def load_settings(self):
        """Load saved folders from settings file"""
        try:
            logger.debug(f"Loading settings from {self.settings_file}")
            if self.settings_file.exists():
                logger.debug("Settings file exists")
                with open(self.settings_file) as f:
                    data = json.load(f)
                    self.saved_folders = data.get("saved_folders", {})
                    logger.debug(f"Loaded saved folders: {self.saved_folders}")
                    self.default.load_from_data(data)
            else:
                logger.debug("Settings file does not exist, initializing with empty data")
                self.saved_folders = {}
                self.default.default_folder = None
                # This will trigger the default folder setup
                self.default.load_from_data({})
                self.save_settings()
                
        except Exception as e:
            logger.error(f"Error loading saved folders: {e}")
            self.saved_folders = {}
            self.default.default_folder = None
            # Attempt to set up default folder even in error case
            self.default.load_from_data({})
            
    def save_settings(self):
        """Save current settings to file"""
        try:
            logger.debug(f"Saving settings to {self.settings_file}")
            data = {"saved_folders": self.saved_folders}
            self.default.save_to_data(data)
            
            with open(self.settings_file, 'w') as f:
                json.dump(data, f, indent=4)
            logger.debug(f"Settings saved successfully: {data}")
                
        except Exception as e:
            logger.error(f"Error saving folders: {e}")
            
    def add_saved_folder(self, name: str, path: str):
        """Add a folder to saved folders"""
        try:
            logger.debug(f"Adding saved folder - name: {name}, path: {path}")
            self.saved_folders[name] = path
            self.save_settings()
            logger.debug("Folder added successfully")
                
        except Exception as e:
            logger.error(f"Error adding saved folder: {e}")
            
    def remove_saved_folder(self, name: str):
        """Remove a folder from saved folders"""
        try:
            logger.debug(f"Removing saved folder: {name}")
            if name in self.saved_folders:
                # If this was the default folder, clear it
                if self.saved_folders[name] == self.default.default_folder:
                    logger.debug("Clearing default folder as it's being removed")
                    self.default.set_folder(None)
                del self.saved_folders[name]
                self.save_settings()
                logger.debug("Folder removed successfully")
                
        except Exception as e:
            logger.error(f"Error removing saved folder: {e}")
            
    def add_recent_folder(self, folder: str):
        """Add a folder to recent folders"""
        logger.debug(f"Adding to recent folders: {folder}")
        self.user_config.add_recent_directory(folder)
            
    def get_saved_folders(self) -> Dict[str, str]:
        """Get dictionary of saved folders (name -> path)"""
        logger.debug(f"Getting saved folders: {self.saved_folders}")
        return self.saved_folders.copy()
        
    def get_recent_folders(self) -> List[str]:
        """Get list of recent folders"""
        recent = self.user_config.settings.recent_directories.copy()
        logger.debug(f"Getting recent folders: {recent}")
        return recent
        
    def get_last_directory(self) -> Optional[str]:
        """Get last accessed directory"""
        last_dir = self.user_config.settings.last_directory
        logger.debug(f"Getting last directory: {last_dir}")
        return last_dir
        
    # For backward compatibility and easier migration
    def set_default_folder(self, path: Optional[str]):
        """Set or clear the default folder (compatibility method)"""
        logger.debug(f"Setting default folder (compatibility): {path}")
        self.default.set_folder(path)
            
    def get_default_folder(self) -> Optional[str]:
        """Get the default folder path (compatibility method)"""
        folder = self.default.get_folder()
        logger.debug(f"Getting default folder (compatibility): {folder}")
        return folder
        
    def setup_default_folder(self, name: str, path: str):
        """Add a folder and set it as default (compatibility method)"""
        logger.debug(f"Setting up default folder (compatibility) - name: {name}, path: {path}")
        self.default.setup_folder(name, path)
