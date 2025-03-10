#!/usr/bin/env python3
import sys
import os
import logging
from pathlib import Path
import ctypes

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from core.container.container import Container
from interface.qt.main_window import MainWindow

def main():
    try:
        # Setup logging
        log_dir = Path("user_data/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "app.log"
        
        # Configure logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Set specific loggers to DEBUG
        logging.getLogger('core.infrastructure.cache.thumbnail_cache').setLevel(logging.DEBUG)
        logging.getLogger('interface.qt.views.browser.thumbnails').setLevel(logging.DEBUG)
        logging.getLogger('interface.qt.views.browser.grid_view').setLevel(logging.DEBUG)
        logging.getLogger('core.infrastructure.persistence.local_image_repository').setLevel(logging.DEBUG)
        
        logger = logging.getLogger(__name__)
        logger.info("Starting application")
        
        # Initialize dependency container
        container = Container()
        
        # Wire the container
        container.wire(
            packages=[
                "interface.qt.views",
                "interface.qt.widgets",
                "interface.qt.controllers",
                "interface.qt.main_window"
            ]
        )
        
        # Initialize resources
        container.init_resources()
        
        # Create Qt application
        app = QApplication(sys.argv)
        
        # Set application icon using high-res version
        # Get the project root directory (where run.py is located)
        root_dir = Path(__file__).resolve().parent
        icon_path = root_dir / "core" / "infrastructure" / "assets" / "logo" / "Eye-Logo-256.png"
        
        if icon_path.exists():
            app_icon = QIcon(str(icon_path))
            app.setWindowIcon(app_icon)
            logger.info(f"Set application icon from {icon_path}")
            
            # Set Windows-specific taskbar icon
            if sys.platform == 'win32':
                # Set app id for Windows taskbar grouping
                app_id = "idioview.app.1.0"
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        else:
            logger.warning(f"Application icon not found at {icon_path}")
        
        # Create and show main window with container
        window = MainWindow(container=container)
        if icon_path.exists():
            window.setWindowIcon(app_icon)  # Ensure the window also has the icon
        window.show()
        
        # Run application
        return app.exec()
        
    except Exception as e:
        logging.exception("Fatal error in main")
        return 1

if __name__ == "__main__":
    sys.exit(main())    