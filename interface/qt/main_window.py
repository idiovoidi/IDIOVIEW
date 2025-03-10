"""Main application window"""

import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QMenu, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

from core.container.container import Container
from core.application.services.image_loader_service import ImageLoaderService
from core.application.services.rating_service import RatingService
from core.application.services.metadata_service import MetadataService
from core.domain.repositories.image_repository import ImageRepository
from core.infrastructure.config.savedfolders import SavedFoldersManager
from core.infrastructure.config.shortcuts import GalleryShortcuts

from .widgets.controls import Toolbar, RightSidebar, Statusbar
from .widgets.controls.search_bar import SearchBar
from .widgets.controls.filter_panel import FilterPanel
from .widgets.controls.tag_panel import TagPanel
from .widgets.menus import FileMenu, EditMenu, ViewMenu, ToolsMenu, HelpMenu
from .widgets.menus.folder_tree import FolderTree
from .widgets.metadata.info_panel import InfoPanel
from .widgets.metadata.metadata_search_panel import MetadataSearchPanel
from .widgets.metadata.metadata_entry_panel import MetadataEntryPanel
from .views.browser.grid_view import GridView
from .widgets.menus.saved_locations_menu import SavedLocationsMenu, SavedLocationsList

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main application window with integrated browser functionality"""
    
    # Signals
    closing = pyqtSignal()  # Emitted when window is closing
    
    def __init__(
        self,
        container: Container,
        parent: Optional[QMainWindow] = None
    ):
        super().__init__(parent)
        
        # Store dependencies from container
        self.image_loader = container.image_loader()
        self.rating_service = container.rating_service()
        self.metadata_service = container.metadata_service()
        self.image_repository = container.image_repository()
        self.saved_folders = container.saved_folders()
        self.window_state = container.window_state()
        
        # Initialize shortcut manager
        self.shortcut_manager = GalleryShortcuts(self, self.image_repository)
        
        # Store config from shortcut manager
        self.config = self.shortcut_manager.config
        
        # Initialize UI components to None
        self.toolbar = None
        self.status_bar = None
        self.folder_tree = None
        self.grid_view = None
        self.info_panel = None
        self.filter_panel = None
        self.tag_panel = None
        self.search_bar = None
        self.main_splitter = None
        self.metadata_search_panel = None
        self.metadata_entry_panel = None
        self.right_sidebar = None
        self.left_panel = None
        self.saved_locations_list = None
        
        # Initialize loading state
        self._initial_load_complete = False
        self._load_timer = QTimer(self)
        self._load_timer.setSingleShot(True)
        self._load_timer.timeout.connect(self._delayed_initial_load)
        
        # Setup UI
        try:
            self.setup_ui()
            
            # Connect signals
            self.connect_signals()
            
            # Restore window state
            self.restore_state()
            
            # Schedule delayed loading of default directory
            self._load_timer.start(100)  # 100ms delay
            
        except Exception as e:
            logger.error(f"Error setting up UI: {e}")
            raise
        
    def setup_ui(self):
        """Initialize the user interface"""
        try:
            # Set window properties
            self.setWindowTitle("ID:I/O VIEWER")
            self.setMinimumSize(1024, 768)
            
            # Create main widget and layout
            main_widget = QWidget()
            self.setCentralWidget(main_widget)
            
            main_layout = QVBoxLayout(main_widget)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)
            
            # Create panels
            self.filter_panel = FilterPanel(metadata_service=self.metadata_service)
            self.tag_panel = TagPanel(metadata_service=self.metadata_service)
            self.search_bar = SearchBar(filter_bar=self.filter_panel)
            
            # Create metadata panels
            self.metadata_search_panel = MetadataSearchPanel(
                image_repository=self.image_repository,
                metadata_service=self.metadata_service
            )
            self.metadata_entry_panel = MetadataEntryPanel(
                image_repository=self.image_repository,
                metadata_service=self.metadata_service
            )
            
            # Create toolbar first
            self.toolbar = Toolbar(self)
            # Add search bar to toolbar using QWidget
            search_widget = QWidget()
            search_layout = QHBoxLayout(search_widget)
            search_layout.setContentsMargins(5, 0, 5, 0)
            search_layout.addWidget(self.search_bar)
            self.toolbar.addWidget(search_widget)
            self.addToolBar(self.toolbar)
            
            # Create status bar
            self.status_bar = Statusbar(self)
            self.setStatusBar(self.status_bar)
            
            # Create menus (after toolbar and status bar)
            self.setup_menus()
            
            # Create main content area
            content_widget = QWidget()
            content_layout = QHBoxLayout(content_widget)
            content_layout.setContentsMargins(0, 0, 0, 0)
            content_layout.setSpacing(0)
            main_layout.addWidget(content_widget)
            
            # Create main splitter
            self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
            content_layout.addWidget(self.main_splitter)
            
            # Create left panel with vertical splitter
            self.left_panel = QWidget()
            left_layout = QVBoxLayout(self.left_panel)
            left_layout.setContentsMargins(0, 0, 0, 0)
            
            left_splitter = QSplitter()
            left_splitter.setOrientation(Qt.Orientation.Vertical)
            
            # Add folder tree to top of left splitter
            self.folder_tree = FolderTree(saved_folders=self.saved_folders)
            self.folder_tree.directory_selected.connect(self._handle_directory_selected)
            left_splitter.addWidget(self.folder_tree)
            
            # Add saved locations to bottom of left splitter
            self.saved_locations_list = SavedLocationsList(saved_folders=self.saved_folders)
            self.saved_locations_list.location_selected.connect(self._handle_directory_selected)
            left_splitter.addWidget(self.saved_locations_list)
            
            # Set initial sizes (60% folder tree, 40% saved locations)
            left_splitter.setSizes([600, 400])
            
            left_layout.addWidget(left_splitter)
            
            # Store left splitter for state management
            self.left_splitter = left_splitter
            
            self.main_splitter.addWidget(self.left_panel)
            
            # Create center panel for grid view
            center_panel = QWidget()
            center_layout = QVBoxLayout(center_panel)
            center_layout.setContentsMargins(0, 0, 0, 0)
            
            # Create grid view
            self.grid_view = GridView(
                rating_service=self.rating_service,
                image_loader_service=self.image_loader,
                parent=center_panel
            )
            center_layout.addWidget(self.grid_view)
            
            self.main_splitter.addWidget(center_panel)
            
            # Create right sidebar
            self.right_sidebar = RightSidebar()
            
            # Create info panel
            self.info_panel = InfoPanel(metadata_service=self.metadata_service)
            
            # Register all panels with right sidebar
            self.right_sidebar.register_panel("info", self.info_panel)  # Register info panel first
            self.right_sidebar.register_panel("search", self.metadata_search_panel)
            self.right_sidebar.register_panel("edit", self.metadata_entry_panel)
            self.right_sidebar.register_panel("tags", self.tag_panel)
            self.right_sidebar.register_panel("filters", self.filter_panel)
            
            # Add right sidebar to main splitter
            self.main_splitter.addWidget(self.right_sidebar)
            
            # Set initial splitter sizes (proportional)
            total_width = self.width()
            self.main_splitter.setSizes([
                int(total_width * 0.15),  # Left panel (15%)
                int(total_width * 0.55),  # Grid view (55%)
                int(total_width * 0.30),  # Right sidebar (30%)
            ])
            
        except Exception as e:
            logger.error(f"Error in setup_ui: {e}")
            raise
        
    def setup_menus(self):
        """Setup application menus"""
        try:
            # Create menu bar
            menubar = self.menuBar()
            
            # File menu
            self.file_menu = FileMenu(self)
            menubar.addMenu(self.file_menu)
            
            # Saved locations menu
            self.saved_locations_menu = SavedLocationsMenu(self)
            self.saved_locations_menu.location_selected.connect(self._handle_directory_selected)
            # Update saved locations list when locations change
            self.saved_locations_menu.location_added.connect(self._refresh_saved_locations)
            self.saved_locations_menu.location_removed.connect(self._refresh_saved_locations)
            menubar.addMenu(self.saved_locations_menu)
            
            # Edit menu
            self.edit_menu = EditMenu(self)
            menubar.addMenu(self.edit_menu)
            
            # View menu
            self.view_menu = ViewMenu(self)
            menubar.addMenu(self.view_menu)
            
            # Tools menu
            self.tools_menu = ToolsMenu(self)
            menubar.addMenu(self.tools_menu)
            
            # Help menu with shortcut manager
            self.help_menu = HelpMenu(self.shortcut_manager, self)
            menubar.addMenu(self.help_menu)
            
            # Connect menu actions
            self.connect_menu_actions()
            
        except Exception as e:
            logger.error(f"Error in setup_menus: {e}")
            raise
        
    def connect_menu_actions(self):
        """Connect menu actions to handlers"""
        try:
            # File menu
            self.file_menu.set_open_callback(self._handle_directory_selected)
            self.file_menu.set_exit_callback(self.close)
            
            # View menu
            if self.toolbar:
                self.view_menu.set_toolbar_callback(self.toolbar.setVisible)
            if self.status_bar:
                self.view_menu.set_statusbar_callback(self.status_bar.setVisible)
                
        except Exception as e:
            logger.error(f"Error connecting menu actions: {e}")
            raise
        
    def connect_signals(self):
        """Connect all signals"""
        try:
            # Connect folder tree signals
            if self.folder_tree:
                self.folder_tree.directory_selected.connect(self._handle_directory_selected)
                
            # Connect grid view signals
            if self.grid_view:
                self.grid_view.imageClicked.connect(self._handle_image_clicked)
                self.grid_view.ratingChanged.connect(self._handle_rating_changed)
                
            # Connect search and filter signals
            if self.search_bar:
                self.search_bar.searchChanged.connect(self._handle_search_and_filters)
                self.search_bar.searchCleared.connect(self._handle_search_cleared)
                
            # Connect toolbar signals
            if self.toolbar:
                self.toolbar.show_subfolders_changed.connect(self._handle_show_subfolders_changed)
                
            # Connect saved locations signals
            if self.saved_locations_menu:
                self.saved_locations_menu.location_added.connect(self._refresh_saved_locations)
                self.saved_locations_menu.location_removed.connect(self._refresh_saved_locations)
                self.saved_locations_menu.default_location_changed.connect(self._handle_default_location_changed)
                
        except Exception as e:
            logger.error(f"Error connecting signals: {e}")
            raise
        
    def _handle_directory_selected(self, path: str) -> None:
        """Handle directory selection"""
        try:
            logger.debug(f"Handling directory selection: {path}")
            # Update status bar
            if self.status_bar:
                self.status_bar.showMessage(f"Loading {path}...")
            
            # Load directory in grid view
            if self.grid_view:
                # Get show subfolders setting from toolbar
                show_subfolders = self.toolbar.get_show_subfolders() if self.toolbar else False
                logger.debug(f"Loading directory with show_subfolders={show_subfolders}")
                
                # Load directory with batching enabled and subfolders setting
                self.grid_view.load_directory(
                    path,
                    batch_size=50,
                    include_subfolders=show_subfolders
                )
                logger.debug("Directory loaded in grid view")
                
                # Update window title
                self.setWindowTitle(f"IDIOVIEW - {path}")
            else:
                logger.warning("No grid view available to load directory")
            
            # Update filter panel with new images
            if self.filter_panel and self.grid_view:
                self.filter_panel.update_model_list(list(self.grid_view.thumbnails.keys()))
                logger.debug("Filter panel updated with new images")
            
            # Add to recent folders
            if self.saved_folders:
                self.saved_folders.add_recent_folder(path)
                logger.debug("Added to recent folders")
            
            # Update status
            if self.status_bar and self.grid_view:
                image_count = len(self.grid_view.thumbnails)
                subfolder_text = " (including subfolders)" if show_subfolders else ""
                status_msg = f"Loaded {image_count} images from {path}{subfolder_text}"
                self.status_bar.showMessage(status_msg)
                logger.debug(status_msg)
            
        except Exception as e:
            logger.error(f"Error loading directory {path}: {e}")
            if self.status_bar:
                self.status_bar.showMessage(f"Error loading directory: {str(e)}")
            # Show error dialog if needed
            
    def _handle_image_clicked(self, image_path: str, shift_held: bool):
        """Handle image click events"""
        try:
            # Update info panel
            if self.info_panel:
                self.info_panel.show_image_info(image_path)
            
            # Update tag panel
            if self.tag_panel:
                self.tag_panel.update_display(image_path)
                
        except Exception as e:
            logger.error(f"Error handling image click: {e}")
            
    def _handle_rating_changed(self, image_path: str, rating: int):
        """Handle rating changes"""
        try:
            # Update rating in service
            if self.rating_service:
                self.rating_service.update_rating(image_path, rating)
                
            # Update info panel
            if self.info_panel:
                self.info_panel.update_rating(image_path, rating)
                
        except Exception as e:
            logger.error(f"Error handling rating change: {e}")
        
    def _handle_search_and_filters(self, search_text: str, filters: dict):
        """Handle combined search and filter changes"""
        try:
            # Update status
            if self.status_bar:
                filter_text = ", ".join(f"{k}: {v}" for k, v in filters.items()) if filters else ""
                status = f"Search: {search_text}" if search_text else ""
                if filter_text:
                    status += f" | Filters: {filter_text}" if status else f"Filters: {filter_text}"
                self.status_bar.showMessage(status if status else "No search or filters active")
                
            # TODO: Implement actual search and filter logic for grid view
            logger.debug(f"Search text: {search_text}, Filters: {filters}")
            
        except Exception as e:
            logger.error(f"Error handling search and filters: {e}")
            
    def _handle_search_cleared(self):
        """Handle search and filters being cleared"""
        try:
            if self.status_bar:
                self.status_bar.showMessage("Search and filters cleared")
                
            # TODO: Reset grid view to show all images
            
        except Exception as e:
            logger.error(f"Error handling search cleared: {e}")
        
    def _refresh_saved_locations(self):
        """Refresh both the saved locations list and menu"""
        try:
            if self.saved_locations_list:
                self.saved_locations_list.refresh_locations()
            if self.saved_locations_menu:
                self.saved_locations_menu.update_locations_section()
        except Exception as e:
            logger.error(f"Error refreshing saved locations: {e}")
        
    def _handle_show_subfolders_changed(self, enabled: bool) -> None:
        """Handle show subfolders toggle"""
        try:
            if self.grid_view and self.grid_view.current_directory:
                self.grid_view.load_directory(
                    self.grid_view.current_directory,
                    batch_size=50,
                    include_subfolders=enabled
                )
                
                # Update status bar
                if self.status_bar:
                    image_count = len(self.grid_view.thumbnails)
                    subfolder_text = " (including subfolders)" if enabled else ""
                    self.status_bar.showMessage(f"Loaded {image_count} images from {self.grid_view.current_directory}{subfolder_text}")
                    
        except Exception as e:
            logger.error(f"Error handling show subfolders change: {e}")
            if self.status_bar:
                self.status_bar.showMessage(f"Error updating view: {str(e)}")
        
    def _handle_default_location_changed(self, path: Optional[str]):
        """Handle when default location is changed"""
        try:
            self.saved_folders.set_default_folder(path)
        except Exception as e:
            logger.error(f"Error handling default location change: {e}")
            
    def _delayed_initial_load(self):
        """Handle delayed loading of initial directory"""
        try:
            logger.debug("Starting delayed initial load")
            if not self._initial_load_complete:
                logger.debug("Initial load not yet complete")
                # Load default location if available
                default_path = self.saved_folders.get_default_folder()
                logger.debug(f"Got default folder path: {default_path}")
                if default_path:
                    logger.debug(f"Loading default folder: {default_path}")
                    self._handle_directory_selected(default_path)
                else:
                    logger.debug("No default folder path available")
                self._initial_load_complete = True
            else:
                logger.debug("Initial load already complete")
        except Exception as e:
            logger.error(f"Error in delayed initial load: {e}")
        
    def _setup_toolbar(self) -> None:
        """Setup toolbar and connect signals"""
        self.toolbar = Toolbar()
        self.addToolBar(self.toolbar)
        
        # Connect toolbar signals
        self.toolbar.show_subfolders_changed.connect(self._handle_show_subfolders_changed)
        
    def restore_state(self):
        """Restore window and splitter states"""
        try:
            # Restore window geometry
            if geometry := self.window_state.get_window_geometry("main"):
                self.restoreGeometry(geometry)
                
            # Restore window state (toolbars, etc)
            if state := self.window_state.get_window_state("main"):
                self.restoreState(state)
                
            # Restore main splitter state
            if self.main_splitter:
                if splitter_state := self.window_state.get_splitter_state("main", "main"):
                    self.main_splitter.restoreState(splitter_state)
                else:
                    # Set default proportions if no saved state
                    total_width = self.width()
                    self.main_splitter.setSizes([
                        int(total_width * 0.15),  # Left panel (15%)
                        int(total_width * 0.55),  # Grid view (55%)
                        int(total_width * 0.30),  # Right sidebar (30%)
                    ])
                    
        except Exception as e:
            logger.error(f"Error restoring window state: {e}")
            
    def closeEvent(self, event):
        """Handle window close"""
        try:
            # Stop any ongoing thumbnail loading
            if self.grid_view:
                self.grid_view.cleanup()
            
            # Save window states
            self.window_state.save_window_geometry("main", self.saveGeometry())
            self.window_state.save_window_state("main", self.saveState())
            
            # Save splitter state
            if self.main_splitter:
                self.window_state.save_splitter_state("main", "main", self.main_splitter.saveState())
            
            # Emit closing signal
            self.closing.emit()
            
            # Accept close event
            super().closeEvent(event)
            
        except Exception as e:
            logger.error(f"Error in closeEvent: {e}")
            event.accept()  # Ensure window closes even if there's an error 

    def _update_saved_locations_list(self):
        """Update the saved locations list when the menu is shown"""
        self.saved_locations_list.update_locations(self.saved_locations_menu.saved_locations)

    def on_fullscreen_closed(self):
        """Handle fullscreen viewer closing"""
        try:
            if self.shortcut_manager:
                self.shortcut_manager.fullscreen_viewer = None
            # Ensure grid view has focus after closing fullscreen
            if self.grid_view:
                self.grid_view.setFocus()
        except Exception as e:
            logger.error(f"Error handling fullscreen close: {e}") 