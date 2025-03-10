"""Metaclass utilities for Qt and ABC compatibility."""

from abc import ABC, ABCMeta
from PyQt6.QtCore import QObject

class QtABCMeta(type(QObject), ABCMeta):
    """Combined metaclass for QObject and ABC compatibility.
    
    This metaclass allows classes to inherit from both QObject and ABC
    without metaclass conflicts. It combines PyQt's QMetaClass with
    Python's ABCMeta.
    
    Usage:
        class MyClass(QObject, ABC, metaclass=QtABCMeta):
            pass
    """
    pass

def with_qt_abc_meta(cls):
    """Decorator to apply QtABCMeta to a class.
    
    Usage:
        @with_qt_abc_meta
        class MyClass(QObject, ABC):
            pass
    """
    return QtABCMeta(cls.__name__, cls.__bases__, dict(cls.__dict__))

class QtViewMixin:
    """Mixin class for Qt views with ABC support.
    
    This mixin provides common functionality for Qt views and handles
    metaclass compatibility.
    
    Usage:
        class MyView(QWidget, QtViewMixin, ABC, metaclass=QtABCMeta):
            pass
    """
    
    def __init_subclass__(cls, **kwargs):
        """Ensure proper metaclass usage in subclasses."""
        if not isinstance(cls, QtABCMeta):
            raise TypeError(
                f"Class {cls.__name__} must use QtABCMeta metaclass. "
                "Use the @with_qt_abc_meta decorator or specify metaclass=QtABCMeta"
            )

__all__ = ['QtABCMeta', 'with_qt_abc_meta', 'QtViewMixin'] 