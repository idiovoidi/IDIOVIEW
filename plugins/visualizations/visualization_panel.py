"""Visualization panel widget for data analysis"""

import logging
from typing import Optional, Dict, Type, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QComboBox, 
    QLabel, QPushButton, QStackedWidget
)
from PyQt6.QtCore import pyqtSignal

# Import base class directly to avoid plugin system dependency
from plugins.visualizations.base import BaseVisualization
from plugins import PluginManager

logger = logging.getLogger(__name__)

class VisualizationPanel(QWidget):
    """Panel for managing and displaying visualizations"""
    
    # Signals
    visualization_changed = pyqtSignal(str)  # Emitted when visualization type changes
    visualization_updated = pyqtSignal()     # Emitted when visualization is updated
    error_occurred = pyqtSignal(str)         # Emitted when an error occurs
    
    def __init__(self, plugin_manager: PluginManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self._plugin_manager = plugin_manager
        self._current_viz: Optional[BaseVisualization] = None
        self._visualizations: Dict[str, Type[BaseVisualization]] = {}
        
        self._init_ui()
        self._load_visualizations()
        
    def _init_ui(self) -> None:
        """Initialize the UI components"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Controls
        controls = QWidget()
        controls_layout = QVBoxLayout()
        controls.setLayout(controls_layout)
        
        # Visualization selector
        selector_layout = QVBoxLayout()
        selector_label = QLabel("Visualization Type:")
        self._viz_selector = QComboBox()
        self._viz_selector.currentIndexChanged.connect(self._on_visualization_changed)
        selector_layout.addWidget(selector_label)
        selector_layout.addWidget(self._viz_selector)
        controls_layout.addLayout(selector_layout)
        
        # Refresh button
        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self._on_refresh_clicked)
        controls_layout.addWidget(self._refresh_btn)
        
        layout.addWidget(controls)
        
        # Visualization container
        self._viz_stack = QStackedWidget()
        layout.addWidget(self._viz_stack)
        
        # Apply dark theme
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                padding: 5px;
            }
            QPushButton {
                background-color: #0078d4;
                border: none;
                border-radius: 3px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #2b88d8;
            }
            QLabel {
                color: #cccccc;
            }
        """)
        
    def _load_visualizations(self) -> None:
        """Load available visualization types"""
        try:
            # Get visualization plugin
            viz_plugin = self._plugin_manager.get_plugin("visualizations")
            if not viz_plugin:
                logger.info("No visualization plugins found")
                return
                
            # Get available visualization types
            self._visualizations = viz_plugin
            
            # Update selector
            self._viz_selector.clear()
            self._viz_selector.addItem("None")
            for name in sorted(self._visualizations.keys()):
                self._viz_selector.addItem(name)
                
            logger.info(f"Loaded {len(self._visualizations)} visualization types")
            
        except Exception as e:
            logger.error(f"Error loading visualizations: {e}")
            self.error_occurred.emit(str(e))
            
    def _on_visualization_changed(self, index: int) -> None:
        """Handle visualization type selection"""
        try:
            # Clean up current visualization
            if self._current_viz:
                self._current_viz.cleanup()
                self._current_viz = None
                
            # Get selected visualization type
            viz_name = self._viz_selector.currentText()
            if not viz_name or viz_name == "None" or viz_name not in self._visualizations:
                return
                
            # Initialize new visualization
            viz_class = self._visualizations[viz_name]
            self._current_viz = viz_class()
            
            if self._current_viz.initialize():
                # Add to widget stack
                self._viz_stack.addWidget(self._current_viz.widget)
                self._viz_stack.setCurrentWidget(self._current_viz.widget)
                logger.info(f"Switched to visualization: {viz_name}")
                self.visualization_changed.emit(viz_name)
            else:
                logger.error(f"Failed to initialize visualization: {viz_name}")
                self._current_viz = None
                self.error_occurred.emit(f"Failed to initialize {viz_name}")
                
        except Exception as e:
            logger.error(f"Error changing visualization: {e}")
            self.error_occurred.emit(str(e))
            
    def _on_refresh_clicked(self) -> None:
        """Handle refresh button click"""
        try:
            if self._current_viz:
                self._current_viz.update()
                self.visualization_updated.emit()
        except Exception as e:
            logger.error(f"Error refreshing visualization: {e}")
            self.error_occurred.emit(str(e))
            
    def update_data(self, data: Any) -> None:
        """Update current visualization with new data"""
        try:
            if self._current_viz:
                self._current_viz.update(data)
                self.visualization_updated.emit()
        except Exception as e:
            logger.error(f"Error updating visualization data: {e}")
            self.error_occurred.emit(str(e))
            
    def cleanup(self) -> None:
        """Clean up panel resources"""
        try:
            if self._current_viz:
                self._current_viz.cleanup()
                self._current_viz = None
            self._visualizations.clear()
        except Exception as e:
            logger.error(f"Error cleaning up visualization panel: {e}")
            self.error_occurred.emit(str(e)) 