"""Metadata entry panel for editing image metadata"""

import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QTextEdit, QSpinBox, QComboBox, QPushButton,
    QLabel, QScrollArea
)

from core.domain.entities.image import Image
from core.domain.repositories.image_repository import ImageRepository
from core.application.services.metadata_service import MetadataService

logger = logging.getLogger(__name__)

class MetadataEntryPanel(QScrollArea):
    """Panel for editing image metadata"""
    
    metadata_updated = pyqtSignal(Image, dict)  # Signals (image, metadata)
    
    def __init__(self, 
                 image_repository: ImageRepository,
                 metadata_service: MetadataService,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Store dependencies
        self.image_repository = image_repository
        self.metadata_service = metadata_service
        
        # Initialize state
        self.current_image: Optional[Image] = None
        self.metadata_fields: Dict[str, QWidget] = {}
        self.current_metadata: Dict[str, Any] = {}
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Create container widget
        container = QWidget()
        self.setWidget(container)
        self.setWidgetResizable(True)
        
        # Create layout
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Create form layout for metadata fields
        self.form_layout = QFormLayout()
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.form_layout.setSpacing(5)
        layout.addLayout(self.form_layout)
        
        # Add metadata fields
        self._add_metadata_fields()
        
        # Add save button
        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self._save_metadata)
        layout.addWidget(self.save_button)
        
        # Add stretch at bottom
        layout.addStretch()
        
        # Style
        self.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e1e;
                border: none;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLineEdit, QTextEdit, QSpinBox, QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 5px;
                color: #ffffff;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #0078d4;
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
        
    def _add_metadata_fields(self):
        """Add metadata input fields"""
        # Basic fields
        self.metadata_fields['name'] = QLineEdit()
        self.form_layout.addRow("Name:", self.metadata_fields['name'])
        
        self.metadata_fields['prompt'] = QTextEdit()
        self.metadata_fields['prompt'].setMaximumHeight(100)
        self.form_layout.addRow("Prompt:", self.metadata_fields['prompt'])
        
        self.metadata_fields['negative_prompt'] = QTextEdit()
        self.metadata_fields['negative_prompt'].setMaximumHeight(100)
        self.form_layout.addRow("Negative Prompt:", self.metadata_fields['negative_prompt'])
        
        # Numeric fields
        self.metadata_fields['steps'] = QSpinBox()
        self.metadata_fields['steps'].setRange(1, 150)
        self.form_layout.addRow("Steps:", self.metadata_fields['steps'])
        
        self.metadata_fields['cfg_scale'] = QSpinBox()
        self.metadata_fields['cfg_scale'].setRange(1, 30)
        self.form_layout.addRow("CFG Scale:", self.metadata_fields['cfg_scale'])
        
        # Model selection
        self.metadata_fields['model'] = QComboBox()
        self.metadata_fields['model'].setEditable(True)
        self.form_layout.addRow("Model:", self.metadata_fields['model'])
        
    def set_image(self, image: Optional[Image]):
        """Set the current image and update fields"""
        try:
            if image and image.path == getattr(self.current_image, 'path', None):
                # Same image, no need to update
                return
                
            self.current_image = image
            if image and image.metadata:
                logger.debug(f"Setting metadata panel for image: {image.path}")
                
                # Get metadata from cached metadata
                self.current_metadata = {}
                if hasattr(image.metadata, 'custom_metadata'):
                    self.current_metadata = image.metadata.custom_metadata.get('invokeai', {})
                
                # Update fields with cached metadata
                self.metadata_fields['name'].setText(image.name)
                self.metadata_fields['prompt'].setText(self.current_metadata.get('prompt', ''))
                self.metadata_fields['negative_prompt'].setText(self.current_metadata.get('negative_prompt', ''))
                
                # Handle numeric fields safely
                try:
                    steps = int(self.current_metadata.get('steps', 20))
                    self.metadata_fields['steps'].setValue(steps)
                except (ValueError, TypeError):
                    self.metadata_fields['steps'].setValue(20)
                    
                try:
                    cfg_scale = int(self.current_metadata.get('cfg_scale', 7))
                    self.metadata_fields['cfg_scale'].setValue(cfg_scale)
                except (ValueError, TypeError):
                    self.metadata_fields['cfg_scale'].setValue(7)
                
                self.metadata_fields['model'].setCurrentText(self.current_metadata.get('model', ''))
                
                # Enable editing
                self._set_fields_enabled(True)
            else:
                logger.debug("No image selected, clearing metadata panel")
                self.current_metadata = {}
                self._clear_fields()
                
        except Exception as e:
            logger.error(f"Error setting image metadata: {e}")
            self._clear_fields()
            
    def _clear_fields(self):
        """Clear all metadata fields"""
        for field in self.metadata_fields.values():
            if isinstance(field, (QLineEdit, QTextEdit)):
                field.clear()
            elif isinstance(field, QSpinBox):
                field.setValue(field.minimum())
            elif isinstance(field, QComboBox):
                field.setCurrentIndex(0)
        self._set_fields_enabled(False)
            
    def _set_fields_enabled(self, enabled: bool):
        """Enable or disable all fields"""
        for field in self.metadata_fields.values():
            field.setEnabled(enabled)
        self.save_button.setEnabled(enabled)
        
    def _save_metadata(self):
        """Save metadata changes"""
        if not self.current_image:
            return
            
        try:
            # Collect metadata from fields
            metadata = {
                'invokeai': {
                    'prompt': self.metadata_fields['prompt'].toPlainText(),
                    'negative_prompt': self.metadata_fields['negative_prompt'].toPlainText(),
                    'steps': self.metadata_fields['steps'].value(),
                    'cfg_scale': self.metadata_fields['cfg_scale'].value(),
                    'model': self.metadata_fields['model'].currentText(),
                }
            }
            
            # Only update if metadata has changed
            if metadata['invokeai'] != self.current_metadata:
                # Update the image's metadata
                if not hasattr(self.current_image.metadata, 'custom_metadata'):
                    self.current_image.metadata.custom_metadata = {}
                self.current_image.metadata.custom_metadata.update(metadata)
                
                # Save through metadata service
                if self.metadata_service.update_metadata(self.current_image, metadata):
                    self.current_metadata = metadata['invokeai']
                    self.metadata_updated.emit(self.current_image, metadata)
                    logger.info(f"Updated metadata for {self.current_image.path}")
                else:
                    logger.error(f"Failed to update metadata for {self.current_image.path}")
                    
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")