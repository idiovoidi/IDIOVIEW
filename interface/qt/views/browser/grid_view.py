from typing import Dict, Optional, List, Set
from PyQt6.QtWidgets import QScrollArea, QWidget, QGridLayout, QSizePolicy, QFrame
from PyQt6.QtGui import QImage, QKeyEvent
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread, QObject
from threading import Lock
import logging

# Configure PIL logging to be less verbose
logging.getLogger('PIL').setLevel(logging.WARNING)

from pathlib import Path
from .thumbnails import ThumbnailWidget
from .base_view import BaseView
from core.domain.entities.image import Image
from core.application.services.rating_service import RatingService
from core.application.services.image_loader_service import ImageLoaderService
from core.infrastructure.cache.thumbnail_cache import ThumbnailCache
from ...widgets.menus.context_menu import ContextMenu
from core.domain.entities.image_hash import ImageHash

logger = logging.getLogger(__name__)

class DirectoryLoader(QThread):
    """Thread for loading directory contents"""
    loaded = pyqtSignal(list)  # Emits list of images when done
    error = pyqtSignal(str)    # Emits error message if failed
    
    def __init__(self, image_loader_service, path: str):
        super().__init__()
        self.image_loader = image_loader_service
        self.path = path
        
    def run(self):
        try:
            images = self.image_loader.load_directory(self.path)
            if not images:
                self.error.emit(f"No images found in directory: {self.path}")
                return
            self.loaded.emit(images)
        except Exception as e:
            self.error.emit(str(e))

class BatchProcessor(QObject):
    """Handles batch processing of thumbnails"""
    batch_complete = pyqtSignal()  # Emits when batch is processed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.process_batch)
        self._timer.setInterval(50)  # 50ms between batches
        self._processing = False
        self._lock = Lock()
        
    def start(self):
        with self._lock:
            if not self._processing:
                self._processing = True
                self._timer.start()
                
    def stop(self):
        with self._lock:
            self._processing = False
            self._timer.stop()
            
    def is_processing(self):
        with self._lock:
            return self._processing
            
    def process_batch(self):
        self.batch_complete.emit()

