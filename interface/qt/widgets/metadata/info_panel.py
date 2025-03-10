from PyQt6.QtWidgets import QTextBrowser, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextDocument, QImageReader
from PIL import Image as PILImage
from pathlib import Path
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from interface.qt.shared.styles import INFO_PANEL_STYLE, INFO_HTML_TEMPLATE, COLORS
from core.application.services.metadata_service import MetadataService
from core.domain.entities.image import Image
from core.domain.entities.image_metadata import ImageMetadata

logger = logging.getLogger(__name__)

class InfoPanel(QWidget):
    """Panel for displaying detailed image information"""
    
    # Signals
    metadata_updated = pyqtSignal(str, dict)  # Emits (image_path, metadata)
    
    def __init__(self, metadata_service: MetadataService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.metadata_service = metadata_service
        self.current_image: Optional[str] = None
        self.current_metadata: Dict[str, Any] = {}
        
        # Setup UI
        self.setup_ui()
        
        # Connect to metadata service signals if any
        if hasattr(self.metadata_service, 'metadata_changed'):
            self.metadata_service.metadata_changed.connect(self._on_metadata_changed)

    def setup_ui(self):
        """Setup the UI components"""
        try:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            
            # Create text browser for displaying info
            self.text_display = QTextBrowser()
            self.text_display.setStyleSheet(INFO_PANEL_STYLE)
            self.text_display.setOpenExternalLinks(True)
            
            # Enable rich text and HTML rendering
            self.text_display.setAcceptRichText(True)
            self.text_display.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextBrowserInteraction |
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            
            # Set document styling
            self._setup_document_style()
            
            layout.addWidget(self.text_display)
            
        except Exception as e:
            logger.error(f"Error setting up InfoPanel UI: {e}")

    def _setup_document_style(self):
        """Setup document styling"""
        document = self.text_display.document()
        document.setDefaultStyleSheet(f"""
            body {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
                font-family: 'Segoe UI', Arial, sans-serif;
                margin: 0;
                padding: 10px;
            }}
            .container {{
                max-width: 100%;
            }}
            .section {{
                background-color: {COLORS['background_alt']};
                border-radius: 5px;
                padding: 10px;
                margin-bottom: 15px;
            }}
            h2 {{
                color: {COLORS['primary']};
                font-size: 16px;
                margin: 0 0 10px 0;
            }}
            .info-grid {{
                display: grid;
                grid-template-columns: auto 1fr;
                gap: 5px 10px;
            }}
            .info-label {{
                color: {COLORS['secondary']};
                font-weight: bold;
            }}
            .info-value {{
                color: {COLORS['text']};
            }}
            .rating-value {{
                color: #FFD700;
                font-weight: bold;
                font-size: 1.1em;
            }}
            .size-value {{
                color: #4CAF50;
                font-weight: bold;
            }}
            .dimensions-value {{
                color: #2196F3;
                font-weight: bold;
            }}
            .format-value {{
                color: #9C27B0;
                font-weight: bold;
            }}
            .path-value {{
                color: #607D8B;
                font-family: 'Consolas', monospace;
            }}
            .date-value {{
                color: #FF9800;
                font-weight: bold;
            }}
            .metadata-value {{
                color: #00BCD4;
                font-weight: bold;
            }}
            pre {{
                background-color: {COLORS['background']};
                padding: 5px;
                border-radius: 3px;
                margin: 0;
                white-space: pre-wrap;
                font-family: 'Consolas', monospace;
            }}
            .json-key {{
                color: #9E9E9E;  /* Grey for keys */
                font-family: 'Consolas', monospace;
            }}
            .json-heading {{
                color: {COLORS['primary']};
                font-size: 1.1em;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
                margin-top: 10px;
                margin-bottom: 5px;
            }}
            .json-value {{
                color: #64B5F6;  /* Light blue for general values */
                font-weight: bold;
                font-family: 'Consolas', monospace;
            }}
            .json-string {{
                color: #81C784;  /* Green for strings */
                font-weight: bold;
                font-family: 'Consolas', monospace;
            }}
            .json-number {{
                color: #FF8A65;  /* Orange for numbers */
                font-weight: bold;
                font-family: 'Consolas', monospace;
            }}
            .json-bool {{
                color: #BA68C8;  /* Purple for booleans */
                font-weight: bold;
                font-family: 'Consolas', monospace;
            }}
            .json-null {{
                color: #E57373;  /* Red for null values */
                font-weight: bold;
                font-family: 'Consolas', monospace;
            }}
        """)

    def _format_json_object(self, obj, indent=0) -> str:
        """Format a JSON object (dict or list) with appropriate styling"""
        if isinstance(obj, dict):
            if not obj:
                return ""
            lines = []
            for key, value in obj.items():
                key_str = f"<span class='json-key'>{key}</span>: "
                value_str = self._format_json_value(value)
                lines.append(f"  {key_str}{value_str}")
            return "\n".join(lines)
        elif isinstance(obj, list):
            if not obj:
                return ""
            lines = []
            for item in obj:
                value_str = self._format_json_value(item)
                lines.append(f"  {value_str}")
            return "\n".join(lines)
        return str(obj)

    def _format_json_value(self, value) -> str:
        """Format a JSON value with appropriate styling"""
        if value is None:
            return f"<span class='json-null'>null</span>"
        elif isinstance(value, bool):
            return f"<span class='json-bool'>{str(value).lower()}</span>"
        elif isinstance(value, (int, float)):
            return f"<span class='json-number'>{value}</span>"
        elif isinstance(value, str):
            return f"<span class='json-string'>'{value}'</span>"
        elif isinstance(value, (list, dict)):
            return self._format_json_object(value)
        return f"<span class='json-value'>{value}</span>"

    def show_image_info(self, image_path: str):
        """Display information for the given image"""
        try:
            if not image_path or not Path(image_path).exists():
                self.clear()
                return

            path = Path(image_path)
            stats = path.stat()
            
            # Get basic image info using Qt
            reader = QImageReader(str(path))
            size = reader.size()
            format_name = reader.format().data().decode()
            
            # Create initial metadata
            initial_metadata = ImageMetadata(
                width=size.width(),
                height=size.height(),
                format=format_name,
                size_bytes=stats.st_size,
                created_at=datetime.fromtimestamp(stats.st_ctime),
                modified_at=datetime.fromtimestamp(stats.st_mtime)
            )
            
            # Create Image entity
            image = Image(
                path=str(path),
                name=path.name,
                metadata=initial_metadata
            )
            
            # Get full metadata from service
            self.current_image = image_path
            self.current_metadata = self.metadata_service.get_metadata(image)
            
            # Build HTML content
            content = []
            
            # File info section (moved to top)
            self._add_file_info_section(content, path, stats)
            
            # Metadata section (moved second)
            self._add_metadata_section(content)
            
            # Basic info section (moved to bottom)
            self._add_basic_info_section(content, path, stats, size, format_name)
            
            # Set content
            self.text_display.setHtml(INFO_HTML_TEMPLATE + "\n".join(content))
            
            # Emit update
            self.metadata_updated.emit(image_path, self.current_metadata)
            
        except Exception as e:
            logger.error(f"Error showing image info: {e}", exc_info=True)
            self.clear()

    def _add_basic_info_section(self, content: list, path: Path, stats, size, format_name):
        """Add basic information section"""
        content.append("<div class='section'>")
        content.append("<h2>Info ℹ️</h2>")
        content.append("<div class='info-grid'>")
        content.append(f"<div class='info-label'>Name:</div><div class='info-value'>{path.name}</div>")
        content.append(f"<div class='info-label'>Size:</div><div class='size-value'>{stats.st_size / (1024 * 1024):.1f} MB</div>")
        content.append(f"<div class='info-label'>Dimensions:</div><div class='dimensions-value'>{size.width()}x{size.height()}</div>")
        content.append("</div></div>")

    def _add_file_info_section(self, content: list, path: Path, stats):
        """Add file information section"""
        content.append("<div class='section'>")
        content.append("<h2>File 📄</h2>")
        content.append("<div class='info-grid'>")
        content.append(f"<div class='info-label'>Path:</div><div class='path-value'>{str(path)}</div>")
        content.append(f"<div class='info-label'>Created:</div><div class='date-value'>{datetime.fromtimestamp(stats.st_ctime)}</div>")
        content.append(f"<div class='info-label'>Modified:</div><div class='date-value'>{datetime.fromtimestamp(stats.st_mtime)}</div>")
        content.append("</div></div>")

    def _add_metadata_section(self, content: list):
        """Add metadata section if available"""
        if self.current_metadata:
            content.append("<div class='section'>")
            content.append("<h2>Metadata 🏷️</h2>")
            content.append("<div class='info-grid'>")
            
            # Skip these redundant or unimportant fields
            skip_fields = {'width', 'height', 'mode'}
            
            # Add rating first if available
            if 'rating' in self.current_metadata:
                content.append("<div class='info-label'>Rating:</div>")
                content.append(f"<div class='rating-value'>{self.current_metadata['rating']} ★</div>")
            
            # Add all other metadata fields
            for key, value in self.current_metadata.items():
                if key != 'rating' and value and key not in skip_fields:  # Skip empty values, rating, and redundant fields
                    if key in ['model', 'loras']:  # Special handling for model and loras
                        content.append(f"<div class='info-label'></div>")  # Empty label cell for alignment
                        content.append(f"<div class='metadata-value'><div class='json-heading'>{key}:</div><pre>{self._format_json_object(value)}</pre></div>")
                    elif isinstance(value, (dict, list)):  # Format other complex objects
                        content.append(f"<div class='info-label'>{key}:</div>")
                        content.append(f"<div class='metadata-value'><pre>{self._format_json_object(value)}</pre></div>")
                    else:
                        content.append(f"<div class='info-label'>{key}:</div>")
                        content.append(f"<div class='metadata-value'>{value}</div>")
                        
            content.append("</div></div>")

    def update_rating(self, image_path: str, rating: int) -> None:
        """Update rating in display"""
        try:
            if image_path != self.current_image:
                return
                
            # Update metadata
            if self.current_metadata:
                self.current_metadata['rating'] = rating
                
            # Update display if needed
            self.show_image_info(image_path)
            
            # Emit update signal
            self.metadata_updated.emit(image_path, self.current_metadata)
            
        except Exception as e:
            logger.error(f"Error updating rating display: {e}")

    def _on_metadata_changed(self, image_path: str, metadata: dict):
        """Handle metadata changes from service"""
        if image_path == self.current_image:
            self.current_metadata = metadata
            self.show_image_info(image_path)
            self.metadata_updated.emit(image_path, metadata)

    def clear(self):
        """Clear the display"""
        self.text_display.setHtml("")
        self.current_image = None
        self.current_metadata = {}

    def get_current_metadata(self) -> Dict[str, Any]:
        """Get current metadata"""
        return self.current_metadata.copy()

    def get_current_image(self) -> Optional[str]:
        """Get current image path"""
        return self.current_image

# EXIF tag mapping
EXIF_TAGS = {
    0x010F: "Camera Manufacturer",
    0x0110: "Camera Model",
    0x0112: "Orientation",
    0x8769: "Exif IFD",
    0x8825: "GPS IFD",
    0x0132: "Date/Time",
    0x829A: "Exposure Time",
    0x829D: "F-Number",
    0x8827: "ISO Speed",
    0x9003: "Original Date/Time",
    0x9004: "Digitized Date/Time",
    0x9201: "Shutter Speed",
    0x9202: "Aperture",
    0x9204: "Exposure Bias",
    0x9207: "Metering Mode",
    0x9209: "Flash",
    0x920A: "Focal Length",
    0xA401: "Custom Rendered",
    0xA402: "Exposure Mode",
    0xA403: "White Balance",
    0xA406: "Scene Type",
}

__all__ = ['InfoPanel']
