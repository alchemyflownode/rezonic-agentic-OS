"""
Desktop Presence for Phoenix Coworker

Provides:
- System tray icon and menu
- Global hotkeys for quick access
- File system watching for proactive behavior
- Desktop overlay for quick commands
"""

import os
import sys
import asyncio
import threading
from pathlib import Path
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Platform detection
IS_WINDOWS = sys.platform == 'win32'
IS_MACOS = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')

# Optional imports with graceful degradation
try:
    import pystray
    from PIL import Image, ImageDraw
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


class FileAction(Enum):
    """Possible actions for new files"""
    ASK = "ask"           # Ask user what to do
    AUTO_ORGANIZE = "auto_organize"  # Automatically organize
    SUMMARIZE = "summarize"  # Summarize if document
    IGNORE = "ignore"     # Do nothing


@dataclass
class WatcherConfig:
    """Configuration for a file watcher"""
    path: Path
    patterns: List[str]  # e.g., ["*.pdf", "*.zip"]
    action: FileAction
    destination: Optional[Path] = None


class DesktopOverlay:
    """
    Quick command overlay UI.
    
    Shows a simple overlay when hotkey is pressed.
    Platform-specific implementations.
    """
    
    def __init__(self, on_command: Callable[[str], None]):
        self.on_command = on_command
        self.visible = False
        self._window = None
    
    def show(self, prompt: str = "What would you like me to do?"):
        """Show the overlay"""
        self.visible = True
        
        # Simple terminal-based overlay for now
        # Can be replaced with tkinter/PyQt for GUI
        print(f"\n{'='*50}")
        print(f"  🐦 Phoenix Coworker")
        print(f"{'='*50}")
        print(f"  {prompt}")
        print(f"  (Type your command or 'cancel' to close)")
        print(f"{'='*50}")
        
        # In a real implementation, this would show a GUI overlay
        # For now, we'll use a simple input
        try:
            command = input("> ").strip()
            if command and command.lower() != 'cancel':
                self.on_command(command)
        except (EOFError, KeyboardInterrupt):
            pass
        finally:
            self.hide()
    
    def hide(self):
        """Hide the overlay"""
        self.visible = False
        print("  (Overlay closed)\n")


class FileWatcherHandler(FileSystemEventHandler):
    """Handler for file system events"""
    
    def __init__(
        self,
        config: WatcherConfig,
        on_file_event: Callable[[Path, str], None]
    ):
        self.config = config
        self.on_file_event = on_file_event
        self.seen_files: set = set()
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Check if matches patterns
        if not self._matches_pattern(file_path):
            return
        
        # Debounce - avoid duplicate events
        file_id = f"{file_path}:{file_path.stat().st_mtime}"
        if file_id in self.seen_files:
            return
        self.seen_files.add(file_id)
        
        # Limit seen files set size
        if len(self.seen_files) > 1000:
            self.seen_files = set(list(self.seen_files)[-500:])
        
        self.on_file_event(file_path, "created")
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        if not self._matches_pattern(file_path):
            return
        
        self.on_file_event(file_path, "modified")
    
    def _matches_pattern(self, file_path: Path) -> bool:
        """Check if file matches configured patterns"""
        if not self.config.patterns:
            return True
        
        import fnmatch
        for pattern in self.config.patterns:
            if fnmatch.fnmatch(file_path.name, pattern):
                return True
        return False


