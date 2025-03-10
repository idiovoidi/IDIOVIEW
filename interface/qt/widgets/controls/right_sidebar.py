"""Unified sidebar widget for all panels"""

import logging
from typing import Optional, Dict
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, 
    QStackedWidget, QSpacerItem, QSizePolicy,
    QTabWidget
)

logger = logging.getLogger(__name__)

class RightSidebar(QWidget):
    """Unified sidebar for all panels"""
    
    # Signals
    panel_toggled = pyqtSignal(str, bool)  # panel_id, visible
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.panels = {}  # panel_id -> QWidget
        self.current_panel = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tab_widget)
        
        # Style
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
            }
            QTabWidget::pane {
                border: none;
                background-color: #1e1e1e;
            }
            QTabWidget::tab-bar {
                alignment: left;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #cccccc;
                padding: 8px 16px;
                border: none;
                min-width: 80px;
            }
            QTabBar::tab:hover {
                background-color: #3d3d3d;
            }
            QTabBar::tab:selected {
                background-color: #0078d4;
                color: white;
            }
        """)
        
        # Set minimum width
        self.setMinimumWidth(250)
        
    def register_panel(self, panel_id: str, panel: QWidget) -> None:
        """Register a panel to be displayed in the sidebar"""
        self.panels[panel_id] = panel
        
        # Get tab label based on panel_id
        tab_labels = {
            "info": "Info ℹ️",
            "search": "Search 🔍",
            "edit": "Edit ✏️",
            "tags": "Tags 🏷️",
            "rating": "Rating ⭐",
            "filters": "Filters 🔧"
        }
        
        # Add panel to tab widget with appropriate label
        label = tab_labels.get(panel_id, panel_id)
        self.tab_widget.addTab(panel, label)
        
        # If this is the info panel, make it the first tab and show it
        if panel_id == "info":
            self.tab_widget.tabBar().moveTab(self.tab_widget.count() - 1, 0)
            self.tab_widget.setCurrentIndex(0)
            self.current_panel = panel_id
            self.panel_toggled.emit(panel_id, True)
        # Otherwise, only set as current if no panel is currently shown
        elif not self.current_panel:
            self.current_panel = panel_id
            self.panel_toggled.emit(panel_id, True)
            
    def _on_tab_changed(self, index: int) -> None:
        """Handle tab change events"""
        if index >= 0 and index < len(self.panels):
            # Hide previous panel if it exists
            if self.current_panel:
                self.panel_toggled.emit(self.current_panel, False)
            
            # Show new panel
            panel_id = list(self.panels.keys())[index]
            self.current_panel = panel_id
            self.panel_toggled.emit(panel_id, True)
        
    def show_panel(self, panel_id: str) -> None:
        """Show a specific panel"""
        if panel_id in self.panels:
            index = list(self.panels.keys()).index(panel_id)
            self.tab_widget.setCurrentIndex(index)
            
    def hide_panel(self, panel_id: str) -> None:
        """Hide a specific panel"""
        if panel_id == self.current_panel:
            self.tab_widget.setCurrentIndex(-1)  # Deselect current tab 