"""Widget-related Qt imports"""

from PyQt6.QtWidgets import (
    # Base widgets
    QWidget, QMainWindow, QDialog,
    
    # Layout widgets
    QVBoxLayout, QHBoxLayout, QSplitter,
    QFrame, QGroupBox, QScrollArea,
    QSpacerItem, QSizePolicy,
    
    # Input widgets
    QPushButton, QLineEdit, QTextEdit,
    QComboBox, QSpinBox, QCheckBox,
    QRadioButton,
    
    # Display widgets
    QLabel, QProgressBar,
    
    # Menu and toolbar
    QMenuBar, QMenu, QToolBar, QStatusBar,
    QSystemTrayIcon,
    
    # Dialogs
    QFileDialog, QMessageBox,
    
    # Tabs
    QTabWidget
)

__all__ = [
    # Base
    'QWidget', 'QMainWindow', 'QDialog',
    
    # Layout
    'QVBoxLayout', 'QHBoxLayout', 'QSplitter',
    'QFrame', 'QGroupBox', 'QScrollArea',
    'QSpacerItem', 'QSizePolicy',
    
    # Input
    'QPushButton', 'QLineEdit', 'QTextEdit',
    'QComboBox', 'QSpinBox', 'QCheckBox',
    'QRadioButton',
    
    # Display
    'QLabel', 'QProgressBar',
    
    # Menu
    'QMenuBar', 'QMenu', 'QToolBar', 'QStatusBar',
    'QSystemTrayIcon',
    
    # Dialogs
    'QFileDialog', 'QMessageBox',
    
    # Tabs
    'QTabWidget'
] 