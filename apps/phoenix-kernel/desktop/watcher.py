import asyncio
import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger("PHOENIX.WATCHER")

class PhoenixFileHandler(FileSystemEventHandler):
    def __init__(self, kernel_client):
        super().__init__()
        self.kernel = kernel_client
        self.watch_folders = [
            str(Path.home() / "Downloads"),
            str(Path.home() / "Documents" / "Notes"),
        ]
        self.ignore = ['*.tmp', '*.partial', '~$*']

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if any(path.match(p) for p in self.ignore):
            return
        time.sleep(0.5)
        if not path.exists():
            return

        ext = path.suffix.lower()
        if ext == '.pdf':
            asyncio.create_task(self.kernel.send_task(f"Summarize PDF: {event.src_path}"))
        elif ext in ['.zip', '.rar', '.7z']:
            asyncio.create_task(self.kernel.send_task(f"Extract archive: {event.src_path}"))
        elif ext in ['.txt', '.md']:
            asyncio.create_task(self.kernel.send_task(f"Index document: {event.src_path}"))
        elif ext in ['.py', '.js', '.ts']:
            asyncio.create_task(self.kernel.send_task(f"Analyze code: {event.src_path}"))

    def start(self):
        observer = Observer()
        for folder in self.watch_folders:
            p = Path(folder)
            if p.exists():
                observer.schedule(self, str(p), recursive=False)
                logger.info(f"Watching: {p}")
            else:
                logger.warning(f"Folder not found: {p}")
        observer.start()
        return observer

    def stop(self):
        logger.info("File watcher stopped")