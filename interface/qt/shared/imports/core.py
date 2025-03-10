"""Core Qt imports for basic functionality"""

from PyQt6.QtCore import (
    # Core functionality
    Qt, QObject, QEvent,
    
    # Signals and slots
    pyqtSignal, pyqtSlot,
    
    # Geometry and layout
    QPoint, QSize, QRect,
    
    # Threading and async
    QThread, QTimer,
    
    # Data handling
    QMimeData, QUrl, QByteArray,
    QBuffer, QIODevice,
    
    # Settings and paths
    QSettings, QStandardPaths
)

__all__ = [
    # Core
    'Qt', 'QObject', 'QEvent',
    
    # Signals
    'pyqtSignal', 'pyqtSlot',
    
    # Geometry
    'QPoint', 'QSize', 'QRect',
    
    # Threading
    'QThread', 'QTimer',
    
    # Data
    'QMimeData', 'QUrl', 'QByteArray',
    'QBuffer', 'QIODevice',
    
    # Settings
    'QSettings', 'QStandardPaths'
] 