class DesktopCoworker:
    """
    Desktop integration for Phoenix Coworker.
    
    Provides system tray presence, global hotkeys, and file watching
    for proactive desktop assistance.
    """
    
    DEFAULT_HOTKEY = "ctrl+shift+space"
    
    def __init__(
        self,
        kernel: Any,  # Phoenix kernel reference
        hotkey: str = None,
        data_dir: Path = None
    ):
        self.kernel = kernel
        self.hotkey = hotkey or self.DEFAULT_HOTKEY
        self.data_dir = data_dir or Path.home() / ".phoenix"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Components
        self.icon: Optional[pystray.Icon] = None
        self.overlay = DesktopOverlay(self._on_overlay_command)
        self.observer: Optional[Observer] = None
        self.watchers: Dict[Path, FileWatcherHandler] = {}
        
        # State
        self.paused = False
        self._running = False
        self._hotkey_handler = None
        
        # Callbacks
        self.on_file_created: Optional[Callable[[Path], None]] = None
        self.on_hotkey_pressed: Optional[Callable[[], None]] = None
        
        print(f"✓ DesktopCoworker initialized (hotkey: {self.hotkey})")
    
    def _create_icon_image(self) -> "Image.Image":
        """Create the system tray icon"""
        # Create a simple Phoenix icon (orange bird-like shape)
        width = 64
        height = 64
        
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        
        # Draw a simple phoenix-like shape (circle with flame colors)
        # Outer circle (orange)
        dc.ellipse([4, 4, 60, 60], fill=(255, 140, 0, 255))
        # Inner circle (yellow)
        dc.ellipse([16, 16, 48, 48], fill=(255, 215, 0, 255))
        # Center dot (red)
        dc.ellipse([26, 26, 38, 38], fill=(220, 20, 60, 255))
        
        return image
    
    def _create_menu(self) -> "pystray.Menu":
        """Create the system tray menu"""
        return pystray.Menu(
            pystray.MenuItem(
                lambda text: f"Status: {'Paused' if self.paused else 'Active'}",
                lambda: None,
                enabled=False
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Quick Command",
                self._on_quick_command
            ),
            pystray.MenuItem(
                "Show Recent Activity",
                self._on_show_activity
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                lambda text: "Resume" if self.paused else "Pause",
                self._on_toggle_pause
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Exit",
                self._on_exit
            )
        )
    
    def _on_quick_command(self):
        """Handle quick command menu item"""
        if not self.paused:
            # Show overlay in a separate thread to not block tray
            threading.Thread(target=self.overlay.show, daemon=True).start()
    
    def _on_show_activity(self):
        """Show recent activity"""
        if self.kernel and hasattr(self.kernel, 'get_recent_activity'):
            activity = self.kernel.get_recent_activity()
            print("\n--- Recent Activity ---")
            for item in activity[-10:]:
                print(f"  {item}")
        else:
            print("\n(No activity tracking available)")
    
    def _on_toggle_pause(self):
        """Toggle pause/resume"""
        self.paused = not self.paused
        status = "paused" if self.paused else "resumed"
        print(f"Phoenix coworker {status}")
        
        if self.icon:
            self.icon.update_menu()
    
    def _on_exit(self):
        """Handle exit menu item"""
        print("Shutting down Phoenix coworker...")
        self.stop()
        if self.icon:
            self.icon.stop()
    
    def _on_overlay_command(self, command: str):
        """Handle command from overlay"""
        if self.kernel and hasattr(self.kernel, 'execute'):
            asyncio.create_task(self.kernel.execute(command))
        else:
            print(f"Would execute: {command}")
    
    def _on_hotkey(self):
        """Handle global hotkey press"""
        if self.paused:
            return
        
        if self.on_hotkey_pressed:
            self.on_hotkey_pressed()
        else:
            self._on_quick_command()
    
    def _on_file_event(self, file_path: Path, event_type: str):
        """Handle file system event"""
        if self.paused:
            return
        
        print(f"📁 File {event_type}: {file_path.name}")
        
        if self.on_file_created:
            self.on_file_created(file_path)
        elif self.kernel and hasattr(self.kernel, 'handle_file_event'):
            asyncio.create_task(
                self.kernel.handle_file_event(file_path, event_type)
            )
        else:
            # Default behavior: proactive suggestions
            self._proactive_file_suggestion(file_path)
    
    def _proactive_file_suggestion(self, file_path: Path):
        """Generate proactive suggestion for new file"""
        suffix = file_path.suffix.lower()
        
        suggestions = {
            '.pdf': f"I see you downloaded '{file_path.name}'. Would you like me to summarize it?",
            '.zip': f"I see you downloaded '{file_path.name}'. Would you like me to extract it?",
            '.jpg': f"I see you downloaded '{file_path.name}'. Would you like me to organize it into Photos?",
            '.png': f"I see you downloaded '{file_path.name}'. Would you like me to organize it into Photos?",
            '.mp4': f"I see you downloaded '{file_path.name}'. Would you like me to move it to Videos?",
            '.exe': f"I see you downloaded '{file_path.name}'. This is an installer - would you like me to run it?",
            '.msi': f"I see you downloaded '{file_path.name}'. This is an installer - would you like me to run it?",
        }
        
        suggestion = suggestions.get(suffix)
        if suggestion:
            print(f"💡 {suggestion}")
            # In a real implementation, this would show a notification
            # For now, we just print the suggestion
    
    def setup_hotkey(self):
        """Setup global hotkey"""
        if not KEYBOARD_AVAILABLE:
            print("⚠ keyboard module not available. Hotkeys disabled.")
            print("  Install with: pip install keyboard")
            return False
        
        try:
            keyboard.add_hotkey(self.hotkey, self._on_hotkey)
            print(f"✓ Hotkey '{self.hotkey}' registered")
            return True
        except Exception as e:
            print(f"⚠ Could not register hotkey: {e}")
            return False
    
    def setup_tray(self):
        """Setup system tray icon"""
        if not PYSTRAY_AVAILABLE:
            print("⚠ pystray not available. System tray disabled.")
            print("  Install with: pip install pystray Pillow")
            return False
        
        try:
            self.icon = pystray.Icon(
                "phoenix",
                icon=self._create_icon_image(),
                title="Phoenix Coworker",
                menu=self._create_menu()
            )
            print("✓ System tray icon created")
            return True
        except Exception as e:
            print(f"⚠ Could not create tray icon: {e}")
            return False
    
    def add_watcher(
        self,
        path: Path,
        patterns: List[str] = None,
        action: FileAction = FileAction.ASK,
        destination: Path = None
    ):
        """Add a file system watcher"""
        if not WATCHDOG_AVAILABLE:
            print("⚠ watchdog not available. File watching disabled.")
            print("  Install with: pip install watchdog")
            return False
        
        path = Path(path).expanduser().resolve()
        
        if not path.exists():
            print(f"⚠ Watch path does not exist: {path}")
            return False
        
        config = WatcherConfig(
            path=path,
            patterns=patterns or ["*"],
            action=action,
            destination=destination
        )
        
        handler = FileWatcherHandler(config, self._on_file_event)
        self.watchers[path] = handler
        
        if self.observer:
            self.observer.schedule(handler, str(path), recursive=False)
            print(f"✓ Watching {path} for {patterns or 'all files'}")
        
        return True
    
    def setup_watchers(self):
        """Setup default file watchers"""
        if not WATCHDOG_AVAILABLE:
            return False
        
        self.observer = Observer()
        
        # Add default watchers
        default_watchers = [
            # Downloads folder
            (Path.home() / "Downloads", ["*.pdf", "*.zip", "*.jpg", "*.png"]),
            # Documents/Notes
            (Path.home() / "Documents" / "Notes", ["*.md", "*.txt"]),
        ]
        
        for path, patterns in default_watchers:
            if path.exists():
                self.add_watcher(path, patterns)
        
        return True
    
    def start(self):
        """Start the desktop integration"""
        self._running = True
        
        # Setup components
        self.setup_hotkey()
        self.setup_tray()
        self.setup_watchers()
        
        # Start file observer
        if self.observer:
            self.observer.start()
        
        # Start system tray (blocks)
        if self.icon:
            print("\n🐦 Phoenix Coworker is running!")
            print(f"   Press {self.hotkey} for quick command")
            print("   Right-click tray icon for menu")
            print()
            
            # Run tray icon in separate thread so we can do other things
            tray_thread = threading.Thread(target=self.icon.run, daemon=True)
            tray_thread.start()
        else:
            print("\n🐦 Phoenix Coworker is running (no tray icon)")
            print(f"   Press {self.hotkey} for quick command")
            print()
        
        return self._running
    
    def stop(self):
        """Stop the desktop integration"""
        self._running = False
        
        # Stop hotkey
        if KEYBOARD_AVAILABLE:
            try:
                keyboard.remove_hotkey(self.hotkey)
            except:
                pass
        
        # Stop file observer
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        # Stop tray icon
        if self.icon:
            self.icon.stop()
        
        print("Desktop coworker stopped")
    
    def run(self):
        """Run the desktop coworker (blocking)"""
        self.start()
        
        try:
            while self._running:
                asyncio.sleep(0.1)
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        finally:
            self.stop()


