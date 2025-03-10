"""Tag management panel widget"""

import logging
from typing import Optional, List
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QListWidget
)
from PyQt6.QtCore import pyqtSignal

from core.application.services.metadata_service import MetadataService
from interface.qt.shared.styles import COLORS
from core.domain.entities.image import Image
from core.domain.entities.image_metadata import ImageMetadata

logger = logging.getLogger(__name__)

class TagPanel(QWidget):
    """Panel for managing image tags"""
    
    # Signals
    tags_updated = pyqtSignal(str, list)  # image_path, tags
    
    def __init__(self, metadata_service: MetadataService, parent=None):
        super().__init__(parent)
        self.metadata_service = metadata_service
        self.current_image_path: Optional[str] = None
        self._setup_ui()
        self._setup_style()
        
    def _setup_style(self):
        """Setup widget styling"""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
            }}
            QLineEdit {{
                background-color: {COLORS['background_alt']};
                border: 1px solid {COLORS['border']};
                border-radius: 3px;
                padding: 5px;
                color: {COLORS['text']};
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                border: none;
                border-radius: 3px;
                padding: 5px 15px;
                color: {COLORS['text']};
            }}
            QPushButton:hover {{
                background-color: {COLORS['hover']};
            }}
            QListWidget {{
                background-color: {COLORS['background_alt']};
                border: 1px solid {COLORS['border']};
                border-radius: 3px;
                color: {COLORS['text']};
            }}
        """)
        
    def _setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header
        header = QLabel("Tags")
        header.setStyleSheet(f"font-weight: bold; color: {COLORS['text']};")
        layout.addWidget(header)
        
        # Add tag input
        input_layout = QHBoxLayout()
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Enter tag...")
        self.tag_input.returnPressed.connect(self._add_tag)
        
        add_button = QPushButton("Add")
        add_button.clicked.connect(self._add_tag)
        
        input_layout.addWidget(self.tag_input)
        input_layout.addWidget(add_button)
        layout.addLayout(input_layout)
        
        # Tag list
        self.tag_list = QListWidget()
        layout.addWidget(self.tag_list)
        
        # Remove button
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self._remove_selected_tag)
        layout.addWidget(remove_button)
        
    def clear(self):
        """Clear the panel"""
        self.tag_list.clear()
        self.tag_input.clear()
        self.current_image_path = None
        
    def update_display(self, image_path: str):
        """Update display with image's tags"""
        try:
            self.current_image_path = image_path
            self.tag_list.clear()
            
            if not image_path or not Path(image_path).exists():
                return
                
            # Create Image object
            path = Path(image_path)
            stats = path.stat()
            metadata = ImageMetadata(
                width=0,  # Will be filled when needed
                height=0,  # Will be filled when needed
                format=path.suffix[1:].lower(),
                size_bytes=stats.st_size,
                created_at=datetime.fromtimestamp(stats.st_ctime),
                modified_at=datetime.fromtimestamp(stats.st_mtime)
            )
            image = Image(
                path=str(path),
                name=path.name,
                metadata=metadata
            )
                
            metadata = self.metadata_service.get_metadata(image)
            if metadata and metadata.get('tags'):
                for tag in sorted(metadata['tags']):
                    self.tag_list.addItem(tag)
                    
        except Exception as e:
            logger.error(f"Error updating tag display: {e}")
            
    def _add_tag(self):
        """Add a new tag"""
        try:
            tag = self.tag_input.text().strip()
            if not tag or not self.current_image_path:
                return
                
            # Add to list if not already present
            existing_items = [
                self.tag_list.item(i).text() 
                for i in range(self.tag_list.count())
            ]
            
            if tag not in existing_items:
                self.tag_list.addItem(tag)
                self._save_tags()
                
            self.tag_input.clear()
            
        except Exception as e:
            logger.error(f"Error adding tag: {e}")
            
    def _remove_selected_tag(self):
        """Remove selected tag"""
        try:
            selected = self.tag_list.selectedItems()
            if not selected:
                return
                
            for item in selected:
                self.tag_list.takeItem(self.tag_list.row(item))
                
            self._save_tags()
            
        except Exception as e:
            logger.error(f"Error removing tag: {e}")
            
    def _save_tags(self):
        """Save tags to image metadata"""
        try:
            if not self.current_image_path:
                return
                
            tags = [
                self.tag_list.item(i).text() 
                for i in range(self.tag_list.count())
            ]
            
            if self.metadata_service.update_tags(self.current_image_path, set(tags)):
                self.tags_updated.emit(self.current_image_path, tags)
            else:
                logger.error("Failed to save tags")
                
        except Exception as e:
            logger.error(f"Error saving tags: {e}")
            
    def get_tags(self) -> List[str]:
        """Get current tags"""
        return [
            self.tag_list.item(i).text() 
            for i in range(self.tag_list.count())
        ]

__all__ = ['TagPanel'] 