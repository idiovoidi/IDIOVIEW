"""PyQt6 imports organized by category"""

from .core import *
from .widgets import *
from .gui import *

# Constants
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
DEFAULT_THUMBNAIL_SIZE = 200
THUMBNAIL_PADDING = 10
SCROLL_BAR_WIDTH = 15

__all__ = (
    core.__all__ +  # Core functionality
    widgets.__all__ +  # Widget components
    gui.__all__ +  # GUI elements
    [
        'IMAGE_EXTENSIONS',
        'DEFAULT_THUMBNAIL_SIZE',
        'THUMBNAIL_PADDING',
        'SCROLL_BAR_WIDTH'
    ]
) 