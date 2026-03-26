"""
Mastery Worker - Gamification System with XP and Levels
Tracks user achievements and provides gamification feedback
WITH PERSISTENCE via Hive Memory Bus
"""

import time
import json
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class Level(Enum):
    APPRENTICE = 1000
    VIBE_CODER = 2500
    REZ_APPRENTICE = 5000
    ZERO_DRIFT_ADEPT = 10000
    SOVEREIGN_ARCHITECT = 20000
    REZ_MASTER = 50000
    CONSTITUTIONAL_AI = 100000

class MasteryWorker:
    """
    Tracks XP, levels, and achievements across the system
    Now with persistence via Hive Memory Bus
    """
    def __init__(self, hive_bus=None):
        self.hive_bus = hive_bus
        self.name = "mastery_worker"
        self.xp = 0
        self.level = Level.APPRENTICE
        self.achievements = []
        self.xp_history = []
        
        # Load saved state if available
        self._load_state()
        logger.info(f"  🎮 MasteryWorker initialized with {self.xp} XP")
    
    def _load_state(self):
        """Load saved XP and achievements from hive bus"""
        if self.hive_bus:
            try:
                # Try to load from memory bus
                saved = self.hive_bus.recall('mastery_state')
                if saved:
                    self.xp = saved.get('xp', 0)
                    self.achievements = saved.get('achievements', [])
                    self.xp_history = saved.get('history', [])
                    self._update_level_from_xp()
                    logger.info(f"  📦 Loaded mastery state: {self.xp} XP")
            except Exception as e:
                logger.debug(f"Could not load mastery state: {e}")
    
    def _save_state(self):
        """Save current state to hive bus"""
        if self.hive_bus:
            try:
                state = {
                    'xp': self.xp,
                    'achievements': self.achievements,
                    'history': self.xp_history[-50:],  # Keep last 50
                    'timestamp': time.time()
                }
                self.hive_bus.store('mastery_state', state)
            except Exception as e:
                logger.debug(f"Could not save mastery state: {e}")
    
    def _update_level_from_xp(self):
        """Update level based on current XP"""
        for level in Level:
            if self.xp >= level.value and level.value > self.level.value:
                self.level = level
    
    async def health_check(self):
        """Health check for the worker"""
        return {
            "healthy": True,
            "worker": self.name,
            "xp": self.xp,
            "level": self.level.name,
            "achievements": len(self.achievements)
        }
    
    async def add_xp(self, action: str, amount: int, description: str = ""):
        """
        Add XP points for an action
        """
        self.xp += amount
        entry = {
            "timestamp": time.time(),
            "action": action,
            "amount": amount,
            "description": description,
            "total": self.xp
        }
        self.xp_history.append(entry)
        
        # Check for level up
        old_level = self.level
        leveled_up = await self._check_level_up()
        
        result = {
            "xp_added": amount,
            "total_xp": self.xp,
            "level": self.level.name,
            "leveled_up": leveled_up
        }
        
        # Save state
        self._save_state()
        
        # Store in hive memory if available
        if self.hive_bus:
            self.hive_bus.store(
                f"xp_{int(time.time())}",
                entry,
                tags=["mastery", "xp", action]
            )
        
        return result
    
    async def _check_level_up(self):
        """Check if XP threshold reached for next level"""
        leveled_up = False
        for level in Level:
            if self.xp >= level.value and level.value > self.level.value:
                self.level = level
                achievement = f"🏆 Reached {level.name} at {self.xp} XP"
                self.achievements.append(achievement)
                logger.info(f"  {achievement}")
                leveled_up = True
                self._save_state()  # Save after level up
        return leveled_up
    
    async def get_stats(self):
        """Get current mastery statistics"""
        return {
            "xp": self.xp,
            "level": self.level.name,
            "next_level": self._get_next_level(),
            "xp_to_next": self._xp_to_next_level(),
            "achievements": self.achievements[-5:],  # Last 5 achievements
            "total_actions": len(self.xp_history)
        }
    
    def _get_next_level(self):
        """Get the next level"""
        levels = list(Level)
        for i, level in enumerate(levels):
            if level == self.level and i < len(levels) - 1:
                return levels[i + 1].name
        return "MAX"
    
    def _xp_to_next_level(self):
        """Calculate XP needed for next level"""
        levels = list(Level)
        for i, level in enumerate(levels):
            if level == self.level and i < len(levels) - 1:
                return levels[i + 1].value - self.xp
        return 0
    
    async def process(self, task: str) -> dict:
        """Process mastery-related commands"""
        task_lower = task.lower()
        
        if task.startswith('/xp'):
            stats = await self.get_stats()
            achievements_text = "\n".join(['  • ' + a for a in stats['achievements']]) if stats['achievements'] else "  None yet"
            
            return {
                "content": f"""🎮 **MASTERY STATUS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current XP: {stats['xp']}
Level: {stats['level']}
Next Level: {stats['next_level']}
XP to Next: {stats['xp_to_next']}
Total Actions: {stats['total_actions']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Recent Achievements:
{achievements_text}
"""
            }
        
        elif task.startswith('/add_xp'):
            # Format: /add_xp 500 scan "Completed full system scan"
            parts = task.split()
            if len(parts) >= 3:
                try:
                    amount = int(parts[1])
                    action = parts[2]
                    description = ' '.join(parts[3:]) if len(parts) > 3 else ""
                    result = await self.add_xp(action, amount, description)
                    return {
                        "content": f"✅ Added {amount} XP for {action}! Total: {result['total_xp']} (Level: {result['level']})"
                    }
                except ValueError:
                    return {"content": "❌ Invalid amount. Use a number."}
                except Exception as e:
                    return {"content": f"❌ Error: {str(e)}"}
            else:
                return {"content": "❌ Usage: /add_xp <amount> <action> [description]"}
        
        elif task.startswith('/achievements'):
            if self.achievements:
                return {
                    "content": "🏆 **ACHIEVEMENTS**\n" + "\n".join(["  • " + a for a in self.achievements[-10:]])
                }
            else:
                return {"content": "No achievements yet. Keep using the system!"}
        
        elif task.startswith('/reset'):
            # Admin command to reset XP (for testing)
            self.xp = 0
            self.level = Level.APPRENTICE
            self.achievements = []
            self.xp_history = []
            self._save_state()
            return {"content": "🔄 Mastery stats reset to zero"}
        
        else:
            stats = await self.get_stats()
            return {
                "content": f"Mastery Worker ready. Current XP: {stats['xp']} (Level: {stats['level']})"
            }
    
    async def process_stream(self, task: str):
        """Stream mastery responses"""
        result = await self.process(task)
        yield result['content']

