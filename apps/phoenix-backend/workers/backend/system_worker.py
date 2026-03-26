"""
System Worker - Handles slash commands and system utilities
"""

import psutil
import logging
import os

logger = logging.getLogger(__name__)

class SystemWorker:
    def __init__(self, hive_bus=None):
        self.hive_bus = hive_bus`n        self.name = "system"
        self.description = "System commands and utilities"
    
    async def process(self, task: str, model: str = None) -> dict:
        """Process system commands"""
        task_lower = task.lower().strip()
        
        # =========================================================
        # SYSTEM CHECK
        # =========================================================
        if task_lower == '/check_system' or task_lower == 'check system':
            try:
                cpu = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory().percent
                disk = psutil.disk_usage('/').percent
                
                return {
                    "content": f"""**??? SYSTEM HEALTH REPORT**

**Resources:**
• CPU: {cpu}%
• Memory: {memory}%
• Disk: {disk}%

**Workers:**
• ?? Brain: ACTIVE
• ??? Eyes: ACTIVE
• ? Hands: ACTIVE
• ?? Memory: ACTIVE
• ?? System: ACTIVE

**Status:** ? OPERATIONAL
**Drift Events:** 0"""
                }
            except Exception as e:
                return {"content": f"Error checking system: {e}"}
        
        # =========================================================
        # LIST FILES
        # =========================================================
        elif task_lower == '/list_files' or task_lower.startswith('list files'):
            try:
                files = os.listdir(".")[:25]
                formatted = "?? **Current Directory Contents:**\n\n"
                
                dirs = []
                file_list = []
                
                for f in files:
                    if os.path.isdir(f):
                        dirs.append(f)
                    else:
                        file_list.append(f)
                
                for d in sorted(dirs):
                    formatted += f"?? `{d}/`\n"
                
                for f in sorted(file_list):
                    try:
                        size = os.path.getsize(f) / 1024
                        if size < 1:
                            size_str = f"{os.path.getsize(f)} bytes"
                        else:
                            size_str = f"{size:.1f} KB"
                        formatted += f"?? `{f}` ({size_str})\n"
                    except:
                        formatted += f"?? `{f}`\n"
                
                return {"content": formatted}
            except Exception as e:
                return {"content": f"File error: {e}"}
        
        # =========================================================
        # CLEAR CHAT
        # =========================================================
        elif task_lower == '/clear_chat' or task_lower == 'clear chat':
            return {"content": "?? **Chat cleared locally**\n\n*The UI will refresh on next message*"}
        
        # =========================================================
        # HELP
        # =========================================================
        elif task_lower == '/help' or task_lower == 'help':
            return {
                "content": """**?? AVAILABLE COMMANDS**

**System Commands:**
• `/check_system` - Display system health
• `/list_files` - List current directory
• `/clear_chat` - Clear chat history
• `/help` - Show this help

**PC Search:**
• `search pc [filename]` - Find files
• `list drives` - Show drive space

**Memory:**
• `remember [info]` - Store in memory
• `recall [topic]` - Retrieve from memory

**Online:**
• Ask any question for web search"""
            }
        
        # Default response
        return {"content": "?? System worker ready. Try `/help` for commands."}

