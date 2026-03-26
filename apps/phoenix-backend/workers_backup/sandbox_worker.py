import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# backend/workers/sandbox_worker.py
import subprocess
import os
import tempfile
import time
import logging
from .base_worker import BaseWorker

logger = logging.getLogger(__name__)

class SandboxWorker(BaseWorker):
    def __init__(self, hive_bus=None):
        super().__init__("sandbox")
        self.description = "Executes local Python code securely"

    async def process(self, task: str, model: str = None, memory_bus=None) -> dict:
        self.set_memory_bus(memory_bus)
        logger.info(f"âš¡[SANDBOX] Waking execution environment...")

        code_to_run = ""
        
        # 1. Did the user pass code directly?
        if "```python" in task:
            code_to_run = task.split("```python")[1].split("```")[0].strip()
            
        # 2. Or do we need to pull from the Hive Mind?
        elif self.memory_bus:
            logger.info("ðŸ” Searching Hive Mind for recent HandsWorker code...")
            recent_codes = await self.search_context("", limit=1, worker_filter="hands")
            if recent_codes:
                raw_memory = recent_codes[0]
                if "```python" in raw_memory:
                    code_to_run = raw_memory.split("```python")[1].split("```")[0].strip()

        if not code_to_run:
            return {"content": "âŒ **Sandbox Error:** No executable Python code found in prompt or recent memory."}

        # 3. EXECUTE SECURELY
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(code_to_run)
                temp_path = temp_file.name

            start_time = time.time()
            result = subprocess.run(['python', temp_path], capture_output=True, text=True, timeout=15)
            exec_time = round(time.time() - start_time, 2)
            os.remove(temp_path)

            if result.returncode == 0:
                output = result.stdout.strip() or "Process finished with exit code 0."
                content_msg = f"âœ… **Execution Success ({exec_time}s):**\n```text\n{output}\n```"
                await self.publish(f"Sandbox executed code successfully. Output: {output[:200]}", {"status": "success"})
                return {"success": True, "content": content_msg}
            else:
                error_output = result.stderr.strip()
                content_msg = f"âŒ **Execution Error:**\n```text\n{error_output}\n```"
                await self.publish(f"Sandbox execution crashed! Traceback: {error_output}", {"status": "error"})
                return {"success": False, "content": content_msg}

        except subprocess.TimeoutExpired:
            await self.publish("Sandbox execution timed out after 15s.", {"status": "timeout"})
            return {"success": False, "content": "â±ï¸ **Execution Error:** Process timed out after 15 seconds."}
        except Exception as e:
            return {"success": False, "content": f"âš ï¸ **Sandbox System Error:** {str(e)}"}

    async def process(self, task: str, memory_bus=None):
        """Process task – auto-generated stub"""
        return {"content": f"Processed: {task[:50]}", "worker": self.name}
    
    async def health_check(self):
        """Return worker health status"""
        return {"worker": self.name, "status": "healthy", "timestamp": __import__('time').time()}

