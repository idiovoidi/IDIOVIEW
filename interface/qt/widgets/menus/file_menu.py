"""File menu for the application"""

import logging
from typing import Callable, Optional, List
from ...shared.imports.core import Qt
from ...shared.imports.gui import QKeySequence
from ...shared.imports.widgets import QFileDialog
from .base_menu import BaseMenu

logger = logging.getLogger(__name__)

class FileMenu(BaseMenu):
    """File menu with file operations"""
    
    def __init__(self, parent=None):
        super().__init__("&File", parent)
        
    def setup_actions(self):
        """Setup menu actions"""
        # Open directory
        self.add_action_with_shortcut(
            name="open_dir",
            text="&Open Directory...",
            shortcut=QKeySequence.StandardKey.Open
        )
        
        # Recent directories submenu
        self.recent_menu = self.add_menu(
            name="recent",
            text="Recent Directories"
        )
        
        self.add_separator()
        
        # Export actions
        self.export_menu = self.add_menu(
            name="export",
            text="Export"
        )
        self.add_action_with_shortcut(
            name="export_metadata",
            text="Export Metadata...",
            parent=self.export_menu
        )
        
        self.add_separator()
        
        # Exit action
        self.add_action_with_shortcut(
            name="exit",
            text="E&xit",
            shortcut=QKeySequence.StandardKey.Quit
        )
        
    def set_open_callback(self, callback: Callable[[], None]):
        """Set callback for open directory action"""
        if action := self.get_action("open_dir"):
            action.triggered.connect(callback)
            
    def set_exit_callback(self, callback: Callable[[], None]):
        """Set callback for exit action"""
        if action := self.get_action("exit"):
            action.triggered.connect(callback)
            
    def update_recent_dirs(self, dirs: List[str]):
        """Update recent directories menu
        
        Args:
            dirs: List of recent directory paths
        """
        self.recent_menu.clear()
        for path in dirs:
            action = self.add_action_with_shortcut(
                name=f"recent_{path}",
                text=path,
                parent=self.recent_menu
            )
            action.setData(path)
            
    def get_export_directory(self) -> Optional[str]:
        """Show dialog to select export directory
        
        Returns:
            Selected directory path or None if cancelled
        """
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Export Directory",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        return str(directory) if directory else None 