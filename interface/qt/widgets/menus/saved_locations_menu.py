"""Menu and list widgets for managing saved/favorite locations"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, List, Callable

from PyQt6.QtWidgets import (
    QMenu, QInputDialog, QMessageBox,
    QFileDialog, QWidget, QVBoxLayout, QListWidget, 
    QListWidgetItem, QLabel
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import pyqtSignal, Qt

from core.infrastructure.config.savedfolders import SavedFoldersManager

logger = logging.getLogger(__name__)

class SavedLocationsList(QWidget):
    """Widget for displaying saved locations in a list view"""
    
    # Signals
    location_selected = pyqtSignal(str)  # Emits path when location is selected
    
    def __init__(self, saved_folders: SavedFoldersManager, parent=None):
        super().__init__(parent)
        self.saved_folders = saved_folders
        self.setup_ui()
        self.refresh_locations()
        
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Add header label
        header = QLabel("Saved Locations ⭐")
        header.setStyleSheet("""
            QLabel {
                padding: 5px;
                background-color: #2d2d2d;
                color: #cccccc;
                font-weight: bold;
            }
        """)
        layout.addWidget(header)
        
        # Create list widget
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                border: none;
            }
            QListWidget::item {
                color: #cccccc;
                padding: 5px;
            }
            QListWidget::item:hover {
                background-color: #3d3d3d;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
        """)
        layout.addWidget(self.list_widget)
        
    def refresh_locations(self):
        """Refresh the list from saved folders manager"""
        try:
            self.list_widget.clear()
            saved_folders = self.saved_folders.get_saved_folders()
            
            if saved_folders:
                for name, path in saved_folders.items():
                    item = QListWidgetItem(name)
                    item.setToolTip(path)
                    item.setData(Qt.ItemDataRole.UserRole, path)  # Store path in item data
                    self.list_widget.addItem(item)
            else:
                # Add placeholder if no locations saved
                item = QListWidgetItem("No saved locations")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                self.list_widget.addItem(item)
                
        except Exception as e:
            logger.error(f"Error refreshing saved locations: {e}")
            
    def _on_item_clicked(self, item: QListWidgetItem):
        """Handle item click events"""
        try:
            if not item.flags() & Qt.ItemFlag.ItemIsEnabled:
                return  # Skip disabled items
                
            path = item.data(Qt.ItemDataRole.UserRole)
            if path:
                self.location_selected.emit(path)
        except Exception as e:
            logger.error(f"Error handling item click: {e}")

