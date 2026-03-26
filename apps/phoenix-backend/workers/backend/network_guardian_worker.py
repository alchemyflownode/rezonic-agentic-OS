"""
Network Guardian Worker - Monitors network for rogue activity
"""

import psutil
import socket
import subprocess
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class NetworkGuardianWorker(BaseWorker):
    """
    Monitors network connections, detects suspicious activity
    """
    
    def __init__(self, hive_bus=None, kernel_memory=None):
        super().__init__("network_guardian", hive_bus, kernel_memory)
        self.suspicious_ports = [
            4444,  # Metasploit default
            1337,  # Common backdoor
            6667,  # IRC (often used by bots)
            31337, # Elite backdoor
            12345, # NetBus
            27374, # SubSeven
            5555,  # Android ADB
            3389,  # RDP
            22,    # SSH (watch for brute force)
            23,    # Telnet
        ]
        self.known_bad_ips = set()  # Would load from threat intel
        self.connection_history = []
        logger.info("  🌐 NetworkGuardianWorker initialized")
    
    async def process(self, task: str) -> str:
        """Process network commands"""
        task_lower = task.lower()
        
        if '/net status' in task or '/network status' in task:
            return await self._get_network_status()
        
        elif '/net connections' in task:
            return await self._list_connections()
        
        elif '/net scan' in task:
            return await self._scan_network()
        
        elif '/net suspicious' in task:
            return await self._find_suspicious()
        
        return "🌐 Network Guardian ready. Try /net status, /net suspicious"
    
    async def _get_network_status(self) -> str:
        """Get overall network status"""
        net = psutil.net_io_counters()
        connections = psutil.net_connections()
        
        # Count by status
        status_counts = {}
        for conn in connections:
            status_counts[conn.status] = status_counts.get(conn.status, 0) + 1
        
        # Get interfaces
        interfaces = psutil.net_if_stats()
        
        result = f"""🌐 **NETWORK STATUS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 STATISTICS
  • Sent: {self._format_bytes(net.bytes_sent)}
  • Received: {self._format_bytes(net.bytes_recv)}
  • Packets sent: {net.packets_sent:,}
  • Packets recv: {net.packets_recv:,}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔌 CONNECTIONS
  • Total: {len(connections)}
  • ESTABLISHED: {status_counts.get('ESTABLISHED', 0)}
  • LISTEN: {status_counts.get('LISTEN', 0)}
  • TIME_WAIT: {status_counts.get('TIME_WAIT', 0)}
  • CLOSE_WAIT: {status_counts.get('CLOSE_WAIT', 0)}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🖧 INTERFACES
"""
        for name, stats in interfaces.items():
            result += f"  • {name}: {'UP' if stats.isup else 'DOWN'} - {stats.speed}Mb/s\n"
        
        return result
    
    async def _list_connections(self) -> str:
        """List all network connections"""
        connections = psutil.net_connections()
        
        result = "🔌 **ACTIVE CONNECTIONS**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        # Group by status
        established = [c for c in connections if c.status == 'ESTABLISHED']
        listening = [c for c in connections if c.status == 'LISTEN']
        
        result += f"\n📡 ESTABLISHED ({len(established)}):\n"
        for conn in established[:10]:  # Show first 10
            if conn.raddr:
                result += f"  • {conn.laddr.ip}:{conn.laddr.port} → {conn.raddr.ip}:{conn.raddr.port}\n"
        
        result += f"\n👂 LISTENING ({len(listening)}):\n"
        for conn in listening[:10]:
            result += f"  • {conn.laddr.ip}:{conn.laddr.port}\n"
        
        return result
    
    async def _find_suspicious(self) -> str:
        """Find suspicious network activity"""
        connections = psutil.net_connections()
        suspicious = []
        
        for conn in connections:
            # Check for suspicious ports
            if conn.raddr and conn.raddr.port in self.suspicious_ports:
                suspicious.append({
                    'type': 'suspicious_port',
                    'port': conn.raddr.port,
                    'remote': f"{conn.raddr.ip}:{conn.raddr.port}",
                    'local': f"{conn.laddr.ip}:{conn.laddr.port}",
                    'process': self._get_process_name(conn.pid)
                })
            
            # Check for many connections to same IP (possible botnet)
            if conn.raddr:
                same_ip = [c for c in connections if c.raddr and c.raddr.ip == conn.raddr.ip]
                if len(same_ip) > 10:
                    suspicious.append({
                        'type': 'many_connections',
                        'ip': conn.raddr.ip,
                        'count': len(same_ip),
                        'ports': list(set(c.raddr.port for c in same_ip if c.raddr))
                    })
        
        if not suspicious:
            return "✅ No suspicious network activity detected"
        
        result = "🚨 **SUSPICIOUS ACTIVITY DETECTED**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for item in suspicious[:5]:
            if item['type'] == 'suspicious_port':
                result += f"\n⚠️ Suspicious port {item['port']}\n"
                result += f"   • {item['local']} → {item['remote']}\n"
                result += f"   • Process: {item['process']}\n"
            
            elif item['type'] == 'many_connections':
                result += f"\n⚠️ Many connections to {item['ip']}\n"
                result += f"   • {item['count']} connections\n"
                result += f"   • Ports: {', '.join([str(p) for p in item['ports'][:5]])}\n"
        
        # Store in memory
        if self.hive_bus:
            self.hive_bus.publish('suspicious_network', {'count': len(suspicious)})
        
        return result
    
    async def _scan_network(self) -> str:
        """Quick network scan (local only)"""
        local_ip = self._get_local_ip()
        if not local_ip:
            return "Could not determine local IP"
        
        # Get network prefix
        parts = local_ip.split('.')
        network = f"{parts[0]}.{parts[1]}.{parts[2]}"
        
        result = f"🔍 Scanning network {network}.0/24...\n"
        
        # Quick ping scan (simplified - would use nmap in production)
        active_hosts = []
        for i in range(1, 5):  # Just scan first few for demo
            target = f"{network}.{i}"
            if await self._ping_host(target):
                active_hosts.append(target)
        
        if active_hosts:
            result += "\n✅ Active hosts found:\n"
            for host in active_hosts:
                result += f"  • {host}\n"
        else:
            result += "\nNo other hosts found"
        
        return result
    
    def _get_process_name(self, pid: int) -> str:
        """Get process name by PID"""
        try:
            proc = psutil.Process(pid)
            return proc.name()
        except:
            return "unknown"
    
    def _get_local_ip(self) -> Optional[str]:
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return None
    
    async def _ping_host(self, ip: str) -> bool:
        """Ping a host (simplified)"""
        try:
            # Use subprocess to ping (would use asyncio in production)
            import subprocess
            result = subprocess.run(
                ['ping', '-n', '1', '-w', '1000', ip],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except:
            return False
    
    def _format_bytes(self, bytes_val: int) -> str:
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} TB"