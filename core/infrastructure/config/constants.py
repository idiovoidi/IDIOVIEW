"""Application-wide constants"""

import os
from pathlib import Path

# Default paths - these can be overridden by user settings
DEFAULT_PATHS = {
    'images': 'user_data/images',
    'thumbnails': 'user_data/cache/thumbnails',
    'favorites': 'user_data/collections/favorites',
    'boards': 'user_data/collections/boards',
    'cache': 'user_data/cache',
    'config': 'user_data/config',
    'collections': 'user_data/collections'
}

# Application settings
APP_NAME = "ID:I/O VIEW"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Mitchell"

# UI Constants
THUMBNAIL_SIZE = 200
THUMBNAIL_PADDING = 10
SCROLL_BAR_WIDTH = 15

# File extensions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

__all__ = [
    'DEFAULT_PATHS',
    'APP_NAME',
    'APP_VERSION',
    'APP_AUTHOR',
    'THUMBNAIL_SIZE',
    'THUMBNAIL_PADDING',
    'SCROLL_BAR_WIDTH',
    'IMAGE_EXTENSIONS'
] 