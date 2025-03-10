"""Folder tree widget for browsing directories"""

from typing import Optional
from PyQt6.QtWidgets import QTreeView
from PyQt6.QtCore import Qt, pyqtSignal, QDir
from PyQt6.QtGui import QFileSystemModel
from dependency_injector.wiring import inject, Provide
import logging
import os

from core.infrastructure.config.savedfolders import SavedFoldersManager
from core.container.container import Container

logger = logging.getLogger(__name__)

class FolderTree(QTreeView):
    """Tree view for browsing folders"""
    
    directory_selected = pyqtSignal(str)  # Emitted when directory is selected
    
    @inject
    def __init__(
        self,
        saved_folders: SavedFoldersManager = Provide[Container.saved_folders],
        parent: Optional[QTreeView] = None
    ):
        super().__init__(parent)
        
        self.saved_folders = saved_folders
        
        # Create file system model
        self.model = QFileSystemModel()
        self.model.setRootPath("")  # Show all drives
        
        # Set filters to show only directories
        self.model.setFilter(QDir.Filter.Dirs | QDir.Filter.NoDotAndDotDot)
        
        # Set model
        self.setModel(self.model)
        
        # Hide all columns except name
        for i in range(1, self.model.columnCount()):
            self.hideColumn(i)
            
        # Connect signals
        self.clicked.connect(self._on_clicked)
        
        # Style
        self.setStyleSheet("""
            QTreeView {
                background-color: #1e1e1e;
                border: none;
            }
            QTreeView::item {
                color: #ffffff;
                padding: 4px;
            }
            QTreeView::item:hover {
                background-color: #2d2d2d;
            }
            QTreeView::item:selected {
                background-color: #0078d4;
            }
        """)
        
        # Show default location
        self._show_default_location()
        
    def _show_default_location(self):
        """Show and expand to the default location"""
        try:
            default_path = self.saved_folders.get_default_folder()
            if not default_path or not os.path.exists(default_path):
                logger.warning(f"Default path does not exist: {default_path}")
                return
                
            logger.debug(f"Showing default location: {default_path}")
            
            # Get the index for the default path
            index = self.model.index(default_path)
            if not index.isValid():
                logger.error(f"Could not get valid index for default path: {default_path}")
                return
                
            # Expand path to the default location
            parent = index
            path_parts = []
            while parent.isValid():
                path_parts.insert(0, parent)
                parent = parent.parent()
                
            # Expand each part of the path
            for part in path_parts:
                self.expand(part)
                
            # Select and scroll to the default location
            self.setCurrentIndex(index)
            self.scrollTo(index)
            
            # Emit the directory selected signal
            self.directory_selected.emit(default_path)
            
        except Exception as e:
            logger.error(f"Error showing default location: {e}")
        
    def _on_clicked(self, index):
        """Handle item click - emit the selected directory path"""
        path = self.model.filePath(index)
        if os.path.isdir(path):  # Only emit if it's a valid directory
            logger.debug(f"Directory selected: {path}")
            self.directory_selected.emit(path)
            self.saved_folders.add_recent_folder(path) 