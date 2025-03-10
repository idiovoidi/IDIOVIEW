"""Keyboard shortcuts configuration"""

from typing import Optional, Dict, Callable, Any
import json
from pathlib import Path
import logging
from PyQt6.QtGui import QShortcut, QKeyEvent
from PyQt6.QtWidgets import QApplication


from interface.qt.shared.imports import (
    # Core imports
    Qt, QKeySequence,
    
    # Widget imports
    QDialog, QLabel, QHBoxLayout, QVBoxLayout, 
    QPushButton, QGroupBox, QLineEdit
)

from interface.qt.views.browser.fullscreen_view import FullScreenViewer
from core.infrastructure.persistence.local_image_repository import LocalImageRepository

logger = logging.getLogger(__name__)

class ShortcutConfig:
    """Manages shortcut configuration and persistence"""
    
    DEFAULT_SHORTCUTS = {
        # Grid Navigation
        "grid_left": "Left",
        "grid_right": "Right",
        "grid_up": "Up",
        "grid_down": "Down",
        "grid_first": "Home",
        "grid_last": "End",
        "grid_page_up": "PgUp",
        "grid_page_down": "PgDown",
        
        # Selection
        "select": "Space",
        "select_all": "Ctrl+A",
        "deselect_all": "Ctrl+D",
        "extend_selection": "Shift",  # Modifier key
        
        # View modes
        "toggle_fullscreen": "Return",
        "exit_fullscreen": "Escape",
        
        # Image operations
        "rotate_image": "R",
        "mirror_image": "M",
        "toggle_fit": "F",
        "delete_image": "Delete",
        
        # Ratings (0-5)
        "rate_0": "0",
        "rate_1": "1",
        "rate_2": "2",
        "rate_3": "3",
        "rate_4": "4",
        "rate_5": "5",
        
        # File operations
        "open_folder": "Ctrl+O",
        "save_changes": "Ctrl+S",
    }
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.config_file = config_dir / "shortcuts.json"
        self.shortcuts = self.DEFAULT_SHORTCUTS.copy()
        logger.debug(f"Initializing ShortcutConfig with config_dir: {config_dir}")
        logger.debug(f"Default shortcuts: {self.shortcuts}")
        self.load_config()
        
    def load_config(self) -> None:
        """Load custom shortcuts from config file"""
        try:
            if self.config_file.exists():
                logger.debug(f"Loading shortcuts from {self.config_file}")
                with open(self.config_file, 'r') as f:
                    custom_shortcuts = json.load(f)
                    logger.debug(f"Loaded custom shortcuts: {custom_shortcuts}")
                    self.shortcuts.update(custom_shortcuts)
            else:
                logger.debug(f"No custom shortcuts file found at {self.config_file}, using defaults")
                # Ensure the config directory exists
                self.config_dir.mkdir(parents=True, exist_ok=True)
                # Save the default shortcuts
                self.save_config()
        except Exception as e:
            logger.error(f"Error loading shortcut config: {e}")
            
    def save_config(self) -> None:
        """Save current shortcuts to config file"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Saving shortcuts to {self.config_file}: {self.shortcuts}")
            with open(self.config_file, 'w') as f:
                json.dump(self.shortcuts, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving shortcut config: {e}")
            
    def get_shortcut(self, action: str) -> str:
        """Get shortcut sequence for action"""
        shortcut = self.shortcuts.get(action, self.DEFAULT_SHORTCUTS.get(action, ""))
        logger.debug(f"Getting shortcut for action '{action}': {shortcut}")
        return shortcut
        
    def set_shortcut(self, action: str, sequence: str) -> None:
        """Set custom shortcut for action"""
        if action in self.DEFAULT_SHORTCUTS:
            logger.debug(f"Setting shortcut for action '{action}' to '{sequence}'")
            self.shortcuts[action] = sequence
            self.save_config()
        else:
            logger.warning(f"Attempted to set shortcut for unknown action: {action}")
            
    def reset_to_default(self, action: Optional[str] = None) -> None:
        """Reset shortcuts to default"""
        if action:
            if action in self.DEFAULT_SHORTCUTS:
                logger.debug(f"Resetting shortcut for action '{action}' to default")
                self.shortcuts[action] = self.DEFAULT_SHORTCUTS[action]
        else:
            logger.debug("Resetting all shortcuts to defaults")
            self.shortcuts = self.DEFAULT_SHORTCUTS.copy()
        self.save_config()

class GalleryShortcuts:
    """Manages keyboard shortcuts for the gallery application"""
    
    def __init__(self, main_window, image_repository: LocalImageRepository):
        """Initialize shortcuts for the main window"""
        self.main_window = main_window
        self.image_repository = image_repository
        logger.debug("Initializing GalleryShortcuts")
        self.config = ShortcutConfig(Path("user_data/config"))
        self.shortcuts: Dict[str, QShortcut] = {}
        self.fullscreen_viewer = None  # Track current fullscreen viewer
        self.setup_main_shortcuts()
        
    def setup_main_shortcuts(self):
        """Setup shortcuts for the main window"""
        try:
            logger.debug("Setting up main shortcuts")
            
            # Grid navigation shortcuts
            self._add_shortcut("grid_left", lambda: self._handle_grid_navigation("left"))
            self._add_shortcut("grid_right", lambda: self._handle_grid_navigation("right"))
            self._add_shortcut("grid_up", lambda: self._handle_grid_navigation("up"))
            self._add_shortcut("grid_down", lambda: self._handle_grid_navigation("down"))
            self._add_shortcut("grid_first", lambda: self._handle_grid_navigation("first"))
            self._add_shortcut("grid_last", lambda: self._handle_grid_navigation("last"))
            self._add_shortcut("grid_page_up", lambda: self._handle_grid_navigation("page_up"))
            self._add_shortcut("grid_page_down", lambda: self._handle_grid_navigation("page_down"))
            
            # Selection shortcuts
            self._add_shortcut("select_all", self._handle_select_all)
            self._add_shortcut("deselect_all", self._handle_deselect_all)
            
            # View mode shortcuts
            self._add_shortcut("toggle_fullscreen", self.toggle_fullscreen)
            self._add_shortcut("exit_fullscreen", self.exit_fullscreen)
            
            # Image operations
            self._add_shortcut("delete_image", self.delete_selected)
            self._add_shortcut("open_folder", self.open_folder)
            
            # Rating shortcuts
            for i in range(6):
                self._add_shortcut(f"rate_{i}", lambda x=i: self.set_rating(x))
                
            logger.debug(f"Shortcuts setup complete. Active shortcuts: {list(self.shortcuts.keys())}")
        except Exception as e:
            logger.error(f"Error setting up shortcuts: {e}")

    def _handle_grid_navigation(self, direction: str) -> None:
        """Handle grid navigation shortcuts"""
        try:
            if not hasattr(self.main_window, 'grid_view'):
                return
                
            grid_view = self.main_window.grid_view
            shift_held = bool(QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier)
            
            if direction == "left":
                grid_view.navigate(-1, 0, extend_selection=shift_held)
            elif direction == "right":
                grid_view.navigate(1, 0, extend_selection=shift_held)
            elif direction == "up":
                grid_view.navigate(0, -1, extend_selection=shift_held)
            elif direction == "down":
                grid_view.navigate(0, 1, extend_selection=shift_held)
            elif direction == "first":
                grid_view.navigate_to_position("first", extend_selection=shift_held)
            elif direction == "last":
                grid_view.navigate_to_position("last", extend_selection=shift_held)
            elif direction == "page_up":
                grid_view.navigate_to_position("page_up", extend_selection=shift_held)
            elif direction == "page_down":
                grid_view.navigate_to_position("page_down", extend_selection=shift_held)
                
        except Exception as e:
            logger.error(f"Error handling grid navigation: {e}")

    def _handle_select_all(self) -> None:
        """Handle select all shortcut"""
        if hasattr(self.main_window, 'grid_view'):
            self.main_window.grid_view.select_all()

    def _handle_deselect_all(self) -> None:
        """Handle deselect all shortcut"""
        if hasattr(self.main_window, 'grid_view'):
            self.main_window.grid_view.deselect_all()

    def _add_shortcut(self, action: str, callback: Callable) -> None:
        """Add a shortcut with the specified action and callback"""
        sequence = self.config.get_shortcut(action)
        logger.debug(f"Adding shortcut for action '{action}' with sequence '{sequence}'")
        if sequence:
            shortcut = QShortcut(QKeySequence(sequence), self.main_window)
            shortcut.activated.connect(callback)
            self.shortcuts[action] = shortcut
            logger.debug(f"Shortcut added successfully for {action}")
        else:
            logger.warning(f"No sequence found for action: {action}")
            
    def update_shortcut(self, action: str, sequence: str) -> None:
        """Update an existing shortcut"""
        try:
            if action in self.shortcuts:
                logger.debug(f"Updating shortcut for action '{action}' to '{sequence}'")
                self.config.set_shortcut(action, sequence)
                self.shortcuts[action].setKey(QKeySequence(sequence))
            else:
                logger.warning(f"Attempted to update non-existent shortcut: {action}")
        except Exception as e:
            logger.error(f"Error updating shortcut: {e}")

    def toggle_fullscreen(self) -> None:
        """Toggle fullscreen view"""
        try:
            logger.debug("Toggle fullscreen called")
            # If fullscreen view is active, close it
            if self.fullscreen_viewer and self.fullscreen_viewer.isVisible():
                logger.debug("Closing fullscreen view")
                # Store current image hash before closing
                current_hash = self.fullscreen_viewer.image_hashes.get(
                    self.fullscreen_viewer.image_paths[self.fullscreen_viewer.current_index]
                )
                self.fullscreen_viewer.close()
                self.fullscreen_viewer = None
                
                # Sync grid view to last fullscreen position
                if current_hash and hasattr(self.main_window, 'grid_view'):
                    self.main_window.grid_view.select_by_hash(current_hash)
                return

            # Otherwise, open fullscreen view
            if not hasattr(self.main_window, 'grid_view'):
                logger.debug("Cannot open fullscreen: no grid view available")
                return
                
            selected_images = self.main_window.grid_view.get_selected_paths()
            if not selected_images:
                logger.debug("Cannot open fullscreen: no images selected")
                return
                
            logger.debug("Opening fullscreen view")
            # Get image data from grid view
            image_data = self.main_window.grid_view.get_current_image_data()
            
            # Create and show fullscreen viewer
            self.fullscreen_viewer = FullScreenViewer(
                image_data=image_data,
                image_loader=self.main_window.image_loader,
                rating_service=self.main_window.rating_service,
                metadata_service=self.main_window.metadata_service,
                parent=self.main_window
            )
            
            # Connect signals
            self.fullscreen_viewer.image_deleted.connect(self.main_window.grid_view.remove_image)
            self.fullscreen_viewer.closed.connect(self.main_window.on_fullscreen_closed)
            self.fullscreen_viewer.image_changed.connect(
                lambda path: self.main_window.grid_view.select_by_hash(
                    self.fullscreen_viewer.image_hashes.get(path, "")
                )
            )
            
            self.fullscreen_viewer.showFullScreen()
            
        except Exception as e:
            logger.error(f"Error toggling fullscreen view: {e}")

    def delete_selected(self) -> None:
        """Delete selected image"""
        if hasattr(self.main_window, 'delete_selected'):
            self.main_window.delete_selected()

    def open_folder(self) -> None:
        """Open folder dialog"""
        if hasattr(self.main_window, 'open_folder'):
            self.main_window.open_folder()

    def set_rating(self, rating: int) -> None:
        """Set rating for selected image"""
        if hasattr(self.main_window, 'set_rating'):
            self.main_window.set_rating(rating)

    def apply_fullscreen_shortcuts(self, fullscreen_viewer: FullScreenViewer) -> None:
        """Apply shortcuts to fullscreen viewer"""
        try:
            # Toggle fullscreen (Space)
            QShortcut(QKeySequence(self.config.get_shortcut("toggle_fullscreen")), 
                     fullscreen_viewer, activated=fullscreen_viewer.close)
            
            # Exit fullscreen (Escape)
            QShortcut(QKeySequence(self.config.get_shortcut("exit_fullscreen")), 
                     fullscreen_viewer, activated=fullscreen_viewer.close)
            
            # Navigation
            QShortcut(QKeySequence(self.config.get_shortcut("next_image")), 
                     fullscreen_viewer, activated=fullscreen_viewer.next_image)
            QShortcut(QKeySequence(self.config.get_shortcut("previous_image")), 
                     fullscreen_viewer, activated=fullscreen_viewer.previous_image)
            
            # Image operations
            QShortcut(QKeySequence(self.config.get_shortcut("rotate_image")), 
                     fullscreen_viewer, activated=fullscreen_viewer.rotate_image)
            QShortcut(QKeySequence(self.config.get_shortcut("mirror_image")), 
                     fullscreen_viewer, activated=fullscreen_viewer.toggle_mirror_mode)
            QShortcut(QKeySequence(self.config.get_shortcut("toggle_fit")), 
                     fullscreen_viewer, activated=fullscreen_viewer.toggle_fit_mode)
            
            # Rating shortcuts
            for i in range(6):
                QShortcut(QKeySequence(self.config.get_shortcut(f"rate_{i}")), 
                         fullscreen_viewer, activated=lambda x=i: fullscreen_viewer.set_rating(x))
                
        except Exception as e:
            logger.error(f"Error setting up fullscreen shortcuts: {e}")

    def setup_fullscreen_wheel_event(self, fullscreen_viewer: FullScreenViewer) -> None:
        """Setup mouse wheel event for fullscreen viewer"""
        fullscreen_viewer.wheelEvent = lambda event: self.fullscreen_wheel_event(event, fullscreen_viewer)

    def fullscreen_wheel_event(self, event, fullscreen_viewer: FullScreenViewer) -> None:
        """Handle mouse wheel events in fullscreen"""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                fullscreen_viewer.zoom_in()
            else:
                fullscreen_viewer.zoom_out()
        else:
            if event.angleDelta().y() > 0:
                fullscreen_viewer.previous_image()
            else:
                fullscreen_viewer.next_image()

    def exit_fullscreen(self) -> None:
        """Exit fullscreen view"""
        try:
            logger.debug("Exit fullscreen called")
            if self.fullscreen_viewer and self.fullscreen_viewer.isVisible():
                logger.debug("Closing fullscreen view")
                # Store current image hash before closing
                current_hash = self.fullscreen_viewer.image_hashes.get(
                    self.fullscreen_viewer.image_paths[self.fullscreen_viewer.current_index]
                )
                self.fullscreen_viewer.close()
                self.fullscreen_viewer = None
                
                # Sync grid view to last fullscreen position
                if current_hash and hasattr(self.main_window, 'grid_view'):
                    self.main_window.grid_view.select_by_hash(current_hash)
        except Exception as e:
            logger.error(f"Error exiting fullscreen view: {e}")

class ShortcutsDialog(QDialog):
    """Dialog showing available keyboard shortcuts"""
    
    def __init__(self, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Style
        self.setStyleSheet("""
            QDialog {
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
        """)
        
        # Create sections
        layout.addWidget(self.create_section("General Shortcuts", [
            ("Space", "Toggle Fullscreen"),
            ("Delete", "Delete Image"),
            ("Left/Right", "Previous/Next Image"),
            ("Up/Down", "Previous/Next Image"),
            ("0-5", "Set Rating"),
            ("Ctrl+O", "Open Folder")
        ]))
        
        layout.addWidget(self.create_section("Fullscreen Shortcuts", [
            ("Space/Esc", "Exit Fullscreen"),
            ("N", "Show Tag Panel"),
            ("R", "Rotate Image"),
            ("M", "Mirror Image"),
            ("F", "Toggle Fit Mode"),
            ("Mouse Wheel", "Navigate Images"),
            ("Ctrl+Wheel", "Zoom In/Out"),
            ("Right Click", "Exit Fullscreen"),
            ("Middle Click", "Enter Fullscreen")
        ]))
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
    def create_section(self, title: str, shortcuts: list[tuple[str, str]]) -> QGroupBox:
        """Create a section of shortcuts"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                color: white;
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 1em;
                padding-top: 1em;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        for key, description in shortcuts:
            row = QHBoxLayout()
            key_label = QLabel(f"<b>{key}</b>")
            key_label.setStyleSheet("color: #2997ff;")
            row.addWidget(key_label)
            row.addWidget(QLabel(description))
            row.addStretch()
            layout.addLayout(row)
            
        return group

class ShortcutCustomizeDialog(QDialog):
    """Dialog for customizing keyboard shortcuts"""
    
    def __init__(self, shortcut_manager: GalleryShortcuts, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.shortcut_manager = shortcut_manager
        self.setWindowTitle("Customize Shortcuts")
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Style
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: white;
                min-width: 500px;
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
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #2997ff;
            }
            QPushButton:disabled {
                background-color: #555555;
            }
            QLineEdit {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
        """)
        
        # Add sections
        layout.addWidget(self.create_shortcut_section("Navigation", [
            ("previous_image", "Previous Image"),
            ("next_image", "Next Image"),
            ("move_up", "Move Up"),
            ("move_down", "Move Down")
        ]))
        
        layout.addWidget(self.create_shortcut_section("View Modes", [
            ("toggle_fullscreen", "Toggle Fullscreen"),
            ("exit_fullscreen", "Exit Fullscreen")
        ]))
        
        layout.addWidget(self.create_shortcut_section("Image Operations", [
            ("rotate_image", "Rotate Image"),
            ("mirror_image", "Mirror Image"),
            ("toggle_fit", "Toggle Fit"),
            ("delete_image", "Delete Image")
        ]))
        
        layout.addWidget(self.create_shortcut_section("Ratings", [
            (f"rate_{i}", f"Rate {i} Stars") for i in range(6)
        ]))
        
        layout.addWidget(self.create_shortcut_section("File Operations", [
            ("open_folder", "Open Folder"),
            ("save_changes", "Save Changes")
        ]))
        
        # Buttons
        button_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Reset All")
        reset_btn.clicked.connect(self.reset_all_shortcuts)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
    def create_shortcut_section(self, title: str, shortcuts: list[tuple[str, str]]) -> QGroupBox:
        """Create a section of shortcut settings"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                color: white;
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 1em;
                padding-top: 1em;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        for action, description in shortcuts:
            row = QHBoxLayout()
            
            # Description
            row.addWidget(QLabel(description))
            
            # Current shortcut
            shortcut_edit = QLineEdit(self.shortcut_manager.config.get_shortcut(action))
            shortcut_edit.setPlaceholderText("Click to set shortcut")
            shortcut_edit.setReadOnly(True)
            shortcut_edit.focusInEvent = lambda e, a=action, edit=shortcut_edit: self.start_shortcut_capture(a, edit)
            row.addWidget(shortcut_edit)
            
            # Reset button
            reset_btn = QPushButton("Reset")
            reset_btn.clicked.connect(lambda checked, a=action, edit=shortcut_edit: self.reset_shortcut(a, edit))
            row.addWidget(reset_btn)
            
            layout.addLayout(row)
            
        return group
        
    def start_shortcut_capture(self, action: str, edit: QLineEdit) -> None:
        """Start capturing a new shortcut"""
        edit.setText("Press shortcut...")
        edit.keyPressEvent = lambda e: self.capture_shortcut(e, action, edit)
        
    def capture_shortcut(self, event: QKeyEvent, action: str, edit: QLineEdit) -> None:
        """Capture and set new shortcut"""
        try:
            # Create key sequence
            sequence = QKeySequence(event.key() | int(event.modifiers()))
            sequence_str = sequence.toString()
            
            # Update shortcut
            self.shortcut_manager.update_shortcut(action, sequence_str)
            edit.setText(sequence_str)
            
            # Restore normal key press handling
            edit.keyPressEvent = edit.__class__.keyPressEvent
            edit.clearFocus()
            
        except Exception as e:
            logger.error(f"Error capturing shortcut: {e}")
            edit.setText(self.shortcut_manager.config.get_shortcut(action))
            
    def reset_shortcut(self, action: str, edit: QLineEdit) -> None:
        """Reset shortcut to default"""
        try:
            self.shortcut_manager.config.reset_to_default(action)
            self.shortcut_manager.update_shortcut(action, self.shortcut_manager.config.get_shortcut(action))
            edit.setText(self.shortcut_manager.config.get_shortcut(action))
        except Exception as e:
            logger.error(f"Error resetting shortcut: {e}")
            
    def reset_all_shortcuts(self) -> None:
        """Reset all shortcuts to defaults"""
        try:
            self.shortcut_manager.config.reset_to_default()
            self.accept()  # Close dialog
            ShortcutCustomizeDialog(self.shortcut_manager, self.parent()).exec()  # Reopen with defaults
        except Exception as e:
            logger.error(f"Error resetting all shortcuts: {e}")

__all__ = ['GalleryShortcuts', 'ShortcutsDialog']

                