class SavedLocationsMenu(QMenu):
    """Menu for managing saved locations"""
    
    # Signals
    location_selected = pyqtSignal(str)  # Emitted when a location is selected
    location_added = pyqtSignal()  # Emitted when a location is added
    location_removed = pyqtSignal()  # Emitted when a location is removed
    default_location_changed = pyqtSignal(str)  # Emitted when default location changes, None = cleared
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__("Saved Locations", parent)
        
        # Get saved folders manager from parent window
        self.saved_folders = parent.saved_folders if parent else None
        
        # Create menu sections
        self.locations_section = QMenu("Locations", self)
        self.default_section = QMenu("Set Default Location", self)
        
        # Add menu sections
        self.addMenu(self.locations_section)
        self.addSeparator()
        self.addMenu(self.default_section)
        self.addSeparator()
        
        # Add actions
        self.add_location_action = self.addAction("Add Current Location...")
        self.add_location_action.triggered.connect(self._add_current_location)
        
        # Update menu
        self.update_locations_section()
        
    def update_locations_section(self):
        """Update the locations section of the menu"""
        try:
            # Clear existing items
            self.locations_section.clear()
            self.default_section.clear()
            
            if not self.saved_folders:
                return
                
            # Add saved locations
            default_path = self.saved_folders.get_default_folder()
            
            for name, path in self.saved_folders.saved_folders.items():
                # Add to locations menu
                location_action = self.locations_section.addAction(name)
                location_action.setData(path)
                location_action.triggered.connect(
                    lambda checked, p=path: self.location_selected.emit(p)
                )
                
                # Add remove option
                remove_action = self.locations_section.addAction(f"Remove {name}")
                remove_action.setData(path)
                remove_action.triggered.connect(
                    lambda checked, p=path: self._remove_location(p)
                )
                
                # Add separator between locations
                self.locations_section.addSeparator()
                
                # Add to default location menu
                default_action = self.default_section.addAction(
                    f"{name} {'(Current Default)' if path == default_path else ''}"
                )
                default_action.setData(path)
                default_action.triggered.connect(
                    lambda checked, p=path: self._set_default_location(p)
                )
                
            # Add clear default option
            if default_path:
                self.default_section.addSeparator()
                clear_action = self.default_section.addAction("Clear Default")
                clear_action.triggered.connect(self._clear_default_location)
                
        except Exception as e:
            logger.error(f"Error updating locations menu: {e}")
            
    def _set_default_location(self, path: str):
        """Set the default location"""
        try:
            self.default_location_changed.emit(path)
            self.update_locations_section()
        except Exception as e:
            logger.error(f"Error setting default location: {e}")
            
    def _clear_default_location(self):
        """Clear the default location"""
        try:
            self.default_location_changed.emit(None)
            self.update_locations_section()
        except Exception as e:
            logger.error(f"Error clearing default location: {e}")
            
    def _add_current_location(self):
        """Add current location to saved locations"""
        try:
            # Get current path from parent window
            if hasattr(self.parent(), 'grid_view'):
                current_path = self.parent().grid_view.current_directory
            else:
                current_path = ""
            
            if not current_path:
                QMessageBox.warning(
                    self,
                    "No Location Selected",
                    "Please select a folder first."
                )
                return
                
            # Get name for location
            name, ok = QInputDialog.getText(
                self,
                "Save Location",
                "Enter a name for this location:"
            )
            
            if ok and name and self.saved_folders:
                self.saved_folders.add_saved_folder(name, current_path)
                self.update_locations_section()
                self.location_added.emit()
                
        except Exception as e:
            logger.error(f"Error adding location: {e}")
            
    def browse_location(self):
        """Browse for a location to add"""
        try:
            path = QFileDialog.getExistingDirectory(
                self,
                "Select Folder",
                str(Path.home()),
                QFileDialog.Option.ShowDirsOnly
            )
            
            if path and self.saved_folders:
                name, ok = QInputDialog.getText(
                    self,
                    "Save Location",
                    "Enter a name for this location:"
                )
                
                if ok and name:
                    self.saved_folders.add_saved_folder(name, path)
                    self.update_locations_section()
                    self.location_added.emit()
                    
        except Exception as e:
            logger.error(f"Error browsing for location: {e}")
            
    def manage_locations(self):
        """Open dialog to manage saved locations"""
        try:
            if not self.saved_folders:
                return
                
            saved_locations = self.saved_folders.get_saved_folders()
            if not saved_locations:
                QMessageBox.information(
                    self,
                    "Manage Locations",
                    "No saved locations to manage."
                )
                return
                
            # Create submenu of locations to remove
            menu = QMenu("Remove Location", self)
            
            for name, path in saved_locations.items():
                action = QAction(f"{name} ({path})", menu)
                action.triggered.connect(lambda checked, n=name: self.remove_location(n))
                menu.addAction(action)
                
            # Show submenu at appropriate position
            menu.exec(self.mapToGlobal(self.rect().bottomRight()))
            
        except Exception as e:
            logger.error(f"Error managing locations: {e}")
            
    def remove_location(self, name: str):
        """Remove a saved location"""
        try:
            if self.saved_folders and name in self.saved_folders.get_saved_folders():
                confirm = QMessageBox.question(
                    self,
                    "Remove Location",
                    f"Are you sure you want to remove '{name}'?"
                )
                
                if confirm == QMessageBox.StandardButton.Yes:
                    self.saved_folders.remove_saved_folder(name)
                    self.update_locations_section()
                    self.location_removed.emit()
                    
        except Exception as e:
            logger.error(f"Error removing location: {e}")
            
    def showEvent(self, event):
        """Update locations when menu is shown"""
        self.update_locations_section()
        super().showEvent(event) 