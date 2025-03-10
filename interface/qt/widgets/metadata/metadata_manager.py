from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea,
    QFormLayout, QLineEdit, QTextEdit, QSpinBox,
    QHBoxLayout, QPushButton, QListWidget, QMessageBox,
    QGroupBox, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QImageReader
import json
import logging
from PIL import Image as PILImage
from PIL.PngImagePlugin import PngInfo
from interface.qt.shared.styles import INFO_PANEL_STYLE, INFO_HTML_TEMPLATE, COLORS
import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from core.domain.entities.image import Image as ImageEntity
from core.domain.entities.image_metadata import ImageMetadata
from core.domain.entities.image_status import ImageStatus
from core.infrastructure.utils.image_utils import open_image_efficient, save_image_optimized

from core.application.services.metadata_service import MetadataService

logger = logging.getLogger("GalleryViewer.MetadataManager")

class MetadataManager:
    """Handles metadata operations and UI management"""
    def __init__(self, metadata_service: MetadataService):
        self.logger = logger
        self.metadata_service = metadata_service
        self.batch_operation = False

    def set_batch_mode(self, enabled: bool):
        """Enable/disable batch operation mode"""
        self.batch_operation = enabled

    def get_metadata(self, image_path: str) -> dict:
        """Get all metadata for an image"""
        try:
            return self.metadata_service.get_metadata_field(image_path, 'all', {})
        except Exception as e:
            self.logger.error(f"Error reading metadata from {image_path}: {e}")
            return {}

    def save_metadata(self, image_path: str, metadata: dict) -> bool:
        """Save metadata to image file"""
        try:
            return self.metadata_service.update_metadata(image_path, metadata)
        except Exception as e:
            self.logger.error(f"Error saving metadata to {image_path}: {e}")
            return False

    def get_review_status(self, image_path: str) -> str:
        """Get review status from image metadata"""
        try:
            return self.metadata_service.get_metadata_field(image_path, 'review_status', '')
        except Exception as e:
            self.logger.debug(f"Error reading review status: {e}")
            return ''

    def set_star_rating(self, image_path: str, rating: int) -> bool:
        """Set star rating for an image"""
        try:
            return self.metadata_service.set_metadata_field(image_path, 'rating', rating)
        except Exception as e:
            self.logger.error(f"Error setting star rating for {image_path}: {e}")
            return False

    def clear_cache(self):
        """Clear metadata cache"""
        # This method is no longer needed as the metadata_service handles caching

    def read_metadata(self, image_path: str) -> Dict[str, Any]:
        """Read metadata from an image file"""
        try:
            # Use QImageReader for basic image info
            reader = QImageReader(image_path)
            size = reader.size()
            format_name = reader.format().data().decode()
            
            metadata = {
                'width': size.width(),
                'height': size.height(),
                'format': format_name,
                'size_mb': Path(image_path).stat().st_size / (1024 * 1024)
            }
            
            # Use PIL only for metadata extraction
            try:
                with PILImage.open(image_path) as img:
                    if 'invokeai_metadata' in img.info:
                        metadata['invokeai_metadata'] = json.loads(img.info['invokeai_metadata'])
                    # Add any EXIF data if needed
                    if hasattr(img, '_getexif') and (exif := img._getexif()):
                        metadata['exif'] = exif
            except Exception as e:
                self.logger.debug(f"Error reading PIL metadata: {e}")
                
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error reading metadata from {image_path}: {e}")
            return {}

    def write_metadata(self, image_path: str, metadata: Dict[str, Any]) -> bool:
        """Write metadata to an image file"""
        try:
            # Only use PIL for metadata writing
            with PILImage.open(image_path) as img:
                # Update metadata
                if 'invokeai' in metadata:
                    img.info['invokeai_metadata'] = json.dumps(metadata['invokeai'])
                    
                # Save with optimized settings
                return save_image_optimized(img, image_path)
                
        except Exception as e:
            self.logger.error(f"Error writing metadata to {image_path}: {e}")
            return False

class MetadataPanel(QWidget):
    """Panel for displaying metadata"""
    metadata_updated = pyqtSignal(ImageEntity, dict)
    
    def __init__(self, 
                 metadata_service: MetadataService,
                 style: Optional[str] = None,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parent = parent
        self.logger = logging.getLogger("GalleryViewer.MetadataPanel")
        self.metadata_service = metadata_service
        self.current_image: Optional[ImageEntity] = None
        
        # Apply style if provided
        if style:
            self.setStyleSheet(style)
            
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Create metadata tree widget
        self.metadata_tree = QTreeWidget()
        self.metadata_tree.setHeaderLabels(["Property", "Value"])
        self.metadata_tree.setColumnCount(2)
        self.metadata_tree.setAlternatingRowColors(True)
        
        # Create scroll area for tree
        scroll = QScrollArea()
        scroll.setWidget(self.metadata_tree)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        # Add status label
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #888888;")
        layout.addWidget(self.status_label)

        # Style the tree widget
        self.metadata_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #0078d4;
            }
            QTreeWidget::item:hover {
                background-color: #3d3d3d;
            }
            QTreeWidget::branch {
                background-color: #2d2d2d;
            }
        """)

        # Set column widths
        self.metadata_tree.setColumnWidth(0, 200)  # Property column
        self.metadata_tree.setColumnWidth(1, 300)  # Value column

    def display_metadata(self, image: Optional[ImageEntity]):
        """Display metadata for the given image"""
        try:
            if not image or image == self.current_image:
                return
                
            self.current_image = image
            
            # Get basic image info using QImageReader
            reader = QImageReader(image.path)
            size = reader.size()
            format_name = reader.format().data().decode()
            
            # Create basic info dictionary
            basic_info = {
                'dimensions': f"{size.width()}x{size.height()}",
                'format': format_name,
                'size': f"{Path(image.path).stat().st_size / (1024 * 1024):.1f} MB"
            }
            
            # Update tree view with metadata
            self.metadata_tree.clear()
            
            # Add basic metadata first
            basic_root = QTreeWidgetItem(["Basic Information"])
            self.metadata_tree.addTopLevelItem(basic_root)
            self._add_metadata_to_tree(basic_root, basic_info)
            
            # Get additional metadata from service
            metadata = self.metadata_service.get_metadata(image)
            if metadata:
                # Add InvokeAI metadata if available
                if 'invokeai_metadata' in metadata:
                    invoke_root = QTreeWidgetItem(["InvokeAI Metadata"])
                    self.metadata_tree.addTopLevelItem(invoke_root)
                    self._add_metadata_to_tree(invoke_root, metadata['invokeai_metadata'])
                
                # Add EXIF data if available
                if 'exif' in metadata:
                    exif_root = QTreeWidgetItem(["EXIF Data"])
                    self.metadata_tree.addTopLevelItem(exif_root)
                    self._add_metadata_to_tree(exif_root, metadata['exif'])
            
            # Expand top-level items
            self.metadata_tree.expandToDepth(0)
            
        except Exception as e:
            self.logger.error(f"Error displaying metadata: {e}")
            self.status_label.setText("Error reading metadata")

    def _add_metadata_to_tree(self, parent, data):
        """Helper method to recursively add metadata to tree"""
        try:
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        item = QTreeWidgetItem([str(key)])
                        parent.addChild(item)
                        self._add_metadata_to_tree(item, value)
                    else:
                        item = QTreeWidgetItem([str(key), str(value)])
                        parent.addChild(item)
            elif isinstance(data, list):
                for i, value in enumerate(data):
                    if isinstance(value, (dict, list)):
                        item = QTreeWidgetItem([f"Item {i}"])
                        parent.addChild(item)
                        self._add_metadata_to_tree(item, value)
                    else:
                        item = QTreeWidgetItem([str(i), str(value)])
                        parent.addChild(item)
            else:
                item = QTreeWidgetItem([str(data)])
                parent.addChild(item)
                
        except Exception as e:
            self.logger.error(f"Error adding metadata to tree: {e}")

    def clear(self):
        """Clear all metadata displays"""
        try:
            self.current_image = None
            self.metadata_tree.clear()
            self.status_label.setText("")
        except Exception as e:
            self.logger.error(f"Error clearing metadata panel: {e}")
