"""Main toolbar widget"""

import logging
from typing import Optional, Tuple
"""Central Qt imports for PyQt6"""
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
    QLabel, QPushButton, QMenu, QToolBar, QComboBox, QSpinBox
)

logger = logging.getLogger(__name__)

class Toolbar(QToolBar):
    """Main application toolbar"""
    
    # Signals
    thumbnail_size_changed = pyqtSignal(int)
    sort_changed = pyqtSignal(str, bool)  # field, ascending
    rating_filter_changed = pyqtSignal(object)  # Optional[int]
    review_filter_changed = pyqtSignal(str)
    show_subfolders_changed = pyqtSignal(bool)  # True when subfolders should be included
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        self.setIconSize(QSize(24, 24))
        self.setup_ui()
        self._setup_signals()
        
    def setup_ui(self):
        """Setup toolbar UI elements"""
        # Thumbnail size control
        self.thumbnail_size = QSpinBox()
        self.thumbnail_size.setRange(100, 500)
        self.thumbnail_size.setValue(200)
        self.thumbnail_size.setSingleStep(50)
        self.thumbnail_size.setPrefix("Size: ")
        self.thumbnail_size.setFixedWidth(100)
        self.addWidget(self.thumbnail_size)
        
        self.addSeparator()
        
        # Sort options
        self.sort_by = QComboBox()
        self.sort_by.addItems(["Name", "Date", "Rating"])
        self.sort_by.setFixedWidth(100)
        self.addWidget(self.sort_by)
        
        self.addSeparator()
        
        # Filter options
        self.rating_filter = QComboBox()
        self.rating_filter.addItems(["All Ratings", "★★★★★", "★★★★", "★★★", "★★", "★"])
        self.rating_filter.setFixedWidth(100)
        self.addWidget(self.rating_filter)
        
        # Review status filter
        self.review_filter = QComboBox()
        self.review_filter.addItems([
            "All Images",
            "Pending Review",
            "Approved",
            "Rejected",
            "Needs Work",
            "Hide Rejected"
        ])
        self.review_filter.setFixedWidth(120)
        self.addWidget(self.review_filter)
        
        self.addSeparator()
        
        # Show subfolders toggle
        self.show_subfolders_button = QAction("Include Subfolders 📁", self)
        self.show_subfolders_button.setCheckable(True)
        self.show_subfolders_button.setChecked(False)
        self.show_subfolders_button.setToolTip("Show images from subfolders")
        self.addAction(self.show_subfolders_button)
        
    def _setup_signals(self):
        """Setup signal connections"""
        self.thumbnail_size.valueChanged.connect(self.thumbnail_size_changed.emit)
        self.sort_by.currentTextChanged.connect(self._handle_sort_changed)
        self.rating_filter.currentTextChanged.connect(self._handle_rating_changed)
        self.review_filter.currentTextChanged.connect(self._handle_review_changed)
        self.show_subfolders_button.triggered.connect(self.show_subfolders_changed.emit)
        
    def _handle_sort_changed(self, text: str):
        """Handle sort option changes"""
        self.sort_changed.emit(text.lower(), True)  # Always ascending for now
        
    def _handle_rating_changed(self, text: str):
        """Handle rating filter changes"""
        if text == "All Ratings":
            self.rating_filter_changed.emit(None)
        else:
            self.rating_filter_changed.emit(len(text))  # Count stars
            
    def _handle_review_changed(self, text: str):
        """Handle review status filter changes"""
        if text == "All Images":
            self.review_filter_changed.emit("")
        else:
            self.review_filter_changed.emit(text.lower().replace(" ", "_"))
            
    def get_thumbnail_size(self) -> int:
        """Get current thumbnail size"""
        return self.thumbnail_size.value()
        
    def get_sort_options(self) -> Tuple[str, bool]:
        """Get current sort options"""
        return (
            self.sort_by.currentText().lower(),
            True  # Always ascending for now
        )
        
    def get_rating_filter(self) -> Optional[int]:
        """Get current rating filter"""
        text = self.rating_filter.currentText()
        if text == "All Ratings":
            return None
        return len(text)  # Count stars
        
    def get_review_filter(self) -> Optional[str]:
        """Get current review filter"""
        text = self.review_filter.currentText()
        if text == "All Images":
            return None
        return text.lower().replace(" ", "_")
        
    def get_show_subfolders(self) -> bool:
        """Get current show subfolders state"""
        return self.show_subfolders_button.isChecked()
        
    def restore_state(self, settings: dict):
        """Restore toolbar state from settings"""
        try:
            if 'thumbnail_size' in settings:
                self.thumbnail_size.setValue(settings['thumbnail_size'])
            if 'sort_by' in settings:
                index = self.sort_by.findText(settings['sort_by'])
                if index >= 0:
                    self.sort_by.setCurrentIndex(index)
            if 'rating_filter' in settings:
                index = self.rating_filter.findText(settings['rating_filter'])
                if index >= 0:
                    self.rating_filter.setCurrentIndex(index)
            if 'review_filter' in settings:
                index = self.review_filter.findText(settings['review_filter'])
                if index >= 0:
                    self.review_filter.setCurrentIndex(index)
            if 'show_subfolders' in settings:
                self.show_subfolders_button.setChecked(settings['show_subfolders'])
        except Exception as e:
            logger.error(f"Error restoring toolbar state: {e}")
            
    def save_state(self) -> dict:
        """Save toolbar state to settings"""
        return {
            'thumbnail_size': self.thumbnail_size.value(),
            'sort_by': self.sort_by.currentText(),
            'rating_filter': self.rating_filter.currentText(),
            'review_filter': self.review_filter.currentText(),
            'show_subfolders': self.show_subfolders_button.isChecked()
        } 