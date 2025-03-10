"""Base menu class for application menus"""

from typing import Optional, Callable, Dict, Union
from ...shared.imports.core import Qt
from ...shared.imports.gui import QAction, QKeySequence, QActionGroup
from ...shared.imports.widgets import QMenu

import logging
logger = logging.getLogger(__name__)

class BaseMenu(QMenu):
    """Base class for application menus with common functionality"""
    
    def __init__(self, title: str, parent: Optional[QMenu] = None):
        """Initialize the base menu
        
        Args:
            title: Menu title
            parent: Parent widget/menu
        """
        super().__init__(title, parent)
        self.actions_map: Dict[str, QAction] = {}
        self.setup_actions()
        
    def setup_actions(self):
        """Setup menu actions - override in subclasses"""
        pass
        
    def add_action_with_shortcut(
        self,
        name: str,
        text: str,
        shortcut: Optional[Union[QKeySequence, str]] = None,
        callback: Optional[Callable] = None,
        checkable: bool = False,
        checked: bool = False,
        enabled: bool = True,
        parent: Optional[QMenu] = None
    ) -> QAction:
        """Add an action with optional shortcut and callback
        
        Args:
            name: Unique identifier for the action
            text: Display text for the action
            shortcut: Optional keyboard shortcut
            callback: Optional callback function
            checkable: Whether action can be checked/unchecked
            checked: Initial checked state if checkable
            enabled: Whether action is enabled
            parent: Optional parent menu (for submenus)
            
        Returns:
            Created QAction
        """
        action = QAction(text, self)
        
        if shortcut:
            action.setShortcut(shortcut)
        if callback:
            action.triggered.connect(callback)
        if checkable:
            action.setCheckable(True)
            action.setChecked(checked)
        
        action.setEnabled(enabled)
        
        # Add action to specified parent menu or self
        if parent:
            parent.addAction(action)
        else:
            self.addAction(action)
            
        self.actions_map[name] = action
        return action
        
    def add_menu(
        self,
        name: str,
        text: str,
        enabled: bool = True
    ) -> QMenu:
        """Add a submenu
        
        Args:
            name: Unique identifier for the menu
            text: Display text for the menu
            enabled: Whether menu is enabled
            
        Returns:
            Created QMenu
        """
        menu = QMenu(text, self)
        menu.setEnabled(enabled)
        self.addMenu(menu)
        self.actions_map[name] = menu.menuAction()
        
        return menu
        
    def add_separator(self):
        """Add a separator line to the menu"""
        self.addSeparator()
        
    def create_action_group(
        self,
        exclusive: bool = True
    ) -> QActionGroup:
        """Create an action group for mutually exclusive actions
        
        Args:
            exclusive: Whether actions are mutually exclusive
            
        Returns:
            Created QActionGroup
        """
        group = QActionGroup(self)
        group.setExclusive(exclusive)
        return group
        
    def get_action(self, name: str) -> Optional[QAction]:
        """Get action by name
        
        Args:
            name: Action identifier
            
        Returns:
            QAction if found, None otherwise
        """
        return self.actions_map.get(name) 