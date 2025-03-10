"""Edit menu for the application"""

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

class EditMenu(QMenu):
    """Edit menu with editing operations"""
    
    def __init__(self, parent=None):
        super().__init__("&Edit", parent)
        self.setup_actions()
        
    def setup_actions(self):
        """Setup menu actions"""
        # Selection actions
        self.select_all_action = QAction("Select &All", self)
        self.select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        self.addAction(self.select_all_action)
        
        self.deselect_all_action = QAction("&Deselect All", self)
        self.deselect_all_action.setShortcut("Ctrl+D")
        self.addAction(self.deselect_all_action)
        
        self.invert_selection_action = QAction("&Invert Selection", self)
        self.invert_selection_action.setShortcut("Ctrl+I")
        self.addAction(self.invert_selection_action)
        
        self.addSeparator()
        
        # Copy actions
        self.copy_action = QAction("&Copy", self)
        self.copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        self.addAction(self.copy_action)
        
        self.copy_path_action = QAction("Copy &Path", self)
        self.copy_path_action.setShortcut("Ctrl+Shift+C")
        self.addAction(self.copy_path_action)
        
        self.addSeparator()
        
        # Delete action
        self.delete_action = QAction("&Delete", self)
        self.delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        self.addAction(self.delete_action)
        
    def set_select_all_callback(self, callback: Callable[[], None]):
        """Set callback for select all action"""
        self.select_all_action.triggered.connect(callback)
        
    def set_deselect_all_callback(self, callback: Callable[[], None]):
        """Set callback for deselect all action"""
        self.deselect_all_action.triggered.connect(callback)
        
    def set_invert_selection_callback(self, callback: Callable[[], None]):
        """Set callback for invert selection action"""
        self.invert_selection_action.triggered.connect(callback)
        
    def set_copy_callback(self, callback: Callable[[], None]):
        """Set callback for copy action"""
        self.copy_action.triggered.connect(callback)
        
    def set_copy_path_callback(self, callback: Callable[[], None]):
        """Set callback for copy path action"""
        self.copy_path_action.triggered.connect(callback)
        
    def set_delete_callback(self, callback: Callable[[], None]):
        """Set callback for delete action"""
        self.delete_action.triggered.connect(callback)
        
    def update_enabled_states(self, has_selection: bool):
        """Update enabled states based on selection"""
        self.copy_action.setEnabled(has_selection)
        self.copy_path_action.setEnabled(has_selection)
        self.delete_action.setEnabled(has_selection) 