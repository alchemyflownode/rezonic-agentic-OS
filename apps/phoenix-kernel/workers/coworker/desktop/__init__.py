"""
Desktop integration package for Phoenix Coworker
"""

from .presence import DesktopCoworker, FileAction, create_desktop_presence

__all__ = [
    "DesktopCoworker",
    "FileAction",
    "create_desktop_presence",
]
