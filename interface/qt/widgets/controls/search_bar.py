"""Search bar widget with integrated filtering"""

import logging
from typing import Callable, Optional, Dict
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
    QLabel, QPushButton, QMenu, QToolBar, QComboBox, QSpinBox, QVBoxLayout, QSpacerItem, QSizePolicy, QLineEdit, QHBoxLayout, QToolButton, QWidgetAction
)

logger = logging.getLogger(__name__)

class SearchBar(QWidget):
    """Search bar for filtering and searching images"""
    
    # Signals
    searchChanged = pyqtSignal(str, dict)  # Emits (search_text, filters)
    searchCleared = pyqtSignal()   # Emitted when search is cleared
    
    def __init__(self, filter_bar=None, parent=None):
        super().__init__(parent)
        self.search_callback = None
        self.filter_bar = filter_bar
        self.current_filters = {}
        
        # Setup search delay timer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
        
        self.setup_ui()
        
        # Connect to filter bar if provided
        if self.filter_bar:
            self.filter_bar.filterChanged.connect(self._on_filters_changed)
        
    def setup_ui(self):
        """Setup search bar UI elements"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search images...")
        self.search_input.textChanged.connect(self._handle_text_changed)
        layout.addWidget(self.search_input)
        
        # Filter button
        if self.filter_bar:
            self.filter_btn = QToolButton()
            self.filter_btn.setIcon(QIcon.fromTheme("view-filter"))
            self.filter_btn.setToolTip("Show filters")
            self.filter_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
            
            # Create menu for filter button
            filter_menu = QMenu(self)
            filter_menu.setStyleSheet("""
                QMenu {
                    background-color: #2d2d2d;
                    border: 1px solid #3d3d3d;
                }
                QMenu::item {
                    padding: 5px 20px;
                    color: #ffffff;
                }
                QMenu::item:selected {
                    background-color: #0078d4;
                }
            """)
            
            # Add filter widget to menu using QWidgetAction
            widget_action = QWidgetAction(filter_menu)
            widget_action.setDefaultWidget(self.filter_bar)
            filter_menu.addAction(widget_action)
            
            self.filter_btn.setMenu(filter_menu)
            layout.addWidget(self.filter_btn)
        
        # Clear button
        self.clear_btn = QPushButton()
        self.clear_btn.setIcon(QIcon.fromTheme("edit-clear"))
        self.clear_btn.setToolTip("Clear search")
        self.clear_btn.clicked.connect(self.clear_search)
        self.clear_btn.hide()
        layout.addWidget(self.clear_btn)
        
        # Style
        self.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                background-color: #2d2d2d;
                color: #cccccc;
                min-width: 200px;
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
            QPushButton, QToolButton {
                background: transparent;
                border: none;
                padding: 5px;
            }
            QPushButton:hover, QToolButton:hover {
                background-color: #3d3d3d;
                border-radius: 3px;
            }
        """)
        
    def set_search_callback(self, callback: Callable[[str, Dict], None]):
        """Set the callback for when search text or filters change"""
        self.search_callback = callback
        
    def _handle_text_changed(self, text: str):
        """Handle search text changes"""
        # Show/hide clear button
        self.clear_btn.setVisible(bool(text))
        
        # Reset and start timer for search callback
        self.search_timer.stop()
        self.search_timer.start(300)  # 300ms delay
        
    def _on_filters_changed(self):
        """Handle filter changes from filter bar"""
        if self.filter_bar:
            self.current_filters = self.filter_bar.get_filters()
            self._perform_search()
        
    def _perform_search(self):
        """Perform the actual search with current text and filters"""
        search_text = self.search_input.text()
        
        # Emit combined search/filter signal
        self.searchChanged.emit(search_text, self.current_filters)
        
        # Call callback if set
        if self.search_callback:
            self.search_callback(search_text, self.current_filters)
            
    def clear_search(self):
        """Clear the search input and filters"""
        self.search_input.clear()
        if self.filter_bar:
            self.filter_bar.clear_filters()
        self.current_filters = {}
        self.searchCleared.emit()
        
    def get_search_text(self) -> str:
        """Get current search text"""
        return self.search_input.text()
        
    def get_current_filters(self) -> Dict:
        """Get current filter settings"""
        return self.current_filters.copy() 