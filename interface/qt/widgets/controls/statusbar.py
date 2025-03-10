"""Status bar widget for application status"""

import logging
"""Central Qt imports for PyQt6"""
from PyQt6.QtCore import (
    Qt, QObject, QSize, QPoint, 
    QEvent, pyqtSignal, QTimer
)
from PyQt6.QtGui import (
    QAction, QIcon, QKeySequence,
    QColor, QFont, QPainter
)
from PyQt6.QtWidgets import (
    QApplication, QWidget, QMainWindow,
    QLabel, QPushButton, QMenu, QToolBar, QComboBox, QSpinBox, QVBoxLayout, QSpacerItem, QSizePolicy, QStatusBar, QProgressBar
)

logger = logging.getLogger(__name__)

class Statusbar(QStatusBar):
    """Application status bar"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup status bar UI elements"""
        # Image count label
        self.image_count = QLabel()
        self.addWidget(self.image_count)
        
        # Selection count label
        self.selection_count = QLabel()
        self.addWidget(self.selection_count)
        
        # Add permanent progress bar
        self.progress = QProgressBar()
        self.progress.setFixedWidth(150)
        self.progress.hide()
        self.addPermanentWidget(self.progress)
        
        # Style
        self.setStyleSheet("""
            QStatusBar {
                background-color: #2d2d2d;
                color: #cccccc;
            }
            QLabel {
                padding: 0 10px;
            }
            QProgressBar {
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
            }
        """)
        
    def update_image_count(self, total: int, filtered: int = None):
        """Update image count display"""
        if filtered is not None and filtered != total:
            self.image_count.setText(f"Images: {filtered}/{total}")
        else:
            self.image_count.setText(f"Images: {total}")
            
    def update_selection(self, count: int):
        """Update selection count display"""
        if count > 0:
            self.selection_count.setText(f"Selected: {count}")
            self.selection_count.show()
        else:
            self.selection_count.hide()
            
    def show_progress(self, value: int = 0, maximum: int = 100):
        """Show and update progress bar"""
        self.progress.setMaximum(maximum)
        self.progress.setValue(value)
        self.progress.show()
        
    def hide_progress(self):
        """Hide progress bar"""
        self.progress.hide() 