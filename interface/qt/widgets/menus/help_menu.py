"""Help menu for the application"""

import logging
from typing import Callable, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QMainWindow, QMenu, QMessageBox, QDialog,
    QVBoxLayout, QWidget
)

from ..panels.shortcuts_panel import ShortcutsPanel
from core.infrastructure.config.shortcuts import GalleryShortcuts

logger = logging.getLogger(__name__)

class ShortcutsDialog(QDialog):
    """Dialog to display the shortcuts panel"""
    
    def __init__(self, shortcut_manager: GalleryShortcuts, parent: Optional[QMainWindow] = None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setMinimumSize(600, 400)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Add shortcuts panel
        self.shortcuts_panel = ShortcutsPanel(shortcut_manager, self)
        layout.addWidget(self.shortcuts_panel)

class HelpMenu(QMenu):
    """Help menu with help and about options"""
    
    def __init__(self, shortcut_manager: Optional[GalleryShortcuts] = None, parent=None):
        super().__init__("&Help", parent)
        self.shortcut_manager = shortcut_manager
        self.setup_actions()
        
    def setup_actions(self):
        """Setup menu actions"""
        # Documentation
        self.docs_action = QAction("&Documentation", self)
        self.addAction(self.docs_action)
        
        # Shortcuts action (only if shortcut manager is provided)
        if self.shortcut_manager:
            self.shortcuts_action = QAction("&Keyboard Shortcuts...", self)
            self.shortcuts_action.triggered.connect(self.show_shortcuts_dialog)
            self.addAction(self.shortcuts_action)
        
        self.addSeparator()
        
        # Check for updates
        self.update_action = QAction("Check for &Updates", self)
        self.addAction(self.update_action)
        
        self.addSeparator()
        
        # About
        self.about_action = QAction("&About", self)
        self.about_action.triggered.connect(self.show_about_dialog)
        self.addAction(self.about_action)
        
    def show_shortcuts_dialog(self):
        """Show the shortcuts dialog"""
        if self.shortcut_manager:
            dialog = ShortcutsDialog(self.shortcut_manager, self.parent())
            dialog.exec()
        
    def set_docs_callback(self, callback: Callable[[], None]):
        """Set callback for documentation"""
        self.docs_action.triggered.connect(callback)
        
    def set_update_callback(self, callback: Callable[[], None]):
        """Set callback for update check"""
        self.update_action.triggered.connect(callback)
        
    def show_about_dialog(self):
        """Show about dialog"""
        QMessageBox.about(
            self.parent(),
            "About ID:I/O Gallery Viewer",
            """
            <h3>ID:I/O Gallery Viewer</h3>
            <p>Organizational Media Library</p>
            <p>https://github.com/idiovoidi/IDIOVIEW</p>
            <p>Version: 0.0.5</p>
            <p>Dogeright © 2025</p>
            """
        ) 