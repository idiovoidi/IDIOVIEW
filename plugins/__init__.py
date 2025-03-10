"""Plugin system initialization"""

import logging
from pathlib import Path
from typing import Dict, Type, Optional, Any

logger = logging.getLogger(__name__)

class PluginManager:
    """Manages plugin loading and access"""
    
    def __init__(self):
        self._plugins: Dict[str, Any] = {}
        self._plugin_dir = Path(__file__).parent
        
    def load_plugins(self) -> None:
        """Load all available plugins"""
        try:
            # Load visualization plugins if directory exists
            viz_dir = self._plugin_dir / "visualizations"
            if viz_dir.exists() and viz_dir.is_dir():
                self._plugins["visualizations"] = self._load_visualization_plugins()
                
        except Exception as e:
            logger.error(f"Error loading plugins: {e}")
            
    def _load_visualization_plugins(self) -> Dict[str, Type['BaseVisualization']]:
        """Load visualization plugin types"""
        from .visualizations.base import BaseVisualization
        plugins = {}
        
        try:
            # Import visualization modules
            viz_dir = self._plugin_dir / "visualizations"
            for file in viz_dir.glob("*.py"):
                if file.stem == "base" or file.stem.startswith("_"):
                    continue
                    
                try:
                    module_name = f"plugins.visualizations.{file.stem}"
                    module = __import__(module_name, fromlist=["*"])
                    
                    # Find visualization classes
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            issubclass(attr, BaseVisualization) and 
                            attr != BaseVisualization):
                            plugins[attr_name] = attr
                            
                except Exception as e:
                    logger.error(f"Error loading visualization plugin {file}: {e}")
                    
        except Exception as e:
            logger.error(f"Error scanning visualization plugins: {e}")
            
        return plugins
        
    def get_plugin(self, plugin_type: str) -> Optional[Any]:
        """Get plugin by type"""
        return self._plugins.get(plugin_type)
        
    def cleanup(self) -> None:
        """Clean up plugin resources"""
        try:
            for plugin in self._plugins.values():
                if hasattr(plugin, 'cleanup'):
                    plugin.cleanup()
            self._plugins.clear()
        except Exception as e:
            logger.error(f"Error cleaning up plugins: {e}") 