import subprocess
import platform
import psutil
import asyncio
from typing import Dict, Any

class SystemControlWorker:
    """Control your PC - apps, processes, system info"""
    
    def __init__(self):
        self.name = "system_control"
        self.os = platform.system()
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        task_lower = task.lower()
        
        # Get system info
        if "info" in task_lower or "status" in task_lower:
            return await self._get_system_info()
        
        # Open application
        elif "open" in task_lower or "launch" in task_lower:
            app = kwargs.get("app", task)
            return await self._open_app(app)
        
        # List running processes
        elif "process" in task_lower or "running" in task_lower:
            return await self._list_processes()
        
        # Kill process
        elif "kill" in task_lower or "stop" in task_lower:
            name = kwargs.get("name", "")
            return await self._kill_process(name)
        
        # Run command
        elif "run" in task_lower or "execute" in task_lower:
            command = kwargs.get("command", "")
            return await self._run_command(command)
        
        return {"error": f"Unknown system operation: {task}", "success": False}
    
    async def _get_system_info(self) -> Dict[str, Any]:
        return {
            "success": True,
            "os": self.os,
            "hostname": platform.node(),
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
                "free_gb": round(psutil.disk_usage('/').free / (1024**3), 2),
                "percent": psutil.disk_usage('/').percent
            },
            "boot_time": psutil.boot_time()
        }
    
    async def _open_app(self, app: str) -> Dict[str, Any]:
        try:
            if self.os == "Windows":
                # Windows: use start command
                cmd = f"start {app}"
                subprocess.Popen(cmd, shell=True)
            elif self.os == "Darwin":  # macOS
                subprocess.Popen(["open", "-a", app])
            else:  # Linux
                subprocess.Popen([app])
            
            return {"success": True, "message": f"Opened: {app}"}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _list_processes(self) -> Dict[str, Any]:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except:
                pass
        
        return {
            "success": True,
            "processes": sorted(processes, key=lambda x: x.get('cpu_percent', 0), reverse=True)[:20],
            "count": len(processes)
        }
    
    async def _kill_process(self, name: str) -> Dict[str, Any]:
        killed = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if name.lower() in proc.info['name'].lower():
                    proc.kill()
                    killed.append(proc.info['name'])
            except:
                pass
        
        if killed:
            return {"success": True, "message": f"Killed: {', '.join(killed)}"}
        return {"error": f"No process found: {name}", "success": False}
    
    async def _run_command(self, command: str) -> Dict[str, Any]:
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            return {
                "success": True,
                "command": command,
                "returncode": process.returncode,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else ""
            }
        except Exception as e:
            return {"error": str(e), "success": False}