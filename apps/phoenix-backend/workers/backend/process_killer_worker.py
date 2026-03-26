"""
Process Killer Worker - Terminates rogue processes
Quarantines before killing, never just deletes
"""

import psutil
import signal
import time
from datetime import datetime
from typing import Dict, List, Optional
import logging

from backend.security.quarantine import quarantine

logger = logging.getLogger(__name__)

class ProcessKillerWorker(BaseWorker):
    """
    Kills rogue processes but ALWAYS quarantines first
    """
    
    def __init__(self, hive_bus=None, kernel_memory=None):
        super().__init__("process_killer", hive_bus, kernel_memory)
        self.killed_history = []
        self.protected_processes = [
            'winlogon.exe',
            'csrss.exe',
            'services.exe',
            'lsass.exe',
            'svchost.exe',  # Careful with this one
            'System',
            'smss.exe',
            'wininit.exe',
            'taskmgr.exe'
        ]
        logger.info("  🔪 ProcessKillerWorker initialized")
    
    async def process(self, task: str) -> str:
        """Process kill commands"""
        task_lower = task.lower()
        
        if '/kill' in task or '/terminate' in task:
            return await self._kill_process(task)
        
        elif '/kill rogue' in task or '/kill suspiciou' in task:
            return await self._kill_rogue_processes()
        
        elif '/process list' in task:
            return await self._list_processes()
        
        return "🔪 Process Killer ready. Try /kill <pid> or /kill rogue"
    
    async def _kill_process(self, task: str) -> str:
        """Kill a specific process by PID or name"""
        parts = task.split()
        if len(parts) < 2:
            return "❌ Usage: /kill <pid> or /kill <process_name>"
        
        target = parts[1]
        
        try:
            # Try as PID first
            if target.isdigit():
                pid = int(target)
                return await self._kill_by_pid(pid)
            else:
                # Kill by name
                return await self._kill_by_name(target)
        except Exception as e:
            return f"❌ Failed to kill: {str(e)}"
    
    async def _kill_by_pid(self, pid: int) -> str:
        """Kill process by PID with quarantine"""
        try:
            process = psutil.Process(pid)
            name = process.name()
            
            # Check if protected
            if name.lower() in [p.lower() for p in self.protected_processes]:
                return f"❌ Cannot kill protected system process: {name}"
            
            # Get process info before killing
            info = self._get_process_info(process)
            
            # QUARANTINE FIRST!
            quarantine_id = await self._quarantine_process(pid, name, info)
            
            # Now kill
            process.terminate()
            
            # Give it a moment
            gone, alive = psutil.wait_procs([process], timeout=3)
            if process in alive:
                process.kill()  # Force kill if still alive
            
            # Record
            record = {
                'pid': pid,
                'name': name,
                'quarantine_id': quarantine_id,
                'timestamp': time.time(),
                'datetime': datetime.now().isoformat()
            }
            self.killed_history.append(record)
            
            # Store in memory
            if self.hive_bus:
                self.hive_bus.publish('process_killed', record)
            
            return f"✅ Killed process {name} (PID: {pid})\n🛡️ Quarantine ID: {quarantine_id}"
            
        except psutil.NoSuchProcess:
            return f"❌ Process with PID {pid} not found"
        except psutil.AccessDenied:
            return f"❌ Access denied - need administrator privileges"
    
    async def _kill_by_name(self, name: str) -> str:
        """Kill all processes with given name"""
        killed = []
        failed = []
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if name.lower() in proc.info['name'].lower():
                    # Check if protected
                    if proc.info['name'].lower() in [p.lower() for p in self.protected_processes]:
                        failed.append(f"{proc.info['name']} (protected)")
                        continue
                    
                    # Quarantine first
                    quarantine_id = await self._quarantine_process(
                        proc.info['pid'], 
                        proc.info['name'],
                        self._get_process_info(proc)
                    )
                    
                    # Kill
                    proc.terminate()
                    killed.append(f"{proc.info['name']} (PID: {proc.info['pid']}) - Quarantine: {quarantine_id}")
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if killed:
            result = "✅ Killed processes:\n" + "\n".join(killed)
            if failed:
                result += "\n\n❌ Failed (protected):\n" + "\n".join(failed)
            return result
        else:
            return f"No processes found matching '{name}'"
    
    async def _kill_rogue_processes(self) -> str:
        """Auto-detect and kill rogue processes"""
        killed = []
        suspicious = []
        
        # Common rogue patterns
        rogue_patterns = [
            'miner', 'crypto', 'xmrig',  # Crypto miners
            'keylogger', 'hook',           # Keyloggers
            'backdoor', 'trojan',          # Malware
            'unknown', 'temp'               # Suspicious names
        ]
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'connections']):
            try:
                name = proc.info['name'].lower()
                cpu = proc.info['cpu_percent']
                mem = proc.info['memory_percent']
                
                # Check for high resource usage (possible miner)
                if cpu > 50 and 'chrome' not in name and 'firefox' not in name:
                    suspicious.append({
                        'name': proc.info['name'],
                        'pid': proc.info['pid'],
                        'reason': f"High CPU: {cpu}%",
                        'score': cpu
                    })
                
                # Check for rogue patterns
                for pattern in rogue_patterns:
                    if pattern in name:
                        suspicious.append({
                            'name': proc.info['name'],
                            'pid': proc.info['pid'],
                            'reason': f"Suspicious name: {name}",
                            'score': 90
                        })
                        break
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by suspicion score
        suspicious.sort(key=lambda x: x['score'], reverse=True)
        
        # Kill top 3 most suspicious
        for proc in suspicious[:3]:
            result = await self._kill_by_pid(proc['pid'])
            killed.append(f"{proc['name']} (PID: {proc['pid']}) - {proc['reason']}")
        
        if killed:
            return "🔪 Killed rogue processes:\n" + "\n".join(killed)
        else:
            return "✅ No rogue processes detected"
    
    async def _quarantine_process(self, pid: int, name: str, info: Dict) -> str:
        """Quarantine process info before killing"""
        # Create quarantine record
        quarantine_id = f"proc_{int(time.time())}_{pid}"
        
        quarantine_path = f"./quarantine/processes/{quarantine_id}.json"
        os.makedirs("./quarantine/processes", exist_ok=True)
        
        with open(quarantine_path, 'w') as f:
            json.dump(info, f, indent=2)
        
        # Log to memory
        if self.hive_bus:
            self.hive_bus.publish('process_quarantined', {
                'quarantine_id': quarantine_id,
                'pid': pid,
                'name': name,
                'info': info
            })
        
        return quarantine_id
    
    def _get_process_info(self, process) -> Dict:
        """Get detailed process info for quarantine"""
        try:
            return {
                'pid': process.pid,
                'name': process.name(),
                'exe': process.exe(),
                'cmdline': process.cmdline(),
                'cwd': process.cwd(),
                'cpu_percent': process.cpu_percent(),
                'memory_percent': process.memory_percent(),
                'memory_info': str(process.memory_info()),
                'connections': len(process.connections()),
                'threads': len(process.threads()),
                'create_time': process.create_time(),
                'username': process.username(),
                'status': process.status()
            }
        except:
            return {'pid': process.pid, 'name': process.name()}
    
    async def _list_processes(self) -> str:
        """List all processes with resource usage"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except:
                continue
        
        # Sort by CPU
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        result = "📋 **PROCESS LIST**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for proc in processes[:20]:
            result += f"  • {proc['name'][:20]:<20} PID:{proc['pid']:<6} CPU:{proc['cpu_percent']:>5.1f}% MEM:{proc['memory_percent']:>5.1f}%\n"
        
        result += f"\n... and {len(processes)-20} more"
        return result