"""View menu for the application"""

import logging
from typing import Callable
from ...shared.imports.core import Qt
from ...shared.imports.gui import QKeySequence
from .base_menu import BaseMenu

logger = logging.getLogger(__name__)

class ViewMenu(BaseMenu):
    """View menu with view options"""
    
    def __init__(self, parent=None):
        super().__init__("&View", parent)
        
    def setup_actions(self):
        """Setup menu actions"""
        # Panel visibility actions
        self.add_action_with_shortcut(
            name="show_sidebar",
            text="Show &Sidebar",
            checkable=True,
            checked=True
        )
        
        self.add_action_with_shortcut(
            name="show_toolbar",
            text="Show &Toolbar",
            checkable=True,
            checked=True
        )
        
        self.add_action_with_shortcut(
            name="show_statusbar",
            text="Show Status&bar",
            checkable=True,
            checked=True
        )
        
        self.add_separator()
        
        # Panel actions
        self.panels_menu = self.add_menu(
            name="panels",
            text="Panels"
        )
        
        self.add_action_with_shortcut(
            name="show_metadata",
            text="&Metadata Panel",
            checkable=True,
            parent=self.panels_menu
        )
        
        self.add_action_with_shortcut(
            name="show_tags",
            text="&Tags Panel",
            checkable=True,
            parent=self.panels_menu
        )
        
        self.add_action_with_shortcut(
            name="show_rating",
            text="&Rating Panel",
            checkable=True,
            parent=self.panels_menu
        )
        
    def set_sidebar_callback(self, callback: Callable[[bool], None]):
        """Set callback for sidebar visibility toggle"""
        if action := self.get_action("show_sidebar"):
            action.triggered.connect(callback)
            
    def set_toolbar_callback(self, callback: Callable[[bool], None]):
        """Set callback for toolbar visibility toggle"""
        if action := self.get_action("show_toolbar"):
            action.triggered.connect(callback)
            
    def set_statusbar_callback(self, callback: Callable[[bool], None]):
        """Set callback for statusbar visibility toggle"""
        if action := self.get_action("show_statusbar"):
            action.triggered.connect(callback)
            
    def set_metadata_panel_callback(self, callback: Callable[[bool], None]):
        """Set callback for metadata panel visibility toggle"""
        if action := self.get_action("show_metadata"):
            action.triggered.connect(callback)
            
    def set_tags_panel_callback(self, callback: Callable[[bool], None]):
        """Set callback for tags panel visibility toggle"""
        if action := self.get_action("show_tags"):
            action.triggered.connect(callback)
            
    def set_rating_panel_callback(self, callback: Callable[[bool], None]):
        """Set callback for rating panel visibility toggle"""
        if action := self.get_action("show_rating"):
            action.triggered.connect(callback) 