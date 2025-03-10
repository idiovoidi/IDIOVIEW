"""Context menu for image items"""

import logging
from typing import Callable, Optional

from PyQt6.QtCore import (
    Qt, QObject, QSize, QPoint, 
    QEvent, pyqtSignal, QTimer
)
from PyQt6.QtGui import (
    QAction, QIcon, QKeySequence,
    QColor, QFont, QPainter, QActionGroup
)
from PyQt6.QtWidgets import (
    QApplication, QWidget, QMainWindow,
    QLabel, QPushButton, QMenu, QHBoxLayout, QVBoxLayout, QFileDialog
)

logger = logging.getLogger(__name__)

class ContextMenu(QMenu):
    """Context menu for image items"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_actions()
        
    def setup_actions(self):
        """Setup menu actions"""
        # Rating actions
        self.rating_menu = QMenu("Rating", self)
        self.rating_group = QActionGroup(self)
        
        for i in range(6):  # 0-5 stars
            action = QAction(f"{i} {'★' * i}", self)
            action.setData(i)
            action.setCheckable(True)
            self.rating_group.addAction(action)
            self.rating_menu.addAction(action)
            
        self.addMenu(self.rating_menu)
        
        # Review status actions
        self.status_menu = QMenu("Review Status", self)
        self.status_group = QActionGroup(self)
        
        for status in ["Pending", "Approved", "Rejected", "Needs Work"]:
            action = QAction(status, self)
            action.setData(status.lower().replace(" ", "_"))
            action.setCheckable(True)
            self.status_group.addAction(action)
            self.status_menu.addAction(action)
            
        self.addMenu(self.status_menu)
        
        self.addSeparator()
        
        # Copy actions
        self.copy_action = QAction("Copy", self)
        self.addAction(self.copy_action)
        
        self.copy_path_action = QAction("Copy Path", self)
        self.addAction(self.copy_path_action)
        
        self.addSeparator()
        
        # Open actions
        self.open_menu = QMenu("Open With", self)
        self.addMenu(self.open_menu)
        
        self.addSeparator()
        
        # Delete action
        self.delete_action = QAction("Delete", self)
        self.addAction(self.delete_action)
        
    def set_rating_callback(self, callback: Callable[[int], None]):
        """Set callback for rating changes"""
        for action in self.rating_group.actions():
            action.triggered.connect(
                lambda checked, r=action.data(): callback(r)
            )
            
    def set_status_callback(self, callback: Callable[[str], None]):
        """Set callback for status changes"""
        for action in self.status_group.actions():
            action.triggered.connect(
                lambda checked, s=action.data(): callback(s)
            )
            
    def set_copy_callback(self, callback: Callable[[], None]):
        """Set callback for copy action"""
        self.copy_action.triggered.connect(callback)
        
    def set_copy_path_callback(self, callback: Callable[[], None]):
        """Set callback for copy path action"""
        self.copy_path_action.triggered.connect(callback)
        
    def set_delete_callback(self, callback: Callable[[], None]):
        """Set callback for delete action"""
        self.delete_action.triggered.connect(callback)
        
    def update_rating(self, rating: int):
        """Update current rating"""
        for action in self.rating_group.actions():
            if action.data() == rating:
                action.setChecked(True)
                break
                
    def update_status(self, status: str):
        """Update current status"""
        for action in self.status_group.actions():
            if action.data() == status:
                action.setChecked(True)
                break
                
    def update_open_with_menu(self, apps: list[tuple[str, str, Callable]]):
        """Update open with menu"""
        self.open_menu.clear()
        for name, icon, callback in apps:
            action = QAction(name, self)
            if icon:
                action.setIcon(QIcon.fromTheme(icon))
            action.triggered.connect(callback)
            self.open_menu.addAction(action) 