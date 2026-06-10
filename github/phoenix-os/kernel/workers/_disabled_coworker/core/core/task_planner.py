"""
Task Planner for Phoenix Coworker

Converts high-level goals into executable steps.
Provides proactive task planning and execution.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto


class StepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class PlanStep:
    """A single step in a plan"""
    id: str
    name: str
    description: str
    tool: str  # e.g., "filesystem", "brain", "execution"
    action: str  # The specific action
    parameters: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 2


@dataclass
class TaskPlan:
    """A complete task plan"""
    id: str
    goal: str
    steps: List[PlanStep]
    priority: TaskPriority
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: StepStatus = StepStatus.PENDING
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "goal": self.goal,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "steps": [
                {
                    "id": s.id,
                    "name": s.name,
                    "description": s.description,
                    "tool": s.tool,
                    "action": s.action,
                    "parameters": s.parameters,
                    "depends_on": s.depends_on,
                    "status": s.status.value,
                    "result": s.result,
                    "error": s.error,
                    "retry_count": s.retry_count,
                }
                for s in self.steps
            ],
            "context": self.context
        }


class TaskPlanner:
    """
    Task planner for Phoenix Coworker.
    
    Breaks down high-level goals into executable steps and manages execution.
    """
    
    # Predefined plan templates for common tasks
    TEMPLATES = {
        "organize_downloads": {
            "goal": "Organize the Downloads folder",
            "steps": [
                {
                    "name": "analyze",
                    "description": "List all files in Downloads folder",
                    "tool": "filesystem",
                    "action": "list_directory",
                    "parameters": {"path": "~/Downloads"}
                },
                {
                    "name": "categorize",
                    "description": "Categorize files by type",
                    "tool": "brain",
                    "action": "classify_files",
                    "parameters": {},
                    "depends_on": ["analyze"]
                },
                {
                    "name": "create_folders",
                    "description": "Create category folders if needed",
                    "tool": "filesystem",
                    "action": "ensure_directories",
                    "parameters": {},
                    "depends_on": ["categorize"]
                },
                {
                    "name": "move_files",
                    "description": "Move files to appropriate folders",
                    "tool": "filesystem",
                    "action": "move_files",
                    "parameters": {},
                    "depends_on": ["create_folders"]
                },
                {
                    "name": "verify",
                    "description": "Verify organization completed",
                    "tool": "filesystem",
                    "action": "list_directory",
                    "parameters": {"path": "~/Downloads"},
                    "depends_on": ["move_files"]
                }
            ]
        },
        
        "summarize_document": {
            "goal": "Summarize a document",
            "steps": [
                {
                    "name": "read",
                    "description": "Read document content",
                    "tool": "filesystem",
                    "action": "read_file",
                    "parameters": {}
                },
                {
                    "name": "summarize",
                    "description": "Generate summary using LLM",
                    "tool": "brain",
                    "action": "summarize",
                    "parameters": {},
                    "depends_on": ["read"]
                },
                {
                    "name": "save",
                    "description": "Save summary to notes",
                    "tool": "filesystem",
                    "action": "write_file",
                    "parameters": {},
                    "depends_on": ["summarize"]
                }
            ]
        },
        
        "morning_briefing": {
            "goal": "Generate morning briefing",
            "steps": [
                {
                    "name": "check_calendar",
                    "description": "Check today's calendar events",
                    "tool": "system",
                    "action": "get_calendar_events",
                    "parameters": {"period": "today"}
                },
                {
                    "name": "check_emails",
                    "description": "Check recent important emails",
                    "tool": "system",
                    "action": "get_emails",
                    "parameters": {"count": 10, "unread_only": True}
                },
                {
                    "name": "check_tasks",
                    "description": "Check pending tasks",
                    "tool": "memory",
                    "action": "recall",
                    "parameters": {"query": "pending tasks today", "limit": 10}
                },
                {
                    "name": "check_weather",
                    "description": "Get weather forecast",
                    "tool": "system",
                    "action": "get_weather",
                    "parameters": {}
                },
                {
                    "name": "generate_briefing",
                    "description": "Compile morning briefing",
                    "tool": "brain",
                    "action": "generate_briefing",
                    "parameters": {},
                    "depends_on": ["check_calendar", "check_emails", "check_tasks", "check_weather"]
                }
            ]
        },
        
        "code_review": {
            "goal": "Review code changes",
            "steps": [
                {
                    "name": "get_changes",
                    "description": "Get recent git changes",
                    "tool": "execution",
                    "action": "run_command",
                    "parameters": {"command": "git diff HEAD~1"}
                },
                {
                    "name": "analyze",
                    "description": "Analyze code for issues",
                    "tool": "brain",
                    "action": "review_code",
                    "parameters": {},
                    "depends_on": ["get_changes"]
                },
                {
                    "name": "report",
                    "description": "Generate review report",
                    "tool": "brain",
                    "action": "generate_report",
                    "parameters": {},
                    "depends_on": ["analyze"]
                }
            ]
        }
    }
    
    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.active_plans: Dict[str, TaskPlan] = {}
        self.plan_history: List[TaskPlan] = []
        self.tool_registry: Dict[str, Callable] = {}
        
        # Register default tools
        self._register_default_tools()
        
        print("✓ TaskPlanner initialized")
    
    def _register_default_tools(self):
        """Register default tool implementations"""
        self.tool_registry["filesystem"] = self._filesystem_tool
        self.tool_registry["brain"] = self._brain_tool
        self.tool_registry["execution"] = self._execution_tool
        self.tool_registry["memory"] = self._memory_tool
        self.tool_registry["system"] = self._system_tool
    
    def register_tool(self, name: str, implementation: Callable):
        """Register a tool implementation"""
        self.tool_registry[name] = implementation
    
    async def _filesystem_tool(self, action: str, parameters: Dict) -> Any:
        """Filesystem tool implementation"""
        if action == "list_directory":
            path = Path(parameters["path"]).expanduser()
            return [str(f) for f in path.iterdir() if f.is_file()]
        
        elif action == "read_file":
            path = Path(parameters["path"]).expanduser()
            return path.read_text()
        
        elif action == "write_file":
            path = Path(parameters["path"]).expanduser()
            path.write_text(parameters["content"])
            return f"Written to {path}"
        
        elif action == "move_files":
            moves = parameters.get("moves", [])
            results = []
            for move in moves:
                src = Path(move["source"]).expanduser()
                dst = Path(move["destination"]).expanduser()
                src.rename(dst)
                results.append(f"Moved {src} to {dst}")
            return results
        
        elif action == "ensure_directories":
            paths = parameters.get("paths", [])
            for path in paths:
                Path(path).expanduser().mkdir(parents=True, exist_ok=True)
            return f"Created {len(paths)} directories"
        
        return f"Unknown filesystem action: {action}"
    
    async def _brain_tool(self, action: str, parameters: Dict) -> Any:
        """Brain/LLM tool implementation"""
        if self.kernel and hasattr(self.kernel, 'brain'):
            return await self.kernel.brain.execute(action, parameters)
        
        # Fallback mock
        return f"[Brain would {action} with {parameters}]"
    
    async def _execution_tool(self, action: str, parameters: Dict) -> Any:
        """Code execution tool"""
        if action == "run_command":
            import subprocess
            result = subprocess.run(
                parameters["command"],
                shell=True,
                capture_output=True,
                text=True
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        return f"Unknown execution action: {action}"
    
    async def _memory_tool(self, action: str, parameters: Dict) -> Any:
        """Memory tool"""
        if self.kernel and hasattr(self.kernel, 'memory'):
            if action == "recall":
                return await self.kernel.memory.recall(
                    parameters.get("query", ""),
                    limit=parameters.get("limit", 5)
                )
        return []
    
    async def _system_tool(self, action: str, parameters: Dict) -> Any:
        """System integration tool"""
        # Placeholder for system integrations
        return f"[System would {action}]"
    
    async def create_plan(
        self,
        goal: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        context: Dict = None
    ) -> TaskPlan:
        """
        Create a plan for achieving a goal.
        
        Args:
            goal: The high-level goal
            priority: Task priority
            context: Additional context
        
        Returns:
            A TaskPlan with steps
        """
        context = context or {}
        
        # Check for template match
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        for template_name, template in self.TEMPLATES.items():
            if template["goal"].lower() in goal.lower() or goal.lower() in template["goal"].lower():
                steps = [
                    PlanStep(
                        id=f"{plan_id}_step_{i}",
                        name=step["name"],
                        description=step["description"],
                        tool=step["tool"],
                        action=step["action"],
                        parameters={**step.get("parameters", {}), **context},
                        depends_on=step.get("depends_on", [])
                    )
                    for i, step in enumerate(template["steps"])
                ]
                
                plan = TaskPlan(
                    id=plan_id,
                    goal=goal,
                    steps=steps,
                    priority=priority,
                    created_at=datetime.now(),
                    context=context
                )
                
                self.active_plans[plan_id] = plan
                return plan
        
        # No template match - create generic plan
        plan = await self._create_generic_plan(goal, priority, context)
        self.active_plans[plan.id] = plan
        return plan
    
    async def _create_generic_plan(
        self,
        goal: str,
        priority: TaskPriority,
        context: Dict
    ) -> TaskPlan:
        """Create a generic plan when no template matches"""
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Use brain to break down goal
        if self.kernel and hasattr(self.kernel, 'brain'):
            breakdown = await self.kernel.brain.execute(
                "breakdown_goal",
                {"goal": goal, "context": context}
            )
            
            steps = [
                PlanStep(
                    id=f"{plan_id}_step_{i}",
                    name=step.get("name", f"step_{i}"),
                    description=step.get("description", ""),
                    tool=step.get("tool", "brain"),
                    action=step.get("action", "execute"),
                    parameters=step.get("parameters", {}),
                    depends_on=step.get("depends_on", [])
                )
                for i, step in enumerate(breakdown.get("steps", []))
            ]
        else:
            # Fallback: single-step plan
            steps = [
                PlanStep(
                    id=f"{plan_id}_step_0",
                    name="execute",
                    description=f"Execute: {goal}",
                    tool="brain",
                    action="execute",
                    parameters={"goal": goal, **context}
                )
            ]
        
        return TaskPlan(
            id=plan_id,
            goal=goal,
            steps=steps,
            priority=priority,
            created_at=datetime.now(),
            context=context
        )
    
    async def execute_plan(self, plan_id: str) -> TaskPlan:
        """
        Execute a plan.
        
        Args:
            plan_id: The plan ID
        
        Returns:
            The completed plan
        """
        plan = self.active_plans.get(plan_id)
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")
        
        plan.status = StepStatus.IN_PROGRESS
        plan.started_at = datetime.now()
        
        print(f"\n📋 Executing plan: {plan.goal}")
        print(f"   {len(plan.steps)} steps\n")
        
        completed_steps = set()
        
        while len(completed_steps) < len(plan.steps):
            # Find next executable step
            executable = None
            for step in plan.steps:
                if step.status == StepStatus.PENDING:
                    if not step.depends_on or all(d in completed_steps for d in step.depends_on):
                        executable = step
                        break
            
            if not executable:
                # Check for stuck steps
                pending = [s for s in plan.steps if s.status == StepStatus.PENDING]
                if pending:
                    print(f"⚠️  Steps stuck due to unmet dependencies: {[s.name for s in pending]}")
                    for s in pending:
                        s.status = StepStatus.SKIPPED
                        s.error = "Dependencies not met"
                break
            
            # Execute step
            await self._execute_step(executable, plan)
            
            if executable.status == StepStatus.COMPLETED:
                completed_steps.add(executable.id)
            elif executable.status == StepStatus.FAILED:
                if executable.retry_count < executable.max_retries:
                    print(f"   Retrying {executable.name}...")
                    executable.retry_count += 1
                    executable.status = StepStatus.PENDING
                else:
                    print(f"   Step {executable.name} failed after retries")
                    completed_steps.add(executable.id)  # Mark as done to continue
        
        # Complete plan
        failed_steps = [s for s in plan.steps if s.status == StepStatus.FAILED]
        plan.status = StepStatus.COMPLETED if not failed_steps else StepStatus.FAILED
        plan.completed_at = datetime.now()
        
        print(f"\n✅ Plan completed: {plan.goal}")
        if failed_steps:
            print(f"   {len(failed_steps)} steps failed")
        
        # Move to history
        self.plan_history.append(plan)
        del self.active_plans[plan_id]
        
        return plan
    
    async def _execute_step(self, step: PlanStep, plan: TaskPlan):
        """Execute a single step"""
        step.status = StepStatus.IN_PROGRESS
        step.started_at = datetime.now()
        
        print(f"  ▶️  {step.name}: {step.description}")
        
        try:
            # Get tool
            tool = self.tool_registry.get(step.tool)
            if not tool:
                raise ValueError(f"Unknown tool: {step.tool}")
            
            # Resolve parameters (substitute results from dependencies)
            parameters = self._resolve_parameters(step.parameters, plan)
            
            # Execute
            result = await tool(step.action, parameters)
            
            step.result = result
            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.now()
            
            print(f"     ✅ Done")
            
        except Exception as e:
            step.error = str(e)
            step.status = StepStatus.FAILED
            print(f"     ❌ Failed: {e}")
    
    def _resolve_parameters(self, parameters: Dict, plan: TaskPlan) -> Dict:
        """Resolve parameter references to actual values"""
        resolved = {}
        
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith("$"):
                # Reference to another step's result
                ref_parts = value[1:].split(".")
                step_name = ref_parts[0]
                
                # Find step by name
                ref_step = None
                for s in plan.steps:
                    if s.name == step_name:
                        ref_step = s
                        break
                
                if ref_step and ref_step.result is not None:
                    if len(ref_parts) > 1:
                        # Access nested property
                        result = ref_step.result
                        for part in ref_parts[1:]:
                            if isinstance(result, dict):
                                result = result.get(part)
                            else:
                                result = None
                                break
                        resolved[key] = result
                    else:
                        resolved[key] = ref_step.result
                else:
                    resolved[key] = None
            else:
                resolved[key] = value
        
        return resolved
    
    async def plan_and_execute(
        self,
        goal: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        context: Dict = None
    ) -> TaskPlan:
        """Create and execute a plan in one call"""
        plan = await self.create_plan(goal, priority, context)
        return await self.execute_plan(plan.id)
    
    def get_plan_status(self, plan_id: str) -> Optional[Dict]:
        """Get the status of a plan"""
        plan = self.active_plans.get(plan_id)
        if not plan:
            return None
        
        return {
            "id": plan.id,
            "goal": plan.goal,
            "status": plan.status.value,
            "total_steps": len(plan.steps),
            "completed_steps": len([s for s in plan.steps if s.status == StepStatus.COMPLETED]),
            "failed_steps": len([s for s in plan.steps if s.status == StepStatus.FAILED]),
            "pending_steps": len([s for s in plan.steps if s.status == StepStatus.PENDING]),
        }
    
    def get_recent_plans(self, limit: int = 10) -> List[Dict]:
        """Get recent plan history"""
        return [p.to_dict() for p in self.plan_history[-limit:]]


# Singleton instance
_planner_instance: Optional[TaskPlanner] = None


def get_task_planner(kernel: Any = None) -> TaskPlanner:
    """Get or create the singleton task planner"""
    global _planner_instance
    if _planner_instance is None:
        _planner_instance = TaskPlanner(kernel)
    return _planner_instance


async def demo():
    """Demo the task planner"""
    print("\n" + "="*50)
    print("  Phoenix Coworker - Task Planner Demo")
    print("="*50 + "\n")
    
    planner = TaskPlanner()
    
    # Demo 1: Organize downloads
    print("--- Demo 1: Organize Downloads ---\n")
    plan = await planner.create_plan(
        "Organize my Downloads folder",
        priority=TaskPriority.MEDIUM
    )
    print(f"Created plan with {len(plan.steps)} steps:")
    for step in plan.steps:
        print(f"  - {step.name}: {step.description}")
    
    # Execute
    result = await planner.execute_plan(plan.id)
    print(f"\nResult: {result.status.value}")
    
    # Demo 2: Summarize document
    print("\n--- Demo 2: Summarize Document ---\n")
    plan = await planner.create_plan(
        "Summarize the quarterly report",
        priority=TaskPriority.HIGH,
        context={"document_path": "~/Downloads/quarterly_report.pdf"}
    )
    print(f"Created plan with {len(plan.steps)} steps:")
    for step in plan.steps:
        print(f"  - {step.name}: {step.description}")
    
    result = await planner.execute_plan(plan.id)
    print(f"\nResult: {result.status.value}")
    
    # Show history
    print("\n--- Plan History ---")
    for p in planner.get_recent_plans():
        print(f"  - {p['goal']}: {p['status']}")


if __name__ == "__main__":
    asyncio.run(demo())
