"""
PC Monitor Worker - Tracks system resources and processes
"""

import psutil
import os
import platform
import subprocess
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class PCMonitorWorker(BaseWorker):
    """
    Monitors PC resources: CPU, RAM, disk, network, processes
    """
    
    def __init__(self, hive_bus=None, kernel_memory=None):
        super().__init__("pc_monitor", hive_bus, kernel_memory)
        self.thresholds = {
            'cpu_percent': 80,      # Alert if CPU > 80%
            'ram_percent': 85,       # Alert if RAM > 85%
            'disk_percent': 90,      # Alert if disk > 90%
            'network_mbps': 100,     # Alert if network > 100 Mbps
            'process_count': 200,    # Alert if too many processes
        }
        self.history = []
        self.max_history = 1000
        self.last_alert = {}
        logger.info("  📊 PCMonitorWorker initialized")
    
    async def process(self, task: str) -> str:
        """Process monitoring commands"""
        task_lower = task.lower()
        
        if '/pc status' in task or '/system status' in task:
            return await self._get_full_status()
        
        elif '/pc cpu' in task:
            return await self._get_cpu_info()
        
        elif '/pc ram' in task or '/pc memory' in task:
            return await self._get_ram_info()
        
        elif '/pc disk' in task:
            return await self._get_disk_info()
        
        elif '/pc network' in task:
            return await self._get_network_info()
        
        elif '/pc processes' in task:
            return await self._get_process_list()
        
        elif '/pc top' in task:
            count = 5
            if len(task.split()) > 2:
                try:
                    count = int(task.split()[2])
                except:
                    pass
            return await self._get_top_processes(count)
        
        elif '/pc alerts' in task:
            return self._get_alert_history()
        
        elif '/pc thresholds' in task:
            return self._get_thresholds()
        
        return "📊 PC Monitor ready. Try /pc status, /pc cpu, /pc ram, /pc processes"
    
    async def _get_full_status(self) -> str:
        """Get complete system status"""
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net = psutil.net_io_counters()
        processes = len(psutil.pids())
        
        # Calculate network speed (approximate)
        net_mbps = (net.bytes_sent + net.bytes_recv) / 1024 / 1024
        
        status = f"""📊 **SYSTEM STATUS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🖥️ CPU: {cpu}% {self._get_status_icon(cpu, 'cpu')}
💾 RAM: {ram.percent}% ({self._format_bytes(ram.used)}/{self._format_bytes(ram.total)})
💽 DISK: {disk.percent}% ({self._format_bytes(disk.used)}/{self._format_bytes(disk.total)})
🌐 NETWORK: {net_mbps:.1f} MB/s
⚙️ PROCESSES: {processes}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OS: {platform.system()} {platform.release()}
HOST: {platform.node()}
UPTIME: {self._format_uptime(time.time() - psutil.boot_time())}
"""
        
        # Check for alerts
        alerts = []
        if cpu > self.thresholds['cpu_percent']:
            alerts.append(f"⚠️ High CPU: {cpu}%")
        if ram.percent > self.thresholds['ram_percent']:
            alerts.append(f"⚠️ High RAM: {ram.percent}%")
        if disk.percent > self.thresholds['disk_percent']:
            alerts.append(f"⚠️ Low disk space: {100-disk.percent}% free")
        if processes > self.thresholds['process_count']:
            alerts.append(f"⚠️ Many processes: {processes}")
        
        if alerts:
            status += "\n🚨 **ALERTS**\n" + "\n".join(alerts)
            # Store alert
            self._store_alert('system', alerts)
        
        return status
    
    async def _get_cpu_info(self) -> str:
        """Get detailed CPU info"""
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        cpu_freq = psutil.cpu_freq()
        
        info = f"""🖥️ **CPU DETAILS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Usage: {psutil.cpu_percent()}%
Per Core: {', '.join([f'{p}%' for p in cpu_percent])}
Frequency: {cpu_freq.current:.0f} MHz
Cores: {psutil.cpu_count(logical=True)} logical, {psutil.cpu_count(logical=False)} physical
"""
        
        # Check for high usage
        high_cores = [i for i, p in enumerate(cpu_percent) if p > self.thresholds['cpu_percent']]
        if high_cores:
            info += f"\n⚠️ High usage on cores: {', '.join([str(i) for i in high_cores])}"
            self._store_alert('cpu', f"High CPU on cores {high_cores}")
        
        return info
    
    async def _get_ram_info(self) -> str:
        """Get detailed RAM info"""
        ram = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        info = f"""💾 **MEMORY DETAILS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RAM Usage: {ram.percent}%
Total: {self._format_bytes(ram.total)}
Used: {self._format_bytes(ram.used)}
Free: {self._format_bytes(ram.available)}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SWAP: {swap.percent}% ({self._format_bytes(swap.used)}/{self._format_bytes(swap.total)})
"""
        
        if ram.percent > self.thresholds['ram_percent']:
            info += f"\n⚠️ High RAM usage!"
            self._store_alert('ram', f"High RAM: {ram.percent}%")
        
        return info
    
    async def _get_disk_info(self) -> str:
        """Get detailed disk info"""
        partitions = psutil.disk_partitions()
        info = "💽 **DISK DETAILS**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                info += f"\n📁 {partition.device} mounted at {partition.mountpoint}\n"
                info += f"  Usage: {usage.percent}% ({self._format_bytes(usage.used)}/{self._format_bytes(usage.total)})\n"
                info += f"  Free: {self._format_bytes(usage.free)}\n"
                
                if usage.percent > self.thresholds['disk_percent']:
                    info += f"  ⚠️ Low disk space!\n"
                    self._store_alert('disk', f"Low disk on {partition.mountpoint}: {usage.percent}%")
            
            except PermissionError:
                continue
        
        return info
    
    async def _get_network_info(self) -> str:
        """Get network statistics"""
        net = psutil.net_io_counters()
        connections = psutil.net_connections()
        
        # Count connections by status
        status_counts = {}
        for conn in connections:
            status = conn.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        info = f"""🌐 **NETWORK DETAILS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Bytes Sent: {self._format_bytes(net.bytes_sent)}
Bytes Received: {self._format_bytes(net.bytes_recv)}
Packets Sent: {net.packets_sent}
Packets Received: {net.packets_recv}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Active Connections: {len(connections)}
  • ESTABLISHED: {status_counts.get('ESTABLISHED', 0)}
  • LISTEN: {status_counts.get('LISTEN', 0)}
  • TIME_WAIT: {status_counts.get('TIME_WAIT', 0)}
  • CLOSE_WAIT: {status_counts.get('CLOSE_WAIT', 0)}
"""
        
        # Check for suspicious connections
        suspicious = []
        for conn in connections:
            if conn.status == 'ESTABLISHED' and conn.raddr:
                # Check for known bad ports
                if conn.raddr.port in [4444, 1337, 6667]:  # Common backdoor ports
                    suspicious.append(f"{conn.raddr.ip}:{conn.raddr.port}")
        
        if suspicious:
            info += f"\n🚨 Suspicious connections: {', '.join(suspicious)}"
            self._store_alert('network', f"Suspicious connections detected", severity='high')
        
        return info
    
    async def _get_process_list(self) -> str:
        """Get list of running processes"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by CPU usage
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        info = "⚙️ **TOP PROCESSES BY CPU**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for proc in processes[:10]:
            info += f"  • {proc['name']:<20} CPU: {proc['cpu_percent']:.1f}%  MEM: {proc['memory_percent']:.1f}%\n"
        
        return info
    
    async def _get_top_processes(self, count: int = 5) -> str:
        """Get top processes by resource usage"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'create_time']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # CPU top
        cpu_top = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:count]
        # Memory top
        mem_top = sorted(processes, key=lambda x: x['memory_percent'], reverse=True)[:count]
        
        info = f"⚙️ **TOP {count} PROCESSES**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        info += "\n🔥 By CPU:\n"
        for proc in cpu_top:
            info += f"  • {proc['name']:<20} {proc['cpu_percent']:.1f}%\n"
        
        info += "\n💾 By Memory:\n"
        for proc in mem_top:
            info += f"  • {proc['name']:<20} {proc['memory_percent']:.1f}%\n"
        
        return info
    
    def _get_alert_history(self) -> str:
        """Get recent alerts"""
        if not self.history:
            return "No alerts recorded"
        
        recent = [a for a in self.history if time.time() - a['timestamp'] < 3600]  # Last hour
        
        info = "🚨 **RECENT ALERTS**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for alert in recent[-10:]:
            time_str = datetime.fromtimestamp(alert['timestamp']).strftime('%H:%M:%S')
            severity_icon = '🔴' if alert.get('severity') == 'high' else '🟡'
            info += f"{severity_icon} [{time_str}] {alert['message']}\n"
        
        return info
    
    def _get_thresholds(self) -> str:
        """Get current alert thresholds"""
        info = "⚙️ **ALERT THRESHOLDS**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for key, value in self.thresholds.items():
            name = key.replace('_', ' ').upper()
            info += f"  • {name}: {value}{'%' if 'percent' in key else ''}\n"
        return info
    
    def _store_alert(self, source: str, message: str, severity: str = 'medium'):
        """Store alert in history and memory"""
        alert = {
            'source': source,
            'message': message,
            'severity': severity,
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat()
        }
        self.history.append(alert)
        
        # Trim history
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        # Store in memory bus
        if self.hive_bus:
            self.hive_bus.publish('system_alert', alert)
    
    def _get_status_icon(self, value: float, metric: str) -> str:
        """Get status icon based on thresholds"""
        threshold = self.thresholds.get(f'{metric}_percent', 80)
        if value > threshold:
            return '🔴'
        elif value > threshold * 0.7:
            return '🟡'
        return '🟢'
    
    def _format_bytes(self, bytes_val: int) -> str:
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} PB"
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"