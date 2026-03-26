import asyncio
from datetime import datetime

class ZeroDriftPlanner:
    def __init__(self, max_steps=20, max_retries=3):
        self.max_steps = max_steps
        self.max_retries = max_retries
        self.step_count = 0
        self.retry_count = 0
        self.completed_goals = set()
        
    async def plan(self, goal, available_tools):
        """Plan steps to achieve a goal with loop prevention"""
        
        # Check if goal already completed
        goal_hash = hash(str(goal))
        if goal_hash in self.completed_goals:
            return {'action': 'finish_task', 'args': {'reason': 'Goal already completed'}}
            
        self.step_count += 1
        
        # Prevent infinite loops
        if self.step_count > self.max_steps:
            return {
                'action': 'error',
                'args': {'msg': f'Max steps ({self.max_steps}) exceeded'}
            }
            
        # Check for repetitive actions
        if self._detect_loop():
            return {
                'action': 'constitutional_override',
                'args': {'reason': 'Loop detected, injecting new strategy'}
            }
            
        # Generate next action
        action = await self._generate_action(goal, available_tools)
        
        # Validate tool exists
        if action['action'] not in available_tools and action['action'] not in ['error', 'finish_task']:
            self.retry_count += 1
            if self.retry_count > self.max_retries:
                return {
                    'action': 'finish_task',
                    'args': {'reason': f'Tool {action["action"]} unavailable after {self.max_retries} retries'}
                }
            return await self.plan(goal, available_tools)  # Retry
            
        return action
        
    def _detect_loop(self):
        """Detect if we're in a loop of the same actions"""
        # Implement loop detection logic
        return False
        
    async def _generate_action(self, goal, tools):
        """Generate next action using LLM"""
        # Your existing LLM call here
        pass