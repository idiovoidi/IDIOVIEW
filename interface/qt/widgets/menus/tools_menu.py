"""Tools menu for the application"""

import logging
from typing import Callable

from PyQt6.QtCore import (
    Qt, QObject, QSize, QPoint, 
    QEvent, pyqtSignal, QTimer
)
from PyQt6.QtGui import (
    QAction, QIcon, QKeySequence,
    QColor, QFont, QPainter
)
from PyQt6.QtWidgets import (
    QApplication, QWidget, QMainWindow,
    QLabel, QPushButton, QMenu, QHBoxLayout, QVBoxLayout, QFileDialog
)

logger = logging.getLogger(__name__)

class ToolsMenu(QMenu):
    """Tools menu with additional tools"""
    
    def __init__(self, parent=None):
        super().__init__("&Tools", parent)
        self.setup_actions()
        
    def setup_actions(self):
        """Setup menu actions"""
        # Batch operations
        self.batch_menu = QMenu("Batch Operations", self)
        
        self.batch_rename_action = QAction("Batch &Rename...", self)
        self.batch_menu.addAction(self.batch_rename_action)
        
        self.batch_tag_action = QAction("Batch &Tag...", self)
        self.batch_menu.addAction(self.batch_tag_action)
        
        self.batch_rate_action = QAction("Batch &Rate...", self)
        self.batch_menu.addAction(self.batch_rate_action)
        
        self.addMenu(self.batch_menu)
        
        self.addSeparator()
        
        # Analysis tools
        self.analyze_menu = QMenu("Analyze", self)
        
        self.analyze_metadata_action = QAction("Analyze &Metadata...", self)
        self.analyze_menu.addAction(self.analyze_metadata_action)
        
        self.analyze_duplicates_action = QAction("Find &Duplicates...", self)
        self.analyze_menu.addAction(self.analyze_duplicates_action)
        
        self.analyze_similar_action = QAction("Find &Similar...", self)
        self.analyze_menu.addAction(self.analyze_similar_action)
        
        self.addMenu(self.analyze_menu)
        
        self.addSeparator()
        
        # Settings
        self.settings_action = QAction("&Settings...", self)
        self.addAction(self.settings_action)
        
    def set_batch_rename_callback(self, callback: Callable[[], None]):
        """Set callback for batch rename"""
        self.batch_rename_action.triggered.connect(callback)
        
    def set_batch_tag_callback(self, callback: Callable[[], None]):
        """Set callback for batch tag"""
        self.batch_tag_action.triggered.connect(callback)
        
    def set_batch_rate_callback(self, callback: Callable[[], None]):
        """Set callback for batch rate"""
        self.batch_rate_action.triggered.connect(callback)
        
    def set_analyze_metadata_callback(self, callback: Callable[[], None]):
        """Set callback for metadata analysis"""
        self.analyze_metadata_action.triggered.connect(callback)
        
    def set_analyze_duplicates_callback(self, callback: Callable[[], None]):
        """Set callback for duplicate analysis"""
        self.analyze_duplicates_action.triggered.connect(callback)
        
    def set_analyze_similar_callback(self, callback: Callable[[], None]):
        """Set callback for similarity analysis"""
        self.analyze_similar_action.triggered.connect(callback)
        
    def set_settings_callback(self, callback: Callable[[], None]):
        """Set callback for settings"""
        self.settings_action.triggered.connect(callback)
        
    def update_enabled_states(self, has_selection: bool):
        """Update enabled states based on selection"""
        self.batch_menu.setEnabled(has_selection)
        self.analyze_menu.setEnabled(has_selection) 