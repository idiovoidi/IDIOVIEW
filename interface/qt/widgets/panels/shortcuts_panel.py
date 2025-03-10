"""Panel for managing keyboard shortcuts"""

import logging
from typing import Optional, Dict

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QLabel,
    QScrollArea, QPushButton, QHBoxLayout,
    QMainWindow, QLineEdit
)

from core.infrastructure.config.shortcuts import (
    GalleryShortcuts,
    ShortcutConfig
)

logger = logging.getLogger(__name__)

class ShortcutLabel(QWidget):
    """Custom widget for displaying and editing a shortcut"""
    shortcutChanged = pyqtSignal(str, str)  # action, new_shortcut
    
    def __init__(self, description: str, action: str, current_shortcut: str, parent=None):
        super().__init__(parent)
        self.action = action
        self.description = description
        self.current_shortcut = current_shortcut
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the widget UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        
        # Description label
        self.desc_label = QLabel(self.description)
        self.desc_label.setStyleSheet("color: white;")
        layout.addWidget(self.desc_label)
        
        layout.addStretch()
        
        # Shortcut button
        self.shortcut_btn = QPushButton(self.current_shortcut)
        self.shortcut_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 3px 10px;
                color: #2997ff;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border-color: #4d4d4d;
            }
        """)
        self.shortcut_btn.clicked.connect(self.start_editing)
        layout.addWidget(self.shortcut_btn)
        
    def start_editing(self):
        """Start editing the shortcut"""
        self.shortcut_edit = QLineEdit(self)
        self.shortcut_edit.setPlaceholderText("Type new shortcut...")
        self.shortcut_edit.setText(self.current_shortcut)
        self.shortcut_edit.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                border: 1px solid #4d4d4d;
                border-radius: 3px;
                padding: 3px 10px;
                color: #2997ff;
            }
        """)
        
        # Replace button with edit
        self.layout().replaceWidget(self.shortcut_btn, self.shortcut_edit)
        self.shortcut_btn.hide()
        self.shortcut_edit.setFocus()
        
        # Handle key press
        self.shortcut_edit.keyPressEvent = self.handle_key_press
        
    def handle_key_press(self, event):
        """Handle key press in the shortcut editor"""
        key_sequence = QKeySequence(event.keyCombination()).toString()
        if key_sequence:
            self.current_shortcut = key_sequence
            self.shortcut_btn.setText(key_sequence)
            self.shortcutChanged.emit(self.action, key_sequence)
            
            # Restore button
            self.layout().replaceWidget(self.shortcut_edit, self.shortcut_btn)
            self.shortcut_edit.deleteLater()
            self.shortcut_btn.show()

class ShortcutsPanel(QWidget):
    """Panel for viewing and customizing keyboard shortcuts"""
    
    def __init__(self, shortcut_manager: GalleryShortcuts, parent: Optional[QMainWindow] = None):
        super().__init__(parent)
        self.shortcut_manager = shortcut_manager
        self.config = shortcut_manager.config  # Store direct reference to config
        self.shortcut_widgets: Dict[str, ShortcutLabel] = {}
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the panel UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Style
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: white;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #0078d4;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
                color: white;
            }
            QPushButton:hover {
                background-color: #2997ff;
            }
            QScrollArea {
                border: none;
                background-color: #1e1e1e;
            }
            QWidget#content {
                background-color: #1e1e1e;
            }
        """)
        
        # Header
        header = QLabel("Keyboard Shortcuts")
        header.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            padding: 10px;
            background-color: #252525;
            border-bottom: 1px solid #333;
        """)
        layout.addWidget(header)
        
        # Instructions
        instructions = QLabel("Click any shortcut to customize it")
        instructions.setStyleSheet("color: #888; font-style: italic; padding: 5px 10px;")
        layout.addWidget(instructions)
        
        # Create scroll area
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create content widget
        content = QWidget()
        content.setObjectName("content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # Add shortcut sections based on ShortcutConfig.DEFAULT_SHORTCUTS
        self.add_shortcut_section(content_layout, "Navigation", [
            ("Previous Image", "previous_image"),
            ("Next Image", "next_image"),
            ("Move Up", "move_up"),
            ("Move Down", "move_down")
        ])
        
        self.add_shortcut_section(content_layout, "View Modes", [
            ("Toggle Fullscreen", "toggle_fullscreen"),
            ("Exit Fullscreen", "exit_fullscreen")
        ])
        
        self.add_shortcut_section(content_layout, "Image Operations", [
            ("Rotate Image", "rotate_image"),
            ("Mirror Image", "mirror_image"),
            ("Toggle Fit", "toggle_fit"),
            ("Delete Image", "delete_image")
        ])
        
        self.add_shortcut_section(content_layout, "Ratings", [
            (f"Rate {i} Stars", f"rate_{i}") for i in range(6)
        ])
        
        self.add_shortcut_section(content_layout, "File Operations", [
            ("Open Folder", "open_folder"),
            ("Save Changes", "save_changes")
        ])
        
        # Add content to scroll area
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(10, 10, 10, 10)
        
        # Add reset button
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_shortcuts)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
    def add_shortcut_section(self, layout: QVBoxLayout, title: str, shortcuts: list[tuple[str, str]]):
        """Add a section of shortcuts to the layout"""
        try:
            # Add section title
            title_label = QLabel(f"<h3>{title}</h3>")
            layout.addWidget(title_label)
            
            # Add shortcuts
            for description, action in shortcuts:
                if action in self.config.DEFAULT_SHORTCUTS:  # Use direct config reference
                    shortcut = self.config.get_shortcut(action)
                    shortcut_widget = ShortcutLabel(description, action, shortcut, self)
                    shortcut_widget.shortcutChanged.connect(self.on_shortcut_changed)
                    self.shortcut_widgets[action] = shortcut_widget
                    layout.addWidget(shortcut_widget)
                else:
                    logger.warning(f"Shortcut action '{action}' not found in DEFAULT_SHORTCUTS")
                
            # Add spacing
            layout.addSpacing(10)
        except Exception as e:
            logger.error(f"Error adding shortcut section: {e}")
            
    def on_shortcut_changed(self, action: str, new_shortcut: str):
        """Handle shortcut changes"""
        try:
            if action in self.config.DEFAULT_SHORTCUTS:  # Use direct config reference
                self.config.set_shortcut(action, new_shortcut)
                self.shortcut_manager.setup_main_shortcuts()
            else:
                logger.error(f"Cannot update unknown shortcut action: {action}")
        except Exception as e:
            logger.error(f"Error updating shortcut: {e}")
            # Restore previous shortcut
            old_shortcut = self.config.get_shortcut(action)
            if action in self.shortcut_widgets:
                self.shortcut_widgets[action].shortcut_btn.setText(old_shortcut)
    
    def reset_shortcuts(self):
        """Reset all shortcuts to defaults"""
        try:
            self.config.reset_to_default()  # Use direct config reference
            self.shortcut_manager.setup_main_shortcuts()
            
            # Update all shortcut widgets
            for action, widget in self.shortcut_widgets.items():
                if action in self.config.DEFAULT_SHORTCUTS:  # Use direct config reference
                    shortcut = self.config.get_shortcut(action)
                    widget.current_shortcut = shortcut
                    widget.shortcut_btn.setText(shortcut)
        except Exception as e:
            logger.error(f"Error resetting shortcuts: {e}") 