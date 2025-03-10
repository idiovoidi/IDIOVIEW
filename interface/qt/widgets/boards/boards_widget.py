"""Board management widgets for organizing images"""

import logging
import os
import json
from pathlib import Path
from typing import Optional, Dict, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QListWidget, QInputDialog, QMessageBox,
    QMenu
)
from PyQt6.QtCore import pyqtSignal
from datetime import datetime

from core.domain.entities.image import Image
from core.application.services.image_loader_service import ImageLoaderService
from core.infrastructure.config.app_config import AppConfig

logger = logging.getLogger(__name__)

class BoardsManager:
    """Manager for image boards functionality"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.boards_dir = config.settings.boards_dir
        self.boards = {}
        self.load_boards()
        
    def load_boards(self):
        """Load all board data from json files"""
        try:
            for filename in os.listdir(self.boards_dir):
                if filename.endswith('.json'):
                    board_name = filename[:-5]  # Remove .json
                    self.boards[board_name] = self.load_board(board_name)
        except Exception as e:
            logger.error(f"Error loading boards: {e}")
            
    def load_board(self, board_name: str) -> dict:
        """Load a specific board's data"""
        try:
            board_path = self.get_board_path(board_name)
            if os.path.exists(board_path):
                with open(board_path) as f:
                    return json.load(f)
            return {'images': [], 'created': '', 'modified': ''}
        except Exception as e:
            logger.error(f"Error loading board {board_name}: {e}")
            return {'images': [], 'created': '', 'modified': ''}
            
    def save_board(self, board_name: str, data: dict):
        """Save board data to file"""
        try:
            board_path = self.get_board_path(board_name)
            with open(board_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving board {board_name}: {e}")
            
    def get_board_path(self, board_name: str) -> str:
        """Get path to board json file"""
        return os.path.join(self.boards_dir, f"{board_name}.json")
        
    def create_board(self, name: str) -> bool:
        """Create a new board"""
        try:
            # Validate name
            if not name or name in self.boards:
                return False
                
            # Create board data
            board_data = {
                'name': name,
                'images': [],
                'created': datetime.now().isoformat(),
                'modified': datetime.now().isoformat()
            }
            
            # Save board
            self.boards[name] = board_data
            self.save_board(name, board_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating board {name}: {e}")
            return False
            
    def add_to_board(self, board_name: str, image: Image) -> bool:
        """Add an image to a board"""
        try:
            if board_name not in self.boards:
                return False
                
            board_data = self.boards[board_name]
            
            # Add image if not already in board
            if image.path not in board_data['images']:
                board_data['images'].append(image.path)
                board_data['modified'] = datetime.now().isoformat()
                
                # Save changes
                self.save_board(board_name, board_data)
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error adding to board {board_name}: {e}")
            return False
            
    def remove_from_board(self, board_name: str, image: Image) -> bool:
        """Remove an image from a board"""
        try:
            if board_name not in self.boards:
                return False
                
            board_data = self.boards[board_name]
            
            # Remove image if present
            if image.path in board_data['images']:
                board_data['images'].remove(image.path)
                board_data['modified'] = datetime.now().isoformat()
                
                # Save changes
                self.save_board(board_name, board_data)
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error removing from board {board_name}: {e}")
            return False
            
    def delete_board(self, name: str) -> bool:
        """Delete a board"""
        try:
            if name not in self.boards:
                return False
                
            # Remove board file
            board_path = self.get_board_path(name)
            if os.path.exists(board_path):
                os.remove(board_path)
                
            # Remove from memory
            del self.boards[name]
            return True
            
        except Exception as e:
            logger.error(f"Error deleting board {name}: {e}")
            return False

class BoardsPanel(QWidget):
    """Panel for managing image boards"""
    
    board_created = pyqtSignal(str)  # Emitted when board is created
    board_deleted = pyqtSignal(str)  # Emitted when board is deleted
    image_added = pyqtSignal(str, str)  # Emitted when image is added (board_name, image_path)
    
    def __init__(self, 
                 config: AppConfig,
                 image_loader_service: ImageLoaderService,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Store dependencies
        self.config = config
        self.image_loader = image_loader_service
        self.boards_manager = BoardsManager(config)
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Board controls
        controls = QHBoxLayout()
        
        # Create board button
        create_btn = QPushButton("Create Board")
        create_btn.clicked.connect(self.create_board)
        controls.addWidget(create_btn)
        
        # Delete board button
        delete_btn = QPushButton("Delete Board")
        delete_btn.clicked.connect(self.delete_board)
        controls.addWidget(delete_btn)
        
        layout.addLayout(controls)
        
        # Boards list
        self.boards_list = QListWidget()
        layout.addWidget(self.boards_list)
        
        # Update boards list
        self.update_boards_list()
        
        # Style
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QPushButton {
                background-color: #0078d4;
                border: none;
                border-radius: 3px;
                padding: 5px 15px;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #2b88d8;
            }
            QListWidget {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
            }
        """)
        
    def update_boards_list(self):
        """Update the boards list display"""
        self.boards_list.clear()
        for board_name in sorted(self.boards_manager.boards.keys()):
            self.boards_list.addItem(board_name)
            
    def create_board(self):
        """Create a new board"""
        name, ok = QInputDialog.getText(
            self, "Create Board", "Board name:"
        )
        if ok and name:
            if self.boards_manager.create_board(name):
                self.update_boards_list()
                self.board_created.emit(name)
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Could not create board. Name may be invalid or already exists."
                )
                
    def delete_board(self):
        """Delete selected board"""
        if current := self.boards_list.currentItem():
            board_name = current.text()
            
            # Confirm deletion
            reply = QMessageBox.question(
                self,
                "Delete Board",
                f"Are you sure you want to delete board '{board_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if self.boards_manager.delete_board(board_name):
                    self.update_boards_list()
                    self.board_deleted.emit(board_name)
                else:
                    QMessageBox.warning(
                        self,
                        "Error",
                        "Could not delete board."
                    )
                    
    def get_board_menu(self, image: Image) -> QMenu:
        """Get context menu for adding image to boards"""
        menu = QMenu("Add to Board", self)
        
        for board_name in sorted(self.boards_manager.boards.keys()):
            action = menu.addAction(board_name)
            action.setData((board_name, image))
            
        menu.triggered.connect(self.handle_menu_action)
        return menu
        
    def handle_menu_action(self, action):
        """Handle board menu action"""
        try:
            board_name, image = action.data()
            
            if self.boards_manager.add_to_board(board_name, image):
                self.image_added.emit(board_name, image.path)
                
        except Exception as e:
            logger.error(f"Error handling menu action: {e}")
            
    def add_to_board(self, board_name: str, image: Image) -> bool:
        """Add an image to a board"""
        try:
            if self.boards_manager.add_to_board(board_name, image):
                self.image_added.emit(board_name, image.path)
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error adding to board: {e}")
            return False 