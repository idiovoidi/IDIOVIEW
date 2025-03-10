"""Metadata search panel for searching and filtering images"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea,
    QFormLayout, QLineEdit, QTextEdit, QSpinBox,
    QHBoxLayout, QPushButton, QListWidget, QMessageBox,
    QGroupBox, QTreeWidget, QTreeWidgetItem, QComboBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from collections import defaultdict
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

from core.domain.entities.image import Image
from core.domain.repositories.image_repository import ImageRepository
from core.application.services.metadata_service import MetadataService

logger = logging.getLogger(__name__)

class MetadataSearchPanel(QWidget):
    """Panel for searching and filtering images based on metadata"""
    
    filter_applied = pyqtSignal(dict)  # Emitted when filter is applied
    image_selected = pyqtSignal(object)  # Emitted when image is selected
    
    def __init__(self, 
                 image_repository: ImageRepository,
                 metadata_service: MetadataService,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Store dependencies
        self.image_repository = image_repository
        self.metadata_service = metadata_service
        
        # Initialize state
        self.metadata_cache: Dict[str, Dict[str, Any]] = {}
        self.current_directory: Optional[str] = None
        self.is_scanning = False
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Quick filters section
        quick_filters = QGroupBox("Quick Filters")
        quick_layout = QVBoxLayout(quick_filters)
        
        # Common filters buttons
        common_filters_layout = QHBoxLayout()
        
        # Add buttons for common filters
        self.add_quick_filter_button("No Tags", lambda: self.quick_filter("Tags", ""), common_filters_layout)
        self.add_quick_filter_button("No Title", lambda: self.quick_filter("Title", ""), common_filters_layout)
        self.add_quick_filter_button("No Source", lambda: self.quick_filter("Source", ""), common_filters_layout)
        
        quick_layout.addLayout(common_filters_layout)
        
        # Add model filters
        model_layout = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.setPlaceholderText("Filter by Model")
        model_layout.addWidget(QLabel("Model:"))
        model_layout.addWidget(self.model_combo)
        quick_layout.addLayout(model_layout)
        
        # Add steps/cfg filters
        params_layout = QHBoxLayout()
        self.steps_combo = QComboBox()
        self.cfg_combo = QComboBox()
        self.steps_combo.setPlaceholderText("Steps")
        self.cfg_combo.setPlaceholderText("CFG Scale")
        
        params_layout.addWidget(QLabel("Steps:"))
        params_layout.addWidget(self.steps_combo)
        params_layout.addWidget(QLabel("CFG:"))
        params_layout.addWidget(self.cfg_combo)
        quick_layout.addLayout(params_layout)
        
        layout.addWidget(quick_filters)
        
        # Search controls
        search_group = QGroupBox("Search")
        search_layout = QVBoxLayout(search_group)
        
        # Search input row
        input_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search metadata...")
        self.search_input.textChanged.connect(self.filter_results)
        input_layout.addWidget(self.search_input)
        
        # Field selector
        self.field_selector = QComboBox()
        self.field_selector.addItems([
            "All Fields",
            "Title",
            "Tags",
            "Source",
            "Category",
            "Author",
            "Model",
            "Steps",
            "CFG Scale"
        ])
        self.field_selector.currentTextChanged.connect(self.filter_results)
        input_layout.addWidget(self.field_selector)
        
        search_layout.addLayout(input_layout)
        layout.addWidget(search_group)
        
        # Results view
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_view = QTreeWidget()
        self.results_view.setHeaderLabels(["Field", "Value", "Count"])
        self.results_view.setAlternatingRowColors(True)
        self.results_view.itemClicked.connect(self.on_result_clicked)
        results_layout.addWidget(self.results_view)
        
        # Add refresh button
        refresh_btn = QPushButton("Refresh Metadata")
        refresh_btn.clicked.connect(self.scan_metadata)
        results_layout.addWidget(refresh_btn)
        
        layout.addWidget(results_group)
        
        # Status bar
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        
        # Style
        self.setStyleSheet("""
            QGroupBox {
                background-color: #2d2d2d;
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 1em;
                padding-top: 1em;
            }
            QGroupBox::title {
                color: white;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
            QTreeWidget {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #555555;
            }
            QTreeWidget::item:alternate {
                background-color: #353535;
            }
            QTreeWidget::item:selected {
                background-color: #0078d4;
            }
            QLineEdit, QComboBox {
                background-color: #3d3d3d;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
                color: white;
            }
            QPushButton {
                background-color: #0078d4;
                border: none;
                border-radius: 3px;
                padding: 5px 10px;
                color: white;
            }
            QPushButton:hover {
                background-color: #2997ff;
            }
        """)
        
        # Initial metadata scan
        QTimer.singleShot(100, self.scan_metadata)
        
    def add_quick_filter_button(self, text: str, callback: callable, layout: QHBoxLayout):
        """Add a quick filter button"""
        btn = QPushButton(text)
        btn.clicked.connect(callback)
        btn.setFixedHeight(30)
        layout.addWidget(btn)
        
    def quick_filter(self, field: str, value: str):
        """Apply a quick filter"""
        try:
            # Find matching images
            matching_images = []
            for data in self.metadata_cache.values():
                metadata = data['metadata']
                if str(metadata.get(field, '')).lower() == value.lower():
                    matching_images.append(data['image'])
            
            if matching_images:
                self.filter_applied.emit({
                    'field': field,
                    'value': value,
                    'images': matching_images
                })
                self.status_label.setText(f"Found {len(matching_images)} images with {field}: {value}")
            else:
                self.status_label.setText(f"No images found with {field}: {value}")
                
        except Exception as e:
            logger.error(f"Error applying quick filter: {e}")
            
    def update_quick_filters(self):
        """Update quick filter options based on metadata"""
        try:
            # Collect unique values
            models = set()
            steps = set()
            cfg_scales = set()
            
            for data in self.metadata_cache.values():
                metadata = data['metadata']
                if model := metadata.get('Model'):
                    models.add(str(model))
                if steps_val := metadata.get('Steps'):
                    steps.add(str(steps_val))
                if cfg := metadata.get('CFG Scale'):
                    cfg_scales.add(str(cfg))
            
            # Update combos
            self.model_combo.clear()
            self.model_combo.addItem("")  # Empty option
            self.model_combo.addItems(sorted(models))
            
            self.steps_combo.clear()
            self.steps_combo.addItem("")
            self.steps_combo.addItems(sorted(steps, key=lambda x: float(x) if x.replace('.','').isdigit() else 0))
            
            self.cfg_combo.clear()
            self.cfg_combo.addItem("")
            self.cfg_combo.addItems(sorted(cfg_scales, key=lambda x: float(x) if x.replace('.','').isdigit() else 0))
            
            # Connect signals
            self.model_combo.currentTextChanged.connect(
                lambda text: self.quick_filter("Model", text) if text else None)
            self.steps_combo.currentTextChanged.connect(
                lambda text: self.quick_filter("Steps", text) if text else None)
            self.cfg_combo.currentTextChanged.connect(
                lambda text: self.quick_filter("CFG Scale", text) if text else None)
            
        except Exception as e:
            logger.error(f"Error updating quick filters: {e}")
            
    def scan_metadata(self, directory: Optional[str] = None):
        """Scan all images and build metadata index"""
        try:
            if self.is_scanning or (directory and directory == self.current_directory):
                return
                
            self.is_scanning = True
            self.metadata_cache.clear()
            self.results_view.clear()
            
            # Use current or new directory
            scan_dir = directory or self.current_directory
            if not scan_dir:
                self.status_label.setText("No directory selected")
                self.is_scanning = False
                return
                
            self.current_directory = scan_dir
            
            # Get all images from repository
            images = self.image_repository.list_images(scan_dir)
            if not images:
                self.status_label.setText("No images found")
                self.is_scanning = False
                return
                
            # Show progress
            self.status_label.setText("Scanning metadata...")
            QApplication.processEvents()
            
            # Collect metadata
            for image in images:
                try:
                    metadata = self.metadata_service.get_metadata(image)
                    
                    # Format metadata for display
                    formatted_metadata = {
                        'Title': metadata.get('title', ''),
                        'Tags': ', '.join(metadata.get('tags', [])),
                        'Source': metadata.get('source', ''),
                        'Category': metadata.get('category', ''),
                        'Author': metadata.get('author', ''),
                        'Model': metadata.get('model', ''),
                        'Steps': metadata.get('steps', ''),
                        'CFG Scale': metadata.get('cfg_scale', '')
                    }
                    
                    # Store in cache with reference to image
                    self.metadata_cache[image.path] = {
                        'metadata': formatted_metadata,
                        'image': image
                    }
                    
                except Exception as e:
                    logger.debug(f"Error processing metadata for {image.path}: {e}")
                    continue
                    
            # Update display
            self.update_results_view()
            self.update_quick_filters()
            self.status_label.setText(f"Found metadata for {len(self.metadata_cache)} images")
            
        except Exception as e:
            logger.error(f"Error scanning metadata: {e}")
            self.status_label.setText("Error scanning metadata")
        finally:
            self.is_scanning = False
            
    def update_results_view(self, filter_text: str = "", field: str = "All Fields"):
        """Update the results tree with filtered metadata"""
        try:
            self.results_view.clear()
            
            # Collect and group metadata
            field_values = defaultdict(lambda: defaultdict(list))
            
            for image_path, data in self.metadata_cache.items():
                metadata = data['metadata']
                
                # Apply filters
                if field == "All Fields":
                    # Search all fields
                    matches = any(
                        filter_text.lower() in str(value).lower()
                        for value in metadata.values()
                    )
                else:
                    # Search specific field
                    matches = filter_text.lower() in str(metadata.get(field, '')).lower()
                
                if not filter_text or matches:
                    # Group by field and value
                    for key, value in metadata.items():
                        if value:  # Only include non-empty values
                            field_values[key][str(value)].append(data['image'])
            
            # Create tree items
            for field, values in field_values.items():
                field_item = QTreeWidgetItem([field, "", str(sum(len(imgs) for imgs in values.values()))])
                self.results_view.addTopLevelItem(field_item)
                
                # Add values
                for value, images in values.items():
                    value_item = QTreeWidgetItem([
                        "",  # No field name
                        value,  # The value
                        str(len(images))  # Count of images
                    ])
                    value_item.setData(0, Qt.ItemDataRole.UserRole, images)  # Store image references
                    field_item.addChild(value_item)
                
            # Expand all items
            self.results_view.expandAll()
            
        except Exception as e:
            logger.error(f"Error updating results: {e}")
            
    def filter_results(self):
        """Apply current filter to results"""
        filter_text = self.search_input.text()
        field = self.field_selector.currentText()
        self.update_results_view(filter_text, field)
        
    def on_result_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle clicking on a result item"""
        try:
            # Get stored images if any
            images = item.data(0, Qt.ItemDataRole.UserRole)
            if images:
                # Emit signal with images
                self.filter_applied.emit({
                    'field': item.parent().text(0),
                    'value': item.text(1),
                    'images': images
                })
                
        except Exception as e:
            logger.error(f"Error handling result click: {e}")