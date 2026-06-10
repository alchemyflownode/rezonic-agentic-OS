"""
Phoenix Coworker Kernel

The central orchestrator that ties together all components:
- Unified Memory
- Safety Guard
- Task Planner
- Event Bus
- Workers
- Desktop Integration
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime

# Core components
from .event_bus import EventBus, EventType, get_event_bus
from .unified_memory import UnifiedMemory, MemoryType, get_memory
from .safety import SafetyGuard, get_safety_guard
from .task_planner import TaskPlanner, TaskPriority, get_task_planner

# Add parent to path for worker imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class KernelConfig:
    """Configuration for the Phoenix kernel"""
    data_dir: Path = None
    hotkey: str = "ctrl+shift+space"
    enable_desktop: bool = True
    enable_file_watching: bool = True
    safety_profile: str = "balanced"  # strict, balanced, trusting
    default_llm: str = "ollama"  # ollama, openai, etc.
    ollama_model: str = "llama3.2"
    ollama_url: str = "http://localhost:11434"
    proactive_tasks: List[str] = None
    
    def __post_init__(self):
        if self.data_dir is None:
            self.data_dir = Path.home() / ".phoenix"
        if self.proactive_tasks is None:
            self.proactive_tasks = ["morning_briefing"]


class PhoenixKernel:
    """
    Phoenix Coworker Kernel
    
    The central brain that coordinates:
    - Memory (unified storage)
    - Safety (action validation)
    - Planning (task breakdown)
    - Events (communication)
    - Workers (execution)
    - Desktop (user interface)
    """
    
    def __init__(self, config: KernelConfig = None):
        self.config = config or KernelConfig()
        self.config.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Core components
        self.event_bus = get_event_bus()
        self.memory = get_memory(self.config.data_dir)
        self.safety = get_safety_guard(self.config.data_dir)
        self.planner = get_task_planner(self)
        
        # Workers (lazy loaded)
        self._workers: Dict[str, Any] = {}
        self._worker_tasks: List[asyncio.Task] = []
        
        # Desktop integration (lazy loaded)
        self._desktop = None
        
        # State
        self._running = False
        self._start_time = None
        
        # Activity tracking
        self._activity_log: List[Dict] = []
        
        # Setup event handlers
        self._setup_event_handlers()
        
        print(f"✓ PhoenixKernel initialized")
        print(f"  Data directory: {self.config.data_dir}")
    
    def _setup_event_handlers(self):
        """Setup internal event handlers"""
        self.event_bus.subscribe(EventType.SAFETY_BLOCKED, self._on_safety_blocked)
        self.event_bus.subscribe(EventType.TASK_COMPLETED, self._on_task_completed)
        self.event_bus.subscribe(EventType.FILE_CREATED, self._on_file_created)
    
    async def _on_safety_blocked(self, event):
        """Handle safety blocked events"""
        await self.memory.remember(
            f"Safety blocked action: {event.data.get('action', 'unknown')}",
            memory_type=MemoryType.EVENT,
            source="safety",
            context={"reason": event.data.get("reason")}
        )
    
    async def _on_task_completed(self, event):
        """Handle task completion"""
        self._log_activity(f"Task completed: {event.data.get('goal', 'unknown')}")
    
    async def _on_file_created(self, event):
        """Handle file creation events"""
        file_path = event.data.get("path")
        if file_path:
            await self.memory.remember(
                f"File created: {Path(file_path).name}",
                memory_type=MemoryType.FILE,
                source="filesystem",
                context={"path": file_path}
            )
    
    def _log_activity(self, message: str):
        """Log an activity"""
        entry = {
            "time": datetime.now().isoformat(),
            "message": message
        }
        self._activity_log.append(entry)
        # Keep last 1000 entries
        if len(self._activity_log) > 1000:
            self._activity_log = self._activity_log[-1000:]
    
    def get_recent_activity(self, limit: int = 10) -> List[str]:
        """Get recent activity log"""
        return [
            f"{a['time'][11:16]} - {a['message']}"
            for a in self._activity_log[-limit:]
        ]
    
    # ========== Worker Management ==========
    
    def get_worker(self, name: str) -> Optional[Any]:
        """Get or create a worker by name"""
        if name not in self._workers:
            self._workers[name] = self._create_worker(name)
        return self._workers.get(name)
    
    def _create_worker(self, name: str) -> Optional[Any]:
        """Create a worker instance"""
        # Import workers lazily
        if name == "brain":
            from workers.brain import BrainWorker
            return BrainWorker(self)
        elif name == "filesystem":
            from workers.filesystem import FilesystemWorker
            return FilesystemWorker(self)
        elif name == "execution":
            from workers.execution import ExecutionWorker
            return ExecutionWorker(self)
        elif name == "vision":
            from workers.vision import VisionWorker
            return VisionWorker(self)
        elif name == "voice":
            from workers.voice import VoiceWorker
            return VoiceWorker(self)
        else:
            print(f"Unknown worker: {name}")
            return None
    
    async def start_worker(self, name: str):
        """Start a worker"""
        worker = self.get_worker(name)
        if worker and hasattr(worker, 'start'):
            task = asyncio.create_task(worker.start())
            self._worker_tasks.append(task)
            await self.event_bus.publish(
                EventType.WORKER_STARTED,
                {"worker": name},
                source="kernel"
            )
    
    async def stop_all_workers(self):
        """Stop all workers"""
        for name, worker in self._workers.items():
            if hasattr(worker, 'stop'):
                try:
                    await worker.stop()
                except Exception as e:
                    print(f"Error stopping worker {name}: {e}")
        
        # Cancel worker tasks
        for task in self._worker_tasks:
            task.cancel()
        
        self._worker_tasks.clear()
    
    # ========== Desktop Integration ==========
    
    def _init_desktop(self):
        """Initialize desktop integration"""
        if not self.config.enable_desktop:
            return None
        
        try:
            from desktop.presence import DesktopCoworker
            
            desktop = DesktopCoworker(self, self.config.hotkey)
            
            # Setup file watchers
            if self.config.enable_file_watching:
                downloads = Path.home() / "Downloads"
                if downloads.exists():
                    desktop.add_watcher(
                        downloads,
                        patterns=["*.pdf", "*.zip", "*.jpg", "*.png"],
                    )
                
                notes = Path.home() / "Documents" / "Notes"
                if notes.exists():
                    desktop.add_watcher(
                        notes,
                        patterns=["*.md", "*.txt"],
                    )
            
            return desktop
            
        except ImportError as e:
            print(f"⚠ Desktop integration not available: {e}")
            return None
    
    @property
    def desktop(self):
        """Get desktop integration (lazy load)"""
        if self._desktop is None:
            self._desktop = self._init_desktop()
        return self._desktop
    
    # ========== Core Operations ==========
    
    async def execute(self, command: str, context: Dict = None) -> Dict:
        """
        Execute a user command.
        
        This is the main entry point for user interactions.
        """
        context = context or {}
        self._log_activity(f"Command: {command[:50]}")
        
        # Safety check
        safe = await self.safety.check_and_confirm(command, context)
        if not safe:
            return {
                "success": False,
                "error": "Action blocked by safety guard"
            }
        
        # Store in memory
        await self.memory.remember(
            command,
            memory_type=MemoryType.CONVERSATION,
            source="user",
            context=context
        )
        
        # Parse and route command
        result = await self._route_command(command, context)
        
        # Store result
        await self.memory.remember(
            f"Executed: {command[:50]}... Result: {result.get('success', False)}",
            memory_type=MemoryType.EVENT,
            source="kernel",
            context={"result": result}
        )
        
        return result
    
    async def _route_command(self, command: str, context: Dict) -> Dict:
        """Route a command to the appropriate handler"""
        command_lower = command.lower()
        
        # Direct worker commands
        if command_lower.startswith("organize"):
            return await self._handle_organize(command, context)
        
        elif command_lower.startswith("summarize"):
            return await self._handle_summarize(command, context)
        
        elif command_lower.startswith("search") or command_lower.startswith("find"):
            return await self._handle_search(command, context)
        
        elif command_lower.startswith("run") or command_lower.startswith("execute"):
            return await self._handle_execute(command, context)
        
        elif command_lower.startswith("remember"):
            return await self._handle_remember(command, context)
        
        elif command_lower.startswith("recall") or command_lower.startswith("what do you know"):
            return await self._handle_recall(command, context)
        
        # Planning commands
        elif command_lower.startswith("plan"):
            goal = command[4:].strip()
            plan = await self.planner.plan_and_execute(goal)
            return {
                "success": plan.status.value == "completed",
                "plan": plan.to_dict()
            }
        
        # Default: use brain worker
        brain = self.get_worker("brain")
        if brain:
            return await brain.process(command, context)
        
        return {
            "success": False,
            "error": "No handler found for command"
        }
    
    async def _handle_organize(self, command: str, context: Dict) -> Dict:
        """Handle organize commands"""
        plan = await self.planner.plan_and_execute(
            "Organize my Downloads folder",
            priority=TaskPriority.MEDIUM
        )
        return {
            "success": plan.status.value == "completed",
            "message": "Downloads folder organized",
            "details": plan.to_dict()
        }
    
    async def _handle_summarize(self, command: str, context: Dict) -> Dict:
        """Handle summarize commands"""
        # Extract file path from command
        words = command.split()
        file_path = None
        for word in words:
            if "." in word and not word.startswith("summarize"):
                file_path = word
                break
        
        if not file_path:
            return {
                "success": False,
                "error": "No file specified to summarize"
            }
        
        plan = await self.planner.plan_and_execute(
            f"Summarize {file_path}",
            priority=TaskPriority.MEDIUM,
            context={"document_path": file_path}
        )
        
        return {
            "success": plan.status.value == "completed",
            "message": f"Summarized {file_path}",
            "summary": plan.steps[-1].result if plan.steps else None
        }
    
    async def _handle_search(self, command: str, context: Dict) -> Dict:
        """Handle search commands"""
        query = command.replace("search", "").replace("find", "").strip()
        
        results = await self.memory.recall(query, limit=10)
        
        return {
            "success": True,
            "query": query,
            "results": [
                {
                    "content": r.content,
                    "type": r.memory_type.value,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in results
            ]
        }
    
    async def _handle_execute(self, command: str, context: Dict) -> Dict:
        """Handle code execution commands"""
        code = command.replace("run", "").replace("execute", "").strip()
        
        execution = self.get_worker("execution")
        if execution:
            return await execution.execute(code, context)
        
        return {
            "success": False,
            "error": "Execution worker not available"
        }
    
    async def _handle_remember(self, command: str, context: Dict) -> Dict:
        """Handle remember commands"""
        fact = command.replace("remember", "").replace("remember that", "").strip()
        
        entry = await self.memory.remember(
            fact,
            memory_type=MemoryType.FACT,
            source="user",
            context=context
        )
        
        return {
            "success": True,
            "message": f"Remembered: {fact[:50]}...",
            "memory_id": entry.id
        }
    
    async def _handle_recall(self, command: str, context: Dict) -> Dict:
        """Handle recall commands"""
        query = command.replace("recall", "").replace("what do you know about", "").strip()
        
        results = await self.memory.recall(query, limit=5)
        
        return {
            "success": True,
            "query": query,
            "memories": [
                {
                    "content": r.content,
                    "source": r.source,
                    "when": r.timestamp.isoformat()
                }
                for r in results
            ]
        }
    
    async def handle_file_event(self, file_path: Path, event_type: str):
        """Handle file system events from desktop watcher"""
        print(f"📁 File {event_type}: {file_path.name}")
        
        # Proactive suggestions based on file type
        suffix = file_path.suffix.lower()
        
        if suffix == '.pdf':
            print(f"💡 I see you downloaded '{file_path.name}'.")
            print("   Would you like me to: [s]ummarize, [o]rganize, [i]gnore?")
            # In real implementation, show notification
        
        elif suffix in ['.zip', '.tar', '.gz']:
            print(f"💡 I see you downloaded '{file_path.name}'.")
            print("   Would you like me to extract it?")
    
    # ========== Lifecycle ==========
    
    async def start(self):
        """Start the kernel"""
        self._running = True
        self._start_time = datetime.now()
        
        print("\n" + "="*50)
        print("  🐦 Phoenix Coworker Starting...")
        print("="*50 + "\n")
        
        # Publish start event
        await self.event_bus.publish(
            EventType.SYSTEM_START,
            {"version": "2.0.0", "config": asdict(self.config)},
            source="kernel"
        )
        
        # Start essential workers
        await self.start_worker("brain")
        await self.start_worker("filesystem")
        
        # Start desktop integration
        if self.desktop:
            self.desktop.start()
        
        # Store startup in memory
        await self.memory.remember(
            "Phoenix coworker started",
            memory_type=MemoryType.EVENT,
            source="system"
        )
        
        print("\n✅ Phoenix Coworker is running!")
        print(f"   Hotkey: {self.config.hotkey}")
        print("   Type 'help' for available commands\n")
        
        self._log_activity("System started")
    
    async def stop(self):
        """Stop the kernel"""
        print("\n🛑 Stopping Phoenix Coworker...")
        
        self._running = False
        
        # Stop desktop
        if self.desktop:
            self.desktop.stop()
        
        # Stop workers
        await self.stop_all_workers()
        
        # Publish stop event
        await self.event_bus.publish(
            EventType.SYSTEM_STOP,
            {"uptime": str(datetime.now() - self._start_time) if self._start_time else "unknown"},
            source="kernel"
        )
        
        # Close memory
        self.memory.close()
        
        print("✅ Phoenix Coworker stopped")
        self._log_activity("System stopped")
    
    async def run(self):
        """Run the kernel (blocking)"""
        await self.start()
        
        try:
            # Interactive loop
            while self._running:
                try:
                    command = await asyncio.get_event_loop().run_in_executor(
                        None, input, "phoenix> "
                    )
                    command = command.strip()
                    
                    if not command:
                        continue
                    
                    if command.lower() in ['exit', 'quit', 'q']:
                        break
                    
                    if command.lower() == 'help':
                        self._show_help()
                        continue
                    
                    if command.lower() == 'status':
                        self._show_status()
                        continue
                    
                    # Execute command
                    result = await self.execute(command)
                    
                    if result.get('success'):
                        if 'message' in result:
                            print(f"✓ {result['message']}")
                        if 'results' in result:
                            for r in result['results']:
                                print(f"  - {r.get('content', r)[:60]}...")
                    else:
                        print(f"✗ {result.get('error', 'Unknown error')}")
                
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Error: {e}")
        
        finally:
            await self.stop()
    
    def _show_help(self):
        """Show help message"""
        print("""
Available commands:
  organize              - Organize Downloads folder
  summarize <file>      - Summarize a document
  search <query>        - Search your memory
  remember <fact>       - Store a fact in memory
  recall <query>        - Recall information
  plan <goal>           - Create and execute a plan
  run <command>         - Execute a shell command
  status                - Show system status
  help                  - Show this help
  exit/quit             - Exit Phoenix
        """)
    
    def _show_status(self):
        """Show system status"""
        uptime = datetime.now() - self._start_time if self._start_time else "N/A"
        
        print(f"""
System Status:
  Uptime: {uptime}
  Workers: {len(self._workers)} active
  Memory: {self.memory.get_stats()}
  Safety: {self.safety.get_audit_summary()}
        """)


async def main():
    """Main entry point"""
    config = KernelConfig()
    kernel = PhoenixKernel(config)
    await kernel.run()


if __name__ == "__main__":
    asyncio.run(main())