# Convenience function
def create_desktop_presence(
    kernel: Any,
    hotkey: str = None,
    watch_downloads: bool = True,
    watch_notes: bool = True
) -> DesktopCoworker:
    """Create and configure a desktop presence"""
    desktop = DesktopCoworker(kernel, hotkey)
    
    if watch_downloads:
        downloads = Path.home() / "Downloads"
        if downloads.exists():
            desktop.add_watcher(
                downloads,
                patterns=["*.pdf", "*.zip", "*.jpg", "*.png", "*.mp4"],
                action=FileAction.ASK
            )
    
    if watch_notes:
        notes = Path.home() / "Documents" / "Notes"
        if notes.exists():
            desktop.add_watcher(
                notes,
                patterns=["*.md", "*.txt"],
                action=FileAction.AUTO_ORGANIZE
            )
    
    return desktop


async def demo():
    """Demo the desktop presence"""
    print("\n" + "="*50)
    print("  Phoenix Coworker - Desktop Presence Demo")
    print("="*50 + "\n")
    
    # Mock kernel
    class MockKernel:
        async def execute(self, command: str):
            print(f"[Kernel] Would execute: {command}")
        
        def get_recent_activity(self):
            return [
                "10:30 - Organized Downloads folder",
                "10:25 - Summarized quarterly_report.pdf",
                "10:15 - Checked email",
            ]
        
        async def handle_file_event(self, path: Path, event_type: str):
            print(f"[Kernel] File event: {path} ({event_type})")
    
    kernel = MockKernel()
    desktop = DesktopCoworker(kernel)
    
    # Add test watchers
    desktop.add_watcher(
        Path.home() / "Downloads",
        patterns=["*.pdf"],
        action=FileAction.ASK
    )
    
    # Start (non-blocking for demo)
    desktop.setup_hotkey()
    desktop.setup_tray()
    desktop.setup_watchers()
    
    if desktop.observer:
        desktop.observer.start()
    
    print("\nDemo running. Press Ctrl+C to exit.")
    print("Try pressing Ctrl+Shift+Space for quick command\n")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        desktop.stop()


if __name__ == "__main__":
    asyncio.run(demo())
