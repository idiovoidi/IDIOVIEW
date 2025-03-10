"""Filter panel for image filtering"""

import logging
from typing import Optional, List, Dict, Any
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QSpinBox, QFrame
)

from core.domain.entities.image import Image
from core.domain.repositories.image_repository import ImageRepository
from core.application.services.metadata_service import MetadataService

logger = logging.getLogger(__name__)

class FilterPanel(QFrame):  # Changed to QFrame for better styling
    """Compact panel for filtering images"""
    
    filterChanged = pyqtSignal()  # Emitted when filters change
    
    def __init__(self, 
                 metadata_service: MetadataService,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Store dependencies
        self.metadata_service = metadata_service
        
        # Initialize state
        self.filters: Dict[str, Any] = {}
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Add title
        title = QLabel("Filters")
        title.setStyleSheet("font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #3d3d3d;")
        layout.addWidget(separator)
        
        # Add filter controls
        self._add_filter_controls(layout)
        
        # Add clear button
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_filters)
        clear_btn.setFixedHeight(30)
        layout.addWidget(clear_btn)
        
        # Style
        self.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
            QComboBox, QSpinBox {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 5px;
                color: #ffffff;
                min-width: 100px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
            }
            QPushButton {
                background-color: #0078d4;
                border: none;
                border-radius: 3px;
                padding: 5px 15px;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #2b88d8;
            }
            QLabel {
                color: #cccccc;
            }
        """)
        
    def _add_filter_controls(self, layout: QVBoxLayout):
        """Add filter control widgets"""
        # Rating filter
        rating_layout = QHBoxLayout()
        rating_layout.addWidget(QLabel("Min Rating:"))
        self.rating_filter = QSpinBox()
        self.rating_filter.setRange(0, 5)
        self.rating_filter.valueChanged.connect(self._on_filter_changed)
        rating_layout.addWidget(self.rating_filter)
        rating_layout.addStretch()
        layout.addLayout(rating_layout)
        
        # Model filter
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model_filter = QComboBox()
        self.model_filter.currentTextChanged.connect(self._on_filter_changed)
        model_layout.addWidget(self.model_filter)
        model_layout.addStretch()
        layout.addLayout(model_layout)
        
        # Add more filters as needed...
        
    def _on_filter_changed(self):
        """Handle filter changes"""
        # Update filters dict
        self.filters = {
            'model': self.model_filter.currentText() if self.model_filter.currentText() != "All Models" else None,
            'min_rating': self.rating_filter.value()
        }
        
        # Remove None values
        self.filters = {k: v for k, v in self.filters.items() if v is not None and v != 0}
        
        # Emit signal
        self.filterChanged.emit()
        
    def clear_filters(self):
        """Clear all filters"""
        self.model_filter.setCurrentIndex(0)
        self.rating_filter.setValue(0)
        self.filters.clear()
        self.filterChanged.emit()
        
    def update_model_list(self, images: List[Image]):
        """Update model filter list from images"""
        try:
            # Get unique models
            models = set()
            for image in images:
                if metadata := self.metadata_service.get_metadata(image):
                    if model := metadata.get('model'):
                        models.add(model)
                    
            # Update combobox
            current = self.model_filter.currentText()
            self.model_filter.clear()
            self.model_filter.addItem("All Models")
            self.model_filter.addItems(sorted(models))
            
            # Restore selection if still valid
            index = self.model_filter.findText(current)
            if index >= 0:
                self.model_filter.setCurrentIndex(index)
                
        except Exception as e:
            logger.error(f"Error updating model list: {e}")
            
    def get_filters(self) -> Dict[str, Any]:
        """Get current filter settings"""
        return self.filters.copy() 