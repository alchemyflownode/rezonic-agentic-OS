import asyncio
import threading
import pystray
from PIL import Image, ImageDraw
import keyboard
import logging
from .ui import CommandOverlay

logger = logging.getLogger("PHOENIX.DESKTOP")

class DesktopPresence:
    def __init__(self, kernel_client, loop):
        self.kernel_client = kernel_client
        self.loop = loop
        self.icon = None
        self.is_paused = False
        self.ui = CommandOverlay(kernel_client, loop)

    def create_icon_image(self):
        size = (64, 64)
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([8, 8, 56, 56], fill=(0, 229, 255, 255))
        draw.ellipse([16, 16, 48, 48], fill=(155, 114, 203, 255))
        draw.polygon([(32, 16), (24, 36), (36, 36), (28, 52), (40, 28), (28, 28)], fill=(255, 255, 255, 255))
        return img

    def show_status(self):
        status = "Paused" if self.is_paused else "Active"
        logger.info(f"Status: {status}")

    def quick_command(self):
        logger.info("Opening command overlay...")
        threading.Thread(target=self.ui.show, daemon=True).start()

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        status = "paused" if self.is_paused else "resumed"
        logger.info(f"Phoenix {status}")

    def exit_app(self):
        logger.info("Shutting down desktop presence...")
        if self.icon:
            self.icon.stop()
        keyboard.unhook_all()

    def setup_hotkeys(self):
        keyboard.add_hotkey('ctrl+shift+space', self.quick_command, suppress=False)
        keyboard.add_hotkey('ctrl+shift+p', self.toggle_pause, suppress=False)
        logger.info("Hotkeys registered: Ctrl+Shift+Space (command), Ctrl+Shift+P (pause)")

    def create_menu(self):
        return pystray.Menu(
            pystray.MenuItem("Status", self.show_status),
            pystray.MenuItem("Quick Command", self.quick_command),
            pystray.MenuItem("Pause/Resume", self.toggle_pause),
            pystray.MenuItem("─" * 10, None, enabled=False),
            pystray.MenuItem("Exit", self.exit_app),
        )

    def run(self):
        self.setup_hotkeys()
        self.icon = pystray.Icon("phoenix_coworker", self.create_icon_image(),
                                 "Phoenix OS - Personal Coworker", self.create_menu())
        threading.Thread(target=self.icon.run, daemon=True).start()
        logger.info("Desktop presence started (system tray + hotkeys)")

    def stop(self):
        if self.icon:
            self.icon.stop()
        keyboard.unhook_all()