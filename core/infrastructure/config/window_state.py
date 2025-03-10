from pathlib import Path
import configparser
import logging
from typing import Dict, Tuple, Optional
from PyQt6.QtCore import QByteArray, QPoint, QSize

logger = logging.getLogger(__name__)

class WindowStateManager:
    """Manages saving and restoring window states"""
    
    def __init__(self, state_file: Path):
        self.state_file = Path(state_file)
        # Ensure parent directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.config = configparser.ConfigParser()
        self._load_state()
        
    def _load_state(self):
        """Load window states from file"""
        try:
            if self.state_file.exists():
                self.config.read(self.state_file)
            else:
                logger.info(f"No existing window state file at {self.state_file}")
        except Exception as e:
            logger.error(f"Error loading window states: {e}")
            
    def save_state(self):
        """Save window states to file"""
        try:
            # Ensure parent directory exists
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.state_file, 'w') as f:
                self.config.write(f)
                
            logger.debug(f"Saved window states to {self.state_file}")
                
        except Exception as e:
            logger.error(f"Error saving window states: {e}")
            
    def save_window_geometry(self, window_name: str, geometry: QByteArray):
        """Save window geometry"""
        try:
            if not self.config.has_section(window_name):
                self.config.add_section(window_name)
            self.config[window_name]['geometry'] = geometry.toHex().data().decode()
            self.save_state()
        except Exception as e:
            logger.error(f"Error saving window geometry: {e}")
            
    def get_window_geometry(self, window_name: str) -> Optional[QByteArray]:
        """Get saved window geometry"""
        try:
            if self.config.has_section(window_name):
                geometry = self.config[window_name].get('geometry')
                if geometry:
                    return QByteArray.fromHex(geometry.encode())
            return None
        except Exception as e:
            logger.error(f"Error getting window geometry: {e}")
            return None
            
    def save_window_state(self, window_name: str, state: QByteArray):
        """Save window state (toolbar positions, etc)"""
        try:
            if not self.config.has_section(window_name):
                self.config.add_section(window_name)
            self.config[window_name]['state'] = state.toHex().data().decode()
            self.save_state()
        except Exception as e:
            logger.error(f"Error saving window state: {e}")
            
    def get_window_state(self, window_name: str) -> Optional[QByteArray]:
        """Get saved window state"""
        try:
            if self.config.has_section(window_name):
                state = self.config[window_name].get('state')
                if state:
                    return QByteArray.fromHex(state.encode())
            return None
        except Exception as e:
            logger.error(f"Error getting window state: {e}")
            return None
            
    def save_splitter_state(self, window_name: str, splitter_name: str, state: QByteArray):
        """Save splitter state"""
        try:
            section = f"{window_name}_splitter_{splitter_name}"
            if not self.config.has_section(section):
                self.config.add_section(section)
            self.config[section]['state'] = state.toHex().data().decode()
            self.save_state()
        except Exception as e:
            logger.error(f"Error saving splitter state: {e}")
            
    def get_splitter_state(self, window_name: str, splitter_name: str) -> Optional[QByteArray]:
        """Get saved splitter state"""
        try:
            section = f"{window_name}_splitter_{splitter_name}"
            if self.config.has_section(section):
                state = self.config[section].get('state')
                if state:
                    return QByteArray.fromHex(state.encode())
            return None
        except Exception as e:
            logger.error(f"Error getting splitter state: {e}")
            return None 