"""
System Monitor Worker - PC health and performance monitoring
"""

import platform
import psutil
import time
import asyncio
from typing import Dict, Any, List
from datetime import datetime
from .base import BaseWorker


class SystemMonitorWorker(BaseWorker):
    """Monitor PC health and performance"""
    
    def __init__(self):
        super().__init__("system_monitor")
        self.os_type = platform.system()
        self.history = []
        self.max_history = 100
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute system monitoring operations"""
        task_lower = task.lower()
        
        # Get system info
        if "info" in task_lower or "status" in task_lower:
            return await self._get_system_info()
        
        # Get CPU info
        elif "cpu" in task_lower:
            return await self._get_cpu_info()
        
        # Get memory info
        elif "memory" in task_lower or "ram" in task_lower:
            return await self._get_memory_info()
        
        # Get disk info
        elif "disk" in task_lower or "drive" in task_lower:
            return await self._get_disk_info()
        
        # Get network info
        elif "network" in task_lower or "net" in task_lower:
            return await self._get_network_info()
        
        # Get process list
        elif "process" in task_lower:
            return await self._get_process_list()
        
        # Get performance history
        elif "history" in task_lower:
            return await self._get_history()
        
        return {"error": f"Unknown system operation: {task}", "success": False}
    
    async def _get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            # Record current stats
            stats = {
                "timestamp": time.time(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            }
            self.history.append(stats)
            if len(self.history) > self.max_history:
                self.history.pop(0)
            
            return {
                "success": True,
                "os": platform.system(),
                "os_version": platform.version(),
                "hostname": platform.node(),
                "processor": platform.processor(),
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
                "cpu": {
                    "cores": psutil.cpu_count(),
                    "physical_cores": psutil.cpu_count(logical=False),
                    "percent": stats["cpu_percent"],
                    "per_cpu": psutil.cpu_percent(interval=1, percpu=True)
                },
                "memory": {
                    "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                    "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
                    "used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
                    "percent": stats["memory_percent"]
                },
                "disk": {
                    "total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
                    "used_gb": round(psutil.disk_usage('/').used / (1024**3), 2),
                    "free_gb": round(psutil.disk_usage('/').free / (1024**3), 2),
                    "percent": stats["disk_percent"]
                },
                "uptime_seconds": time.time() - psutil.boot_time()
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _get_cpu_info(self) -> Dict[str, Any]:
        """Get CPU-specific information"""
        try:
            return {
                "success": True,
                "cores": psutil.cpu_count(),
                "physical_cores": psutil.cpu_count(logical=False),
                "percent": psutil.cpu_percent(interval=1),
                "per_cpu": psutil.cpu_percent(interval=1, percpu=True),
                "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                "stats": psutil.cpu_stats()._asdict(),
                "load_avg": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _get_memory_info(self) -> Dict[str, Any]:
        """Get memory information"""
        try:
            vm = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                "success": True,
                "virtual": {
                    "total_gb": round(vm.total / (1024**3), 2),
                    "available_gb": round(vm.available / (1024**3), 2),
                    "used_gb": round(vm.used / (1024**3), 2),
                    "percent": vm.percent
                },
                "swap": {
                    "total_gb": round(swap.total / (1024**3), 2),
                    "used_gb": round(swap.used / (1024**3), 2),
                    "free_gb": round(swap.free / (1024**3), 2),
                    "percent": swap.percent
                }
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _get_disk_info(self) -> Dict[str, Any]:
        """Get disk information"""
        try:
            disks = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disks.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "percent": usage.percent
                    })
                except:
                    continue
            
            return {
                "success": True,
                "disks": disks
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _get_network_info(self) -> Dict[str, Any]:
        """Get network information"""
        try:
            net_io = psutil.net_io_counters()
            net_connections = psutil.net_connections()
            
            return {
                "success": True,
                "io": {
                    "bytes_sent_gb": round(net_io.bytes_sent / (1024**3), 2),
                    "bytes_recv_gb": round(net_io.bytes_recv / (1024**3), 2),
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv
                },
                "connections": len(net_connections),
                "active_connections": len([c for c in net_connections if c.status == 'ESTABLISHED'])
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _get_process_list(self) -> Dict[str, Any]:
        """Get list of running processes"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except:
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            
            return {
                "success": True,
                "processes": processes[:30],
                "total": len(processes)
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _get_history(self) -> Dict[str, Any]:
        """Get performance history"""
        return {
            "success": True,
            "history": self.history[-20:],
            "total": len(self.history)
        }