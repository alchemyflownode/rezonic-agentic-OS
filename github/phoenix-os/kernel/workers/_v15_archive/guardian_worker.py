# workers/guardian_worker.py - Clean version with NO pkg_resources
import time
import logging
import platform
import os

# Try to import psutil, but don't fail if not available
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("⚠️ psutil not installed. Guardian worker will have limited functionality.")

class GuardianWorker:
    """System guardian worker - monitors and protects the system"""
    
    def __init__(self):
        self.name = "guardian_worker"
        self.health_checks = []
        self.last_check = 0
        self.check_interval = 30
        self.status = "healthy"
        self.alerts = []
    
    async def execute(self, task: str, **kwargs) -> dict:
        task_lower = task.lower()
        
        if task_lower == "status":
            return self._get_status()
        elif task_lower == "check":
            return await self._run_health_check()
        elif task_lower == "alerts":
            return {"alerts": self.alerts[-10:]}
        elif task_lower == "reset":
            self.alerts = []
            return {"success": True, "message": "Alerts cleared"}
        elif task_lower == "system":
            return self._get_system_info()
        
        return {"error": f"Unknown task: {task}", "success": False}
    
    def _get_status(self):
        return {
            "status": self.status,
            "last_check": self.last_check,
            "check_interval": self.check_interval,
            "alert_count": len(self.alerts),
            "healthy": self.status == "healthy"
        }
    
    def _get_system_info(self):
        info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "python_version": platform.python_version(),
            "worker": self.name,
            "status": self.status
        }
        
        if HAS_PSUTIL:
            try:
                info["cpu_percent"] = psutil.cpu_percent(interval=0.5)
                mem = psutil.virtual_memory()
                info["memory_percent"] = mem.percent
                info["memory_used_gb"] = round(mem.used / (1024**3), 1)
                info["memory_total_gb"] = round(mem.total / (1024**3), 1)
            except:
                pass
        
        return info
    
    async def _run_health_check(self):
        self.last_check = time.time()
        issues = []
        
        if HAS_PSUTIL:
            try:
                mem = psutil.virtual_memory()
                if mem.percent > 90:
                    issues.append(f"High memory usage: {mem.percent}%")
            except:
                pass
            
            try:
                cpu = psutil.cpu_percent(interval=1)
                if cpu > 80:
                    issues.append(f"High CPU usage: {cpu}%")
            except:
                pass
        
        # Check disk space
        try:
            import shutil
            disk = shutil.disk_usage("/")
            free_gb = disk.free / (1024**3)
            if free_gb < 10:
                issues.append(f"Low disk space: {free_gb:.1f}GB free")
        except:
            pass
        
        if issues:
            self.status = "degraded"
            for issue in issues:
                self.alerts.append({
                    "timestamp": time.time(),
                    "message": issue
                })
                print(f"[Guardian] ALERT: {issue}")
        else:
            self.status = "healthy"
        
        return {
            "success": True,
            "status": self.status,
            "issues": issues,
            "timestamp": self.last_check
        }
