"""Base class for visualization plugins"""

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
from PyQt6.QtWidgets import QWidget

class BaseVisualization(ABC):
    """Abstract base class for visualization plugins"""
    
    def __init__(self):
        self._widget: Optional[QWidget] = None
        self._data: Dict[str, Any] = {}
        
    @property
    def widget(self) -> Optional[QWidget]:
        """Get the visualization widget"""
        return self._widget
        
    @property
    def name(self) -> str:
        """Get visualization name"""
        return self.__class__.__name__
        
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the visualization"""
        pass
        
    @abstractmethod
    def update(self, data: Optional[Any] = None) -> None:
        """Update visualization with new data"""
        pass
        
    def cleanup(self) -> None:
        """Clean up resources"""
        if self._widget:
            self._widget.deleteLater()
            self._widget = None
        self._data.clear() 