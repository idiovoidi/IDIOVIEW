"""Application dependency container"""

from typing import Optional, Dict, Any
from pathlib import Path
import logging
from dependency_injector import containers, providers

# Configuration imports
from core.infrastructure.config.app_config import AppConfig
from core.infrastructure.config.user_config import UserConfigManager
from core.infrastructure.config.window_state import WindowStateManager
from core.infrastructure.config.savedfolders import SavedFoldersManager

# Cache imports
from core.infrastructure.cache.thumbnail_cache import ThumbnailCache
from core.infrastructure.cache.metadata_cache import MetadataCache

# Repository imports
from core.infrastructure.persistence.local_image_repository import LocalImageRepository

# Service imports
from core.application.services.image_loader_service import ImageLoaderService
from core.application.services.rating_service import RatingService
from core.application.services.metadata_service import MetadataService
from core.application.services.image_transform_service import ImageTransformService
from core.application.services.image_hash_service import ImageHashService
from core.application.services.clustering_service import ClusterManager

logger = logging.getLogger(__name__)

class Container(containers.DeclarativeContainer):
    """Main application container for dependency management"""
    
    # Configuration
    config = providers.Configuration()
    
    # Core paths
    base_dir = providers.Singleton(
        lambda: Path(__file__).parent.parent.parent
    )
    
    # Configuration services
    app_config = providers.Singleton(
        AppConfig.create_default,
        base_dir=base_dir
    )
    
    user_config = providers.Singleton(
        UserConfigManager,
        app_dir=base_dir
    )
    
    window_state = providers.Singleton(
        WindowStateManager,
        state_file=providers.Factory(
            lambda config: config.config_dir / "window_state.ini",
            config=app_config
        )
    )
    
    saved_folders = providers.Singleton(
        SavedFoldersManager,
        user_config=user_config
    )
    
    # Cache directories
    cache_dir = providers.Factory(
        lambda config: config.cache_dir,
        config=app_config
    )
    
    thumbnail_cache_dir = providers.Factory(
        lambda cache_dir: cache_dir / "thumbnails",
        cache_dir=cache_dir
    )
    
    metadata_cache_dir = providers.Factory(
        lambda cache_dir: cache_dir / "metadata",
        cache_dir=cache_dir
    )
    
    # Infrastructure services
    thumbnail_cache = providers.Singleton(
        ThumbnailCache,
        cache_dir=thumbnail_cache_dir,
        max_size=providers.Factory(
            lambda settings: (settings.thumbnail_size, settings.thumbnail_size),
            settings=user_config.provided.settings
        )
    )
    
    metadata_cache = providers.Singleton(
        MetadataCache,
        cache_dir=metadata_cache_dir
    )
    
    # Repository layer
    image_repository = providers.Singleton(
        LocalImageRepository,
        config=app_config
    )
    
    # Application service layer
    image_loader = providers.Singleton(
        ImageLoaderService,
        image_repository=image_repository,
        thumbnail_cache=thumbnail_cache
    )
    
    rating_service = providers.Singleton(
        RatingService,
        image_repository=image_repository
    )
    
    metadata_service = providers.Singleton(
        MetadataService,
        config=app_config
    )
    
    image_transform = providers.Singleton(
        ImageTransformService,
        config=app_config
    )
    
    image_hash = providers.Singleton(
        ImageHashService
    )
    
    clustering = providers.Singleton(
        ClusterManager,
        hash_service=image_hash
    )
    
    def init_resources(self) -> None:
        """Initialize container resources"""
        try:
            # Ensure directories exist
            self.app_config().ensure_directories()
            
            # Initialize caches
            self.thumbnail_cache()
            self.metadata_cache()
            
            logger.info("Container resources initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing container resources: {e}")
            raise

    def cleanup(self) -> None:
        """Clean up container resources"""
        try:
            # Clean up caches
            self.thumbnail_cache().cleanup()
            self.metadata_cache().cleanup()
            
            logger.info("Container resources cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error cleaning up container resources: {e}") 