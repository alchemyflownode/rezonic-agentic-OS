"""
Workers package for Phoenix Coworker
Complete worker registry for PC control and AI assistance
"""

from .base import BaseWorker
from .brain import BrainWorker
from .filesystem import FilesystemWorker
from .execution import ExecutionWorker
from .vision import VisionWorker
from .voice import VoiceWorker

# New PC Control Workers
from .file_manager import FileManagerWorker
from .app_control import AppControlWorker
from .clipboard_manager import ClipboardManagerWorker
from .browser_controller import BrowserControllerWorker
from .system_monitor import SystemMonitorWorker

__all__ = [
    # Core workers
    "BaseWorker",
    "BrainWorker",
    "FilesystemWorker",
    "ExecutionWorker",
    "VisionWorker",
    "VoiceWorker",
    
    # PC Control workers
    "FileManagerWorker",
    "AppControlWorker",
    "ClipboardManagerWorker",
    "BrowserControllerWorker",
    "SystemMonitorWorker",
]