import tkinter as tk
import asyncio
import threading
import logging

logger = logging.getLogger("PHOENIX.UI")

class CommandOverlay:
    def __init__(self, kernel_client, loop):
        self.kernel = kernel_client
        self.loop = loop
        self.root = None
        self.entry = None

    def show(self):
        if self.root:
            self.root.destroy()
        self.root = tk.Tk()
        self.root.title("Phoenix Command")
        self.root.geometry("500x120")
        self.root.configure(bg='#1e1e1e')
        self.root.eval('tk::PlaceWindow . center')
        self.root.overrideredirect(True)

        label = tk.Label(self.root, text="🦊 What would you like me to do?",
                         bg='#1e1e1e', fg='#00e5ff', font=("Segoe UI", 12))
        label.pack(pady=(20, 10))

        self.entry = tk.Entry(self.root, font=("Segoe UI", 14), bg='#2d2d2d', fg='white',
                              insertbackground='white', relief='flat', width=45)
        self.entry.pack(pady=(0, 15), padx=20)
        self.entry.focus_set()

        self.entry.bind('<Return>', self.submit)
        self.root.bind('<Escape>', lambda e: self.root.destroy())
        self.root.attributes('-topmost', True)

        self.root.mainloop()

    def submit(self, event):
        cmd = self.entry.get()
        if cmd:
            logger.info(f"Command: {cmd}")
            asyncio.run_coroutine_threadsafe(self.kernel.send_task(cmd), self.loop)
        self.root.destroy()
        self.root = None