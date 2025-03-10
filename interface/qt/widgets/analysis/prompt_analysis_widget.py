"""Prompt analysis widget for analyzing image prompts"""

import logging
from collections import defaultdict, Counter
import re
import json
from typing import Optional, Dict, List

from PIL import Image as PILImage

# Qt imports
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
    QLabel, QPushButton, QMenu, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, QStackedWidget, QGroupBox, QComboBox
)
from interface.qt.shared.styles import (
    PROMPT_COLORS,
    METADATA_PANEL_STYLE
)

# Core imports
from core.domain.entities.image import Image
from core.application.services.metadata_service import MetadataService

logger = logging.getLogger(__name__)

class PromptAnalysisWidget(QWidget):
    """Widget for analyzing image prompts and patterns"""
    
    def __init__(self, metadata_service: MetadataService, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.metadata_service = metadata_service
        self.logger = logging.getLogger("GalleryViewer.PromptAnalysisWidget")
        self.prompt_cache = {}
        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Analysis Controls
        controls = QHBoxLayout()
        
        # Analysis type selector
        self.analysis_type = QComboBox()
        self.analysis_type.addItems([
            "Common Terms",
            "Term Correlations",
            "Prompt Length Analysis",
            "Style Analysis",
            "Artist References",
            "Quality Terms",
            "Unique Terms"
        ])
        controls.addWidget(QLabel("Analysis:"))
        controls.addWidget(self.analysis_type)
        
        # Refresh button
        refresh_btn = QPushButton("Analyze Prompts")
        refresh_btn.clicked.connect(self.analyze_prompts)
        controls.addWidget(refresh_btn)
        
        layout.addLayout(controls)

        # Create stacked widget for different analysis views
        self.analysis_stack = QStackedWidget()
        
        # Common terms view
        self.common_terms_view = QTreeWidget()
        self.common_terms_view.setHeaderLabels(["Term", "Count", "% of Prompts"])
        self.analysis_stack.addWidget(self.common_terms_view)
        
        # Correlations view
        self.correlations_view = QTreeWidget()
        self.correlations_view.setHeaderLabels(["Term Pair", "Correlation", "Count"])
        self.analysis_stack.addWidget(self.correlations_view)
        
        # Length analysis view
        self.length_view = QTreeWidget()
        self.length_view.setHeaderLabels(["Length Range", "Count", "Examples"])
        self.analysis_stack.addWidget(self.length_view)
        
        # Style analysis view
        self.style_view = QTreeWidget()
        self.style_view.setHeaderLabels(["Style", "Count", "Example Prompts"])
        self.analysis_stack.addWidget(self.style_view)
        
        layout.addWidget(self.analysis_stack)

        # Statistics panel
        stats_group = QGroupBox("Prompt Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_labels = {
            'total': QLabel("Total Prompts: 0"),
            'avg_length': QLabel("Average Length: 0 words"),
            'unique_terms': QLabel("Unique Terms: 0"),
            'common_artists': QLabel("Most Referenced Artists: None"),
            'common_styles': QLabel("Common Styles: None")
        }
        
        for label in self.stats_labels.values():
            stats_layout.addWidget(label)
            
        layout.addWidget(stats_group)

        # Status bar
        self.status_label = QLabel()
        layout.addWidget(self.status_label)

        # Connect signals
        self.analysis_type.currentTextChanged.connect(self.switch_analysis_view)

        # Apply styling
        self.apply_style()

    def apply_style(self):
        """Apply widget styling"""
        self.setStyleSheet("""
            QGroupBox {
                background-color: #2d2d2d;
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 1em;
                padding: 10px;
            }
            QTreeWidget {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #555555;
            }
            QLabel {
                color: #cccccc;
            }
            QComboBox {
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
                padding: 5px 15px;
                color: white;
            }
            QPushButton:hover {
                background-color: #2997ff;
            }
        """)

    def analyze_prompts(self, images: Optional[List[Image]] = None):
        """Analyze prompts from provided images or all loaded images"""
        try:
            self.status_label.setText("Analyzing prompts...")
            QApplication.processEvents()
            
            self.prompt_cache.clear()
            
            # If no images provided, collect from parent
            if images is None and hasattr(self.parent, 'image_grid'):
                images = self.parent.image_grid.all_images
                
            if not images:
                self.status_label.setText("No images available")
                return
                
            # Collect prompts
            prompts = []
            for image in images:
                try:
                    metadata = self.metadata_service.get_metadata(image)
                    if prompt := metadata.get('prompt', ''):
                        prompts.append(prompt)
                        self.prompt_cache[image.path] = prompt
                except Exception as e:
                    self.logger.debug(f"Error reading prompt: {e}")
                    continue

            if prompts:
                # Perform analyses based on current view
                current_view = self.analysis_type.currentText()
                if current_view == "Common Terms":
                    self.analyze_common_terms(prompts)
                elif current_view == "Term Correlations":
                    self.analyze_correlations(prompts)
                elif current_view == "Prompt Length Analysis":
                    self.analyze_lengths(prompts)
                elif current_view == "Style Analysis":
                    self.analyze_styles(prompts)
                
                self.update_statistics(prompts)
                self.status_label.setText(f"Analyzed {len(prompts)} prompts")
            else:
                self.status_label.setText("No prompts found")
                
        except Exception as e:
            self.logger.error(f"Error analyzing prompts: {e}")
            self.status_label.setText("Error analyzing prompts")

    def analyze_common_terms(self, prompts: List[str]):
        """Analyze most common terms in prompts"""
        try:
            # Split prompts into terms
            all_terms = []
            for prompt in prompts:
                terms = prompt.lower().replace(',', ' ').split()
                all_terms.extend(terms)
            
            # Count terms
            term_counts = Counter(all_terms)
            
            # Update tree view
            self.common_terms_view.clear()
            total_prompts = len(prompts)
            
            for term, count in term_counts.most_common(50):
                percentage = (count / total_prompts) * 100
                item = QTreeWidgetItem([
                    term,
                    str(count),
                    f"{percentage:.1f}%"
                ])
                self.common_terms_view.addTopLevelItem(item)
                
        except Exception as e:
            self.logger.error(f"Error analyzing common terms: {e}")

    def analyze_correlations(self, prompts: List[str]):
        """Analyze term correlations"""
        try:
            # Split prompts into term sets
            prompt_terms = [set(p.lower().replace(',', ' ').split()) for p in prompts]
            
            # Find term pairs that appear together
            correlations = defaultdict(int)
            for terms in prompt_terms:
                for term1 in terms:
                    for term2 in terms:
                        if term1 < term2:  # Avoid counting pairs twice
                            correlations[(term1, term2)] += 1
            
            # Update tree view
            self.correlations_view.clear()
            total_prompts = len(prompts)
            
            for (term1, term2), count in sorted(correlations.items(), 
                                              key=lambda x: x[1], reverse=True)[:50]:
                correlation = (count / total_prompts) * 100
                item = QTreeWidgetItem([
                    f"{term1} + {term2}",
                    f"{correlation:.1f}%",
                    str(count)
                ])
                self.correlations_view.addTopLevelItem(item)
                
        except Exception as e:
            self.logger.error(f"Error analyzing correlations: {e}")

    def analyze_lengths(self, prompts: List[str]):
        """Analyze prompt lengths"""
        try:
            # Calculate lengths
            lengths = [(len(p.split()), p) for p in prompts]
            length_ranges = [(0, 10), (11, 20), (21, 30), (31, 50), (51, float('inf'))]
            
            # Group by range
            range_groups = defaultdict(list)
            for length, prompt in lengths:
                for start, end in length_ranges:
                    if start <= length <= end:
                        range_groups[f"{start}-{end if end != float('inf') else '∞'}"].append(prompt)
                        break
            
            # Update tree view
            self.length_view.clear()
            
            for range_str, prompts in sorted(range_groups.items()):
                item = QTreeWidgetItem([
                    range_str,
                    str(len(prompts)),
                    prompts[0][:100] + "..." if prompts else ""
                ])
                self.length_view.addTopLevelItem(item)
                
        except Exception as e:
            self.logger.error(f"Error analyzing lengths: {e}")

    def analyze_styles(self, prompts: List[str]):
        """Analyze artistic styles in prompts"""
        try:
            # Common style keywords
            style_keywords = {
                'anime': ['anime', 'manga', 'japanese'],
                'realistic': ['realistic', 'photorealistic', 'photograph'],
                'artistic': ['painting', 'artwork', 'illustration'],
                'digital': ['digital', 'cgi', '3d'],
                '2d': ['2d', 'cartoon', 'drawn']
            }
            
            # Count style occurrences
            style_counts = defaultdict(int)
            style_examples = defaultdict(list)
            
            for prompt in prompts:
                prompt_lower = prompt.lower()
                for style, keywords in style_keywords.items():
                    if any(k in prompt_lower for k in keywords):
                        style_counts[style] += 1
                        if len(style_examples[style]) < 3:  # Keep up to 3 examples
                            style_examples[style].append(prompt[:100] + '...')
            
            # Update tree view
            self.style_view.clear()
            for style, count in sorted(style_counts.items(), key=lambda x: x[1], reverse=True):
                item = QTreeWidgetItem([
                    style,
                    str(count),
                    '\n'.join(style_examples[style])
                ])
                self.style_view.addTopLevelItem(item)
                
        except Exception as e:
            self.logger.error(f"Error analyzing styles: {e}")

    def update_statistics(self, prompts: List[str]):
        """Update overall statistics"""
        try:
            # Calculate basic stats
            total = len(prompts)
            avg_length = sum(len(p.split()) for p in prompts) / total if total > 0 else 0
            unique_terms = len(set(term for p in prompts for term in p.lower().split()))
            
            # Update labels
            self.stats_labels['total'].setText(f"Total Prompts: {total}")
            self.stats_labels['avg_length'].setText(f"Average Length: {avg_length:.1f} words")
            self.stats_labels['unique_terms'].setText(f"Unique Terms: {unique_terms}")
            
            # Find most common artists
            artist_pattern = r"by ([a-zA-Z\s]+)"
            artists = []
            for prompt in prompts:
                artists.extend(re.findall(artist_pattern, prompt))
            
            if artists:
                artist_counts = Counter(artists)
                top_artists = ', '.join(a for a, _ in artist_counts.most_common(3))
                self.stats_labels['common_artists'].setText(f"Most Referenced Artists: {top_artists}")
            
        except Exception as e:
            self.logger.error(f"Error updating statistics: {e}")

    def switch_analysis_view(self, view_type: str):
        """Switch between different analysis views"""
        view_index = self.analysis_type.findText(view_type)
        if view_index >= 0:
            self.analysis_stack.setCurrentIndex(view_index)

    def clear(self):
        """Clear all analysis displays"""
        try:
            self.common_terms_view.clear()
            self.correlations_view.clear()
            self.style_view.clear()
            self.length_view.clear()
            
            # Reset statistics
            for label in self.stats_labels.values():
                label.setText("")
                
            self.status_label.setText("")
            
        except Exception as e:
            self.logger.error(f"Error clearing prompt analysis: {e}")

    def update_display(self, image: Optional[Image]):
        """Update display with image's prompt information"""
        try:
            if not image:
                self.clear()
                return
                
            # Get prompt from metadata service
            metadata = self.metadata_service.get_metadata(image)
            prompt = metadata.get('prompt', '')
            
            if prompt:
                self.analyze_prompts([image])
            else:
                self.status_label.setText("No prompt found in image metadata")
                
        except Exception as e:
            self.logger.error(f"Error updating prompt display: {e}")
            self.status_label.setText("Error reading prompt data")