class GridView(BaseView):
    """Grid view for displaying image thumbnails."""
    
    # Signals
    imageClicked = pyqtSignal(str, bool)  # Signals (image_path, shift_held)
    ratingChanged = pyqtSignal(str, int)  # Signals (image_path, new_rating)
    loadingProgress = pyqtSignal(int, int)  # Signals (loaded_count, total_count)
    selectionChanged = pyqtSignal()  # Emitted when selection changes
    fullscreenRequested = pyqtSignal(str)  # Emitted when fullscreen is requested for an image
    
    def __init__(self, 
                 rating_service: RatingService,
                 image_loader_service: ImageLoaderService,
                 parent: Optional[QWidget] = None):
        super().__init__(rating_service, image_loader_service, parent)
        
        # Initialize state
        self._batch_size = 50
        self._is_loading = False
        self.thumbnails: Dict[str, ThumbnailWidget] = {}
        self.selected_paths: Set[str] = set()
        self.last_selected_path: Optional[str] = None
        self.current_context_path: Optional[str] = None
        self.current_directory: Optional[str] = None
        
        # Hash tracking
        self.image_hashes: Dict[str, str] = {}  # Map of path -> hash
        
        # Initialize layout state
        self._reflow_timer = QTimer(self)
        self._reflow_timer.timeout.connect(self._do_reflow)
        self._reflow_timer.setSingleShot(True)
        self._needs_reflow = False
        self._is_reflowing = False
        self._layout_lock = Lock()
        
        # Setup context menu
        self.context_menu = ContextMenu(self)
        self._setup_context_menu()
        
        # Setup grid-specific UI
        self._setup_grid_ui()
        
        # Apply dark theme
        self.setStyleSheet("""
            QScrollArea { 
                background-color: #1e1e1e; 
                border: none; 
            }
            QWidget { 
                background-color: #1e1e1e; 
            }
        """)
        
        # Connect to loader service signals
        self.image_loader.directory_loaded.connect(self._on_directory_loaded)
        self.image_loader.load_error.connect(self._on_load_error)
        self.image_loader.loading_progress.connect(self._on_loading_progress)
        self.image_loader.thumbnail_batch_ready.connect(self._on_batch_ready)
        self.image_loader.thumbnail_ready.connect(self._on_thumbnail_ready)
        
    def _setup_context_menu(self):
        """Setup context menu callbacks"""
        self.context_menu.set_rating_callback(self._handle_context_rating)
        self.context_menu.set_status_callback(self._handle_context_status)
        self.context_menu.set_copy_callback(self._handle_context_copy)
        self.context_menu.set_copy_path_callback(self._handle_context_copy_path)
        self.context_menu.set_delete_callback(self._handle_context_delete)
        
    def _handle_context_rating(self, rating: int):
        """Handle rating change from context menu"""
        if self.current_context_path:
            self._on_rating_changed(self.current_context_path, rating)
            
    def _handle_context_status(self, status: str):
        """Handle status change from context menu"""
        if self.current_context_path:
            # TODO: Implement status change handling
            logger.debug(f"Status change for {self.current_context_path}: {status}")
            
    def _handle_context_copy(self):
        """Handle copy action from context menu"""
        if self.current_context_path:
            # TODO: Implement copy to clipboard
            logger.debug(f"Copy {self.current_context_path}")
            
    def _handle_context_copy_path(self):
        """Handle copy path action from context menu"""
        if self.current_context_path:
            # TODO: Implement copy path to clipboard
            logger.debug(f"Copy path {self.current_context_path}")
            
    def _handle_context_delete(self):
        """Handle delete action from context menu"""
        if self.current_context_path:
            # TODO: Implement delete with confirmation
            logger.debug(f"Delete {self.current_context_path}")

    def show_context_menu(self, image_path: str, global_pos):
        """Show context menu for image"""
        try:
            if thumbnail := self.thumbnails.get(image_path):
                self.current_context_path = image_path
                
                # Update menu state
                if self.rating_service:
                    rating = self.rating_service.get_image_rating(image_path)
                    self.context_menu.update_rating(rating)
                
                # TODO: Update status when implemented
                # self.context_menu.update_status(status)
                
                # Show menu at global position
                self.context_menu.popup(global_pos)
        except Exception as e:
            logger.error(f"Error showing context menu: {e}")

    def _setup_grid_ui(self):
        """Setup grid-specific UI components"""
        # Create container widget
        self.container = QWidget()
        self.container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setWidget(self.container)
        
        # Create grid layout
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
    def load_directory(self, path: str, batch_size: int = 50, include_subfolders: bool = False) -> None:
        """Load images from a directory"""
        try:
            logger.debug(f"Loading directory: {path} (include_subfolders: {include_subfolders})")
            
            # Update state
            self.current_directory = path
            self._batch_size = batch_size
            self._is_loading = True
            
            # Clear existing thumbnails
            self.clear_thumbnails()
            
            # Start loading images
            self.image_loader.load_directory(path, batch_size, include_subfolders)
            
        except Exception as e:
            logger.error(f"Error loading directory {path}: {e}")
            self._is_loading = False
            
    def clear_thumbnails(self) -> None:
        """Clear all thumbnails"""
        try:
            # Remove all thumbnails from layout
            while self.grid_layout.count():
                item = self.grid_layout.takeAt(0)
                if widget := item.widget():
                    widget.deleteLater()
            
            # Clear thumbnail dictionary
            self.thumbnails.clear()
            self.selected_paths.clear()
            self.last_selected_path = None
            
        except Exception as e:
            logger.error(f"Error clearing thumbnails: {e}")

    def _on_directory_loaded(self, images: List[Image]) -> None:
        """Handle async loaded images"""
        try:
            self._on_batch_ready(images)
        except Exception as e:
            logger.error(f"Error handling loaded directory: {e}")
            self._is_loading = False
            
    def _on_load_error(self, error: str):
        """Handle directory loading error"""
        logger.error(f"Directory loading error: {error}")
        self._is_loading = False
        
    def _on_batch_ready(self, images: List[Image]) -> None:
        """Handle batch of loaded images"""
        try:
            for image in images:
                self.add_image(image)
            
            # Schedule reflow if needed
            if self._needs_reflow:
                self._reflow_timer.start(100)
        except Exception as e:
            logger.error(f"Error handling image batch: {e}")

    def _on_loading_progress(self, loaded: int, total: int) -> None:
        """Handle loading progress updates"""
        self.loadingProgress.emit(loaded, total)

    def _on_thumbnail_ready(self, image_path: str, thumbnail_image: QImage) -> None:
        """Handle thumbnail ready from loader"""
        try:
            if thumbnail := self.thumbnails.get(image_path):
                thumbnail.set_thumbnail(thumbnail_image)
        except Exception as e:
            logger.error(f"Error handling thumbnail ready: {e}")

    def add_image(self, image: Image) -> None:
        """Add an image to the grid view"""
        try:
            if image.path in self.thumbnails:
                return
                
            # Create thumbnail
            thumbnail = self.create_thumbnail(image)
            
            # Store image hash
            self.image_hashes[image.path] = ImageHash.create_file_hash(image.path)
            
            # Schedule reflow only if needed
            if not self._is_reflowing:
                self._needs_reflow = True
                self._reflow_timer.start(250)  # Increased debounce time
            
        except Exception as e:
            logger.error(f"Error adding image {image.path}: {e}", exc_info=True)
            
    def _do_reflow(self) -> None:
        """Handle deferred reflow"""
        try:
            if self._is_reflowing:
                return
                
            self._is_reflowing = True
            self.reflow_layout()
            self._is_reflowing = False
            
        except Exception as e:
            logger.error(f"Error in deferred reflow: {e}")
            self._is_reflowing = False

    def reflow_layout(self) -> None:
        """Reflow the layout"""
        try:
            if not self.thumbnails:
                return

            self._is_reflowing = True
            
            # Get container width and calculate columns
            container_width = self.container.width()
            thumbnail_width = next(iter(self.thumbnails.values())).width()
            spacing = self.grid_layout.spacing()
            columns = max(1, (container_width + spacing) // (thumbnail_width + spacing))
            
            # Reposition all thumbnails
            for idx, thumbnail in enumerate(self.thumbnails.values()):
                row = idx // columns
                col = idx % columns
                self.grid_layout.addWidget(thumbnail, row, col)
                
            # Update tab order
            self._update_tab_order(columns)
            
            self._is_reflowing = False
            self._needs_reflow = False
            
        except Exception as e:
            logger.error(f"Error in reflow_layout: {e}")
            self._is_reflowing = False
            
    def _update_tab_order(self, columns: int) -> None:
        """Update tab order for thumbnails"""
        try:
            thumbnails = list(self.thumbnails.values())
            if not thumbnails:
                return
                
            # Set tab order following grid layout
            for i in range(len(thumbnails) - 1):
                QWidget.setTabOrder(thumbnails[i], thumbnails[i + 1])
                
        except Exception as e:
            logger.error(f"Error updating tab order: {e}")
            
    def resizeEvent(self, event) -> None:
        """Handle resize with debouncing"""
        try:
            super().resizeEvent(event)
            if not self._is_reflowing:  # Only schedule if not already reflowing
                self._needs_reflow = True
                self._reflow_timer.start(250)  # Increased debounce time
        except Exception as e:
            logger.error(f"Error handling resize: {e}")
            
    def _on_thumbnail_clicked(self, image_path: str, shift_held: bool) -> None:
        """Handle thumbnail click with selection logic"""
        try:
            if not shift_held:
                # Single selection
                self.deselect_all()
                self._update_selection(image_path, True)
                self.last_selected_path = image_path
            else:
                # Shift selection
                if self.last_selected_path:
                    # Get range
                    all_paths = list(self.thumbnails.keys())
                    start_idx = all_paths.index(self.last_selected_path)
                    end_idx = all_paths.index(image_path)
                    
                    # Ensure correct order
                    if start_idx > end_idx:
                        start_idx, end_idx = end_idx, start_idx
                        
                    # Select range
                    for path in all_paths[start_idx:end_idx + 1]:
                        self._update_selection(path, True)
                else:
                    # No previous selection
                    self._update_selection(image_path, True)
                    self.last_selected_path = image_path
            
            # Emit signals
            self.imageClicked.emit(image_path, shift_held)
            self.selectionChanged.emit()
            
        except Exception as e:
            logger.error(f"Error handling thumbnail click: {e}")

    def _update_selection(self, image_path: str, selected: bool) -> None:
        """Update selection state of a thumbnail"""
        if thumbnail := self.thumbnails.get(image_path):
            if selected:
                self.selected_paths.add(image_path)
            else:
                self.selected_paths.discard(image_path)
                if self.last_selected_path == image_path:
                    self.last_selected_path = None
            thumbnail.setStyleSheet(self._get_thumbnail_style(selected))

    def _get_thumbnail_style(self, selected: bool) -> str:
        """Get thumbnail style based on selection state"""
        return """
            QLabel {
                background-color: #2d2d2d;
                border: 2px solid %s;
                border-radius: 3px;
                padding: 2px;
            }
        """ % ("#0078d4" if selected else "transparent")

    def deselect_all(self) -> None:
        """Deselect all thumbnails"""
        for path in list(self.selected_paths):
            self._update_selection(path, False)
        self.last_selected_path = None

    def get_selected_paths(self) -> Set[str]:
        """Get currently selected paths"""
        return self.selected_paths.copy()
        
    def _handle_rating_changed(self, image_path: str, rating: int):
        """Handle rating changes from thumbnails"""
        try:
            if self.rating_service.update_rating(image_path, rating):
                self.ratingChanged.emit(image_path, rating)
        except Exception as e:
            logger.error(f"Error handling rating change: {e}")

    def clear(self) -> None:
        """Clear the grid view and clean up resources"""
        try:
            # Clear thumbnails
            self.clear_thumbnails()
            
            # Reset state
            self.current_directory = None
            self._is_loading = False
            self._needs_reflow = False
            self._is_reflowing = False
            
            # Update layout
            self.container.updateGeometry()
            self.grid_layout.update()
            
        except Exception as e:
            logger.error(f"Error clearing grid view: {e}")

    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            # Clear view
            self.clear()
            
            # Clean up image loader service
            if hasattr(self, 'image_loader'):
                self.image_loader.cleanup()
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def create_thumbnail(self, image: Image) -> ThumbnailWidget:
        """Create and setup a thumbnail widget"""
        thumbnail = ThumbnailWidget(
            image_path=image.path,
            initial_rating=image.rating,
            parent=self.container
        )
        
        # Connect signals
        thumbnail.clicked.connect(self._on_thumbnail_clicked)
        thumbnail.rating_changed.connect(self._on_rating_changed)
        thumbnail.customContextMenuRequested.connect(
            lambda pos, path=image.path: self.show_context_menu(path, thumbnail.mapToGlobal(pos))
        )
        thumbnail.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        # Store thumbnail
        self.thumbnails[image.path] = thumbnail
        return thumbnail

    def _on_rating_changed(self, image_path: str, rating: int):
        """Handle rating changes from thumbnails"""
        try:
            if self.rating_service.update_rating(image_path, rating):
                self.ratingChanged.emit(image_path, rating)
        except Exception as e:
            logger.error(f"Error handling rating change: {e}")

    def get_all_images(self) -> List[str]:
        """Get all image paths in current view"""
        return list(self.thumbnails.keys())
        
    def get_current_index(self) -> Optional[int]:
        """Get index of currently selected image"""
        if self.last_selected_path:
            try:
                return list(self.thumbnails.keys()).index(self.last_selected_path)
            except ValueError:
                return None
        return None
        
    def select_by_index(self, index: int) -> None:
        """Select image by index"""
        try:
            path = list(self.thumbnails.keys())[index]
            self.deselect_all()
            self._update_selection(path, True)
            self.last_selected_path = path
            self.selectionChanged.emit()
            
            # Ensure selected thumbnail is visible
            if thumbnail := self.thumbnails.get(path):
                self.ensureWidgetVisible(thumbnail)
        except (IndexError, KeyError):
            pass
            
    def on_fullscreen_rating_changed(self, path: str, rating: int) -> None:
        """Handle rating changes from fullscreen view"""
        if thumbnail := self.thumbnails.get(path):
            thumbnail.update_rating(rating)
            self.ratingChanged.emit(path, rating)
            
    def on_fullscreen_image_changed(self, path: str) -> None:
        """Handle current image changes from fullscreen view"""
        try:
            index = list(self.thumbnails.keys()).index(path)
            self.select_by_index(index)
        except ValueError:
            pass

    def sync_with_fullscreen(self, current_path: str) -> None:
        """Sync grid view with fullscreen viewer"""
        try:
            if current_path in self.thumbnails:
                # Update selection
                self.deselect_all()
                self._update_selection(current_path, True)
                self.last_selected_path = current_path
                self.selectionChanged.emit()
                
                # Ensure the thumbnail is visible
                if thumbnail := self.thumbnails.get(current_path):
                    self.ensureWidgetVisible(thumbnail)
                    thumbnail.setFocus()
                    
        except Exception as e:
            logger.error(f"Error syncing with fullscreen: {e}")

    def get_current_image_data(self) -> dict:
        """Get data needed for fullscreen view"""
        return {
            'paths': self.get_all_images(),
            'current_index': self.get_current_index(),
            'hashes': self.image_hashes.copy()
        }

    def handle_fullscreen_closed(self, last_path: str) -> None:
        """Handle fullscreen viewer being closed"""
        try:
            self.sync_with_fullscreen(last_path)
        except Exception as e:
            logger.error(f"Error handling fullscreen close: {e}")

    def handle_fullscreen_navigation(self, new_path: str) -> None:
        """Handle navigation in fullscreen view"""
        try:
            self.sync_with_fullscreen(new_path)
        except Exception as e:
            logger.error(f"Error handling fullscreen navigation: {e}")

    def handle_fullscreen_rating_changed(self, path: str, rating: int) -> None:
        """Handle rating changes from fullscreen view"""
        try:
            if thumbnail := self.thumbnails.get(path):
                thumbnail.set_rating(rating)
                self.ratingChanged.emit(path, rating)
        except Exception as e:
            logger.error(f"Error handling fullscreen rating change: {e}")

    def remove_image(self, image_path: str) -> None:
        """Remove an image from the grid view"""
        try:
            # Remove thumbnail widget
            if thumbnail := self.thumbnails.pop(image_path, None):
                self.grid_layout.removeWidget(thumbnail)
                thumbnail.deleteLater()
            
            # Remove hash
            self.image_hashes.pop(image_path, None)
            
            # Update selection
            self.selected_paths.discard(image_path)
            if self.last_selected_path == image_path:
                self.last_selected_path = None
            
            # Reflow layout if needed
            if not self._is_reflowing:
                self._needs_reflow = True
                self._reflow_timer.start(250)
                
        except Exception as e:
            logger.error(f"Error removing image {image_path}: {e}")

    def get_image_by_hash(self, hash_value: str) -> Optional[str]:
        """Find image path by its hash"""
        for path, img_hash in self.image_hashes.items():
            if img_hash == hash_value:
                return path
        return None
        
    def select_by_hash(self, hash_value: str) -> bool:
        """Select image by its hash"""
        try:
            if path := self.get_image_by_hash(hash_value):
                self.deselect_all()
                self._update_selection(path, True)
                self.last_selected_path = path
                self.selectionChanged.emit()
                
                # Ensure selected thumbnail is visible
                if thumbnail := self.thumbnails.get(path):
                    self.ensureWidgetVisible(thumbnail)
                return True
            return False
        except Exception as e:
            logger.error(f"Error selecting by hash: {e}")
            return False
            
    def get_selected_hash(self) -> Optional[str]:
        """Get hash of currently selected image"""
        if self.last_selected_path:
            return self.image_hashes.get(self.last_selected_path)
        return None 