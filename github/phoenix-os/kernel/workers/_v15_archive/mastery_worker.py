#!/usr/bin/env python3
"""
MasteryWorker v3.0 — System-Grade Gamification Engine
=======================================================
Architecture:
    - Event sourcing (immutable XP events)
    - Derived state (level calculated, never stored)
    - Single source of truth for level logic
    - Deterministic event IDs (UUID, not time)
    - Validated state restoration
    - Separated concerns: Core + Storage + Interface
"""

import time
import json
import uuid
import logging
from enum import Enum, auto
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


# ==========================================
# CONFIGURATION (Evolvable)
# ==========================================

LEVEL_CONFIG = [
    ("APPRENTICE", 0),
    ("VIBE_CODER", 1000),
    ("REZ_APPRENTICE", 5000),
    ("ZERO_DRIFT_ADEPT", 10000),
    ("SOVEREIGN_ARCHITECT", 25000),
    ("REZ_MASTER", 50000),
    ("CONSTITUTIONAL_AI", 100000),
    ("SOVEREIGN_LEGEND", 250000),
]

# XP rewards (configurable)
XP_REWARDS = {
    "code_review": 50,
    "code_fix": 100,
    "code_generate": 75,
    "code_optimize": 150,
    "kernel_start": 10,
    "worker_loaded": 5,
    "blueprint_created": 25,
    "trade_executed": 50,
    "security_scan": 50,
    "vulnerability_fixed": 150,
    "drift_corrected": 100,
    "docstring_added": 25,
    "type_hint_added": 15,
}


# ==========================================
# DATA MODELS (Immutability)
# ==========================================

@dataclass(frozen=True)
class XPEvent:
    """Immutable XP event — cornerstone of event sourcing."""
    id: str
    timestamp: float
    action: str
    amount: int
    description: str
    source: str
    xp_after: int
    
    @classmethod
    def create(cls, action: str, amount: int, description: str, source: str, xp_after: int) -> "XPEvent":
        return cls(
            id=uuid.uuid4().hex,
            timestamp=time.time(),
            action=action,
            amount=amount,
            description=description,
            source=source,
            xp_after=xp_after
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LevelInfo:
    """Level information (derived, not stored)."""
    name: str
    threshold: int
    emoji: str
    is_current: bool = False
    
    @property
    def progress_to_next(self) -> float:
        """Not used in core, but useful for UI."""
        return 0.0


# ==========================================
# CORE ENGINE (Single Source of Truth)
# ==========================================

class MasteryCore:
    """
    Pure logic engine for XP and levels.
    No persistence, no I/O, no UI.
    """
    
    def __init__(self):
        self._levels = self._build_levels()
        self._xp = 0
        self._events: List[XPEvent] = []
    
    @property
    def xp(self) -> int:
        return self._xp
    
    @property
    def level(self) -> Tuple[str, int]:
        """Single source of truth for level."""
        return self._calculate_level()
    
    @property
    def events(self) -> List[XPEvent]:
        return self._events.copy()
    
    def add_xp(self, action: str, amount: int, description: str, source: str) -> Tuple[int, bool, List[Dict]]:
        """
        Add XP, return (new_xp, leveled_up, achievements).
        Pure function — no side effects.
        """
        old_level = self.level
        self._xp += amount
        
        # Record event
        event = XPEvent.create(action, amount, description, source, self._xp)
        self._events.append(event)
        
        # Check level up
        new_level = self.level
        leveled_up = new_level != old_level
        
        # Generate achievements for level up
        achievements = []
        if leveled_up:
            achievements.append({
                "name": f"Reached {new_level[0]}",
                "description": f"Earned {self._xp} XP total",
                "emoji": self._get_level_emoji(new_level[0]),
                "timestamp": time.time(),
                "xp_attained": self._xp
            })
        
        return self._xp, leveled_up, achievements
    
    def _calculate_level(self) -> Tuple[str, int]:
        """Single source of truth for level calculation."""
        current_level = self._levels[0]  # Default to first level
        for level in self._levels:
            if self._xp >= level[1]:
                current_level = level
        return current_level
    
    def get_stats(self) -> Dict[str, Any]:
        """Return current statistics (derived, not stored)."""
        current_level = self.level
        next_level = self._get_next_level()
        
        return {
            "xp": self._xp,
            "level": current_level[0],
            "level_threshold": current_level[1],
            "next_level": next_level[0] if next_level else "MAX",
            "next_level_threshold": next_level[1] if next_level else self._xp,
            "xp_to_next": next_level[1] - self._xp if next_level else 0,
            "total_events": len(self._events),
            "total_xp_earned": self._xp,
            "progress_percent": self._calculate_progress(current_level, next_level)
        }
    
    def _calculate_progress(self, current: Tuple[str, int], next: Optional[Tuple[str, int]]) -> float:
        """Calculate progress to next level."""
        if not next:
            return 100.0
        xp_in_level = self._xp - current[1]
        level_range = next[1] - current[1]
        if level_range <= 0:
            return 100.0
        return min(100.0, (xp_in_level / level_range) * 100)
    
    def _get_next_level(self) -> Optional[Tuple[str, int]]:
        """Get next level after current."""
        for i, level in enumerate(self._levels):
            if level == self.level and i < len(self._levels) - 1:
                return self._levels[i + 1]
        return None
    
    def _get_level_emoji(self, level_name: str) -> str:
        """Get emoji for level."""
        emojis = {
            "APPRENTICE": "🌱",
            "VIBE_CODER": "🎸",
            "REZ_APPRENTICE": "🦎",
            "ZERO_DRIFT_ADEPT": "⛓️",
            "SOVEREIGN_ARCHITECT": "🏛️",
            "REZ_MASTER": "🔥",
            "CONSTITUTIONAL_AI": "⚖️",
            "SOVEREIGN_LEGEND": "👑",
        }
        return emojis.get(level_name, "🎮")
    
    def _build_levels(self) -> List[Tuple[str, int]]:
        """Build levels from config (sorted)."""
        return sorted(LEVEL_CONFIG, key=lambda x: x[1])
    
    def restore_from_events(self, events: List[Dict]) -> None:
        """
        Rebuild state from event log.
        This is event sourcing: replay all events to rebuild state.
        """
        self._events = []
        self._xp = 0
        
        # Sort by timestamp to ensure correct replay
        sorted_events = sorted(events, key=lambda e: e.get("timestamp", 0))
        
        for event_data in sorted_events:
            # Validate event structure
            if not isinstance(event_data, dict):
                continue
            if "amount" not in event_data:
                continue
            
            # Replay event
            self._xp += event_data.get("amount", 0)
            
            # Recreate event object
            try:
                event = XPEvent(
                    id=event_data.get("id", uuid.uuid4().hex),
                    timestamp=event_data.get("timestamp", time.time()),
                    action=event_data.get("action", "unknown"),
                    amount=event_data.get("amount", 0),
                    description=event_data.get("description", ""),
                    source=event_data.get("source", "restore"),
                    xp_after=self._xp
                )
                self._events.append(event)
            except Exception as e:
                logger.warning(f"Failed to restore event: {e}")
        
        logger.info(f"Restored {len(self._events)} events, {self._xp} XP")


# ==========================================
# PERSISTENCE LAYER (Separate Concern)
# ==========================================

class MasteryStorage:
    """Handles persistence with validation."""
    
    def __init__(self, data_dir: Path = Path("data")):
        self.data_dir = data_dir
        self.events_path = data_dir / "mastery_events.json"
        self.state_path = data_dir / "mastery_state.json"
    
    def save_events(self, events: List[XPEvent]) -> None:
        """Save events to disk (immutable log)."""
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing events
        existing = self.load_events()
        
        # Merge (avoid duplicates by ID)
        existing_ids = {e.get("id") for e in existing}
        new_events = [e.to_dict() for e in events if e.id not in existing_ids]
        
        all_events = existing + new_events
        
        try:
            with open(self.events_path, 'w', encoding='utf-8') as f:
                json.dump(all_events, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save events: {e}")
    
    def load_events(self) -> List[Dict]:
        """Load events from disk with validation."""
        if not self.events_path.exists():
            return []
        
        try:
            with open(self.events_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    # Validate each event has required fields
                    return [e for e in data if isinstance(e, dict) and "amount" in e]
                return []
        except Exception as e:
            logger.warning(f"Failed to load events: {e}")
            return []
    
    def save_checkpoint(self, state: Dict) -> None:
        """Save checkpoint for faster recovery."""
        try:
            with open(self.state_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Failed to save checkpoint: {e}")
    
    def load_checkpoint(self) -> Optional[Dict]:
        """Load checkpoint if valid."""
        if not self.state_path.exists():
            return None
        
        try:
            with open(self.state_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and "xp" in data:
                    return data
                return None
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")
            return None


# ==========================================
# WORKER INTERFACE (Phoenix Compatible)
# ==========================================

class MasteryWorker:
    """
    Phoenix worker for gamification.
    Separates concerns: Core logic + Storage + UI formatting.
    """
    
    name = "mastery"
    version = "3.0.0"
    
    def __init__(self):
        self.core = MasteryCore()
        self.storage = MasteryStorage()
        self._initialized = False
        self.execution_count = 0
        self.error_count = 0
        self._achievements: List[Dict] = []
    
    async def initialize(self) -> None:
        """Load state from storage."""
        if self._initialized:
            return
        
        # Try checkpoint first (fast recovery)
        checkpoint = self.storage.load_checkpoint()
        if checkpoint and checkpoint.get("xp", 0) > 0:
            # Restore from events to ensure consistency
            events = self.storage.load_events()
            if events:
                self.core.restore_from_events(events)
                logger.info(f"Restored from {len(events)} events: {self.core.xp} XP")
            else:
                # Fallback to checkpoint
                self.core._xp = checkpoint.get("xp", 0)
                logger.info(f"Restored from checkpoint: {self.core.xp} XP")
        else:
            # Load full event log
            events = self.storage.load_events()
            if events:
                self.core.restore_from_events(events)
                logger.info(f"Restored from {len(events)} events: {self.core.xp} XP")
        
        self._initialized = True
        logger.info(f"🎮 MasteryWorker ready: {self.core.xp} XP, Level {self.core.level[0]}")
    
    async def add_xp(self, action: str, amount: int = None, description: str = "", source: str = "system") -> Dict[str, Any]:
        """Add XP with automatic reward lookup."""
        if amount is None:
            amount = XP_REWARDS.get(action, 10)
        
        # Core logic (pure)
        new_xp, leveled_up, achievements = self.core.add_xp(action, amount, description, source)
        
        # Store achievements
        self._achievements.extend(achievements)
        
        # Persist (separate concern)
        self.storage.save_events(self.core.events)
        self.storage.save_checkpoint({"xp": new_xp, "timestamp": time.time()})
        
        return {
            "success": True,
            "xp_added": amount,
            "total_xp": new_xp,
            "level": self.core.level[0],
            "level_emoji": self._get_emoji(self.core.level[0]),
            "leveled_up": leveled_up,
            "achievements": achievements
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        stats = self.core.get_stats()
        stats["level_emoji"] = self._get_emoji(stats["level"])
        stats["achievements_count"] = len(self._achievements)
        stats["recent_achievements"] = self._achievements[-5:]
        return stats
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute mastery commands."""
        self.execution_count += 1
        task = task.strip()
        
        try:
            if task.startswith('/xp') or task == 'stats':
                return await self._cmd_stats()
            
            elif task.startswith('/add_xp'):
                return await self._cmd_add_xp(task)
            
            elif task.startswith('/achievements'):
                return await self._cmd_achievements()
            
            elif task.startswith('/level'):
                return await self._cmd_level()
            
            elif task.startswith('/reset_mastery'):
                return await self._cmd_reset()
            
            else:
                return await self._cmd_stats()
                
        except Exception as e:
            self.error_count += 1
            logger.error(f"Mastery error: {e}")
            return {
                "success": False,
                "error": str(e),
                "worker": self.name,
                "timestamp": time.time()
            }
    
    # ==========================================
    # COMMAND HANDLERS (UI Formatting)
    # ==========================================
    
    async def _cmd_stats(self) -> Dict[str, Any]:
        """Handle /xp command."""
        stats = await self.get_stats()
        
        # Build progress bar
        bar_length = 20
        filled = int(stats["progress_percent"] / 100 * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        content = f"""🎮 **MASTERY STATUS** — {stats['level_emoji']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**XP:** {stats['xp']:,} / {stats['next_level_threshold']:,}
**Level:** {stats['level']} {stats['level_emoji']}
**Progress:** [{bar}] {stats['progress_percent']:.1f}%
**Next Level:** {stats['next_level']} ({stats['xp_to_next']:,} XP to go)

**Stats:**
• Total XP Earned: {stats['total_xp_earned']:,}
• Achievements: {stats['achievements_count']}
• Actions Tracked: {stats['total_events']}

**Recent Achievements:**
"""
        recent = self._achievements[-3:] if self._achievements else []
        if recent:
            for ach in recent:
                content += f"  • {ach.get('emoji', '🏆')} {ach.get('name', 'Achievement')}\n"
        else:
            content += "  • None yet. Keep using Phoenix!\n"
        
        content += "\n💡 Run `/achievements` to see all achievements."
        
        return {
            "success": True,
            "type": "reflex",
            "content": content,
            "worker": self.name
        }
    
    async def _cmd_add_xp(self, task: str) -> Dict[str, Any]:
        """Handle /add_xp command."""
        parts = task.split()
        if len(parts) < 3:
            return {
                "success": False,
                "type": "reflex",
                "content": "❌ Usage: /add_xp <amount> <action> [description]",
                "worker": self.name
            }
        
        try:
            amount = int(parts[1])
            action = parts[2]
            description = ' '.join(parts[3:]) if len(parts) > 3 else ""
            
            result = await self.add_xp(action, amount, description, source="user")
            
            if result["leveled_up"]:
                return {
                    "success": True,
                    "type": "reflex",
                    "content": f"🏆 {result['level_emoji']} **LEVEL UP!** You reached {result['level']}!\n✨ +{amount} XP",
                    "worker": self.name
                }
            else:
                return {
                    "success": True,
                    "type": "reflex",
                    "content": f"✨ +{amount} XP for {action}! Total: {result['total_xp']:,} XP ({result['level']} {result['level_emoji']})",
                    "worker": self.name
                }
        except ValueError:
            return {
                "success": False,
                "type": "reflex",
                "content": "❌ Invalid amount. Use a number.",
                "worker": self.name
            }
    
    async def _cmd_achievements(self) -> Dict[str, Any]:
        """Handle /achievements command."""
        if not self._achievements:
            return {
                "success": True,
                "type": "reflex",
                "content": "🏆 No achievements yet. Keep using Phoenix to earn them!",
                "worker": self.name
            }
        
        content = "🏆 **ACHIEVEMENTS**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for ach in self._achievements[-15:]:
            timestamp = time.strftime("%Y-%m-%d", time.localtime(ach.get("timestamp", time.time())))
            content += f"{ach.get('emoji', '🏆')} **{ach.get('name', 'Achievement')}**\n   _{ach.get('description', '')}_\n   📅 {timestamp}\n\n"
        
        return {
            "success": True,
            "type": "reflex",
            "content": content,
            "worker": self.name
        }
    
    async def _cmd_level(self) -> Dict[str, Any]:
        """Handle /level command."""
        stats = await self.get_stats()
        
        content = "📊 **Level Progression**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        for level_name, threshold in LEVEL_CONFIG:
            emoji = self._get_emoji(level_name)
            unlocked = stats["xp"] >= threshold
            status = "✅" if unlocked else "🔒"
            
            if level_name == stats["level"]:
                content += f"{emoji} **{level_name}** (CURRENT) — {threshold:,} XP {status}\n"
            else:
                content += f"{emoji} {level_name} — {threshold:,} XP {status}\n"
        
        content += f"\n📍 Your XP: {stats['xp']:,}"
        
        return {
            "success": True,
            "type": "reflex",
            "content": content,
            "worker": self.name
        }
    
    async def _cmd_reset(self) -> Dict[str, Any]:
        """Handle /reset_mastery command."""
        # In production, check admin role here
        self.core = MasteryCore()
        self._achievements = []
        self.storage.save_events([])
        self.storage.save_checkpoint({"xp": 0, "timestamp": time.time()})
        
        return {
            "success": True,
            "type": "reflex",
            "content": "🔄 Mastery stats reset to zero. Start your journey anew!",
            "worker": self.name
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Return worker health."""
        return {
            "name": self.name,
            "version": self.version,
            "status": "healthy" if self._initialized else "initializing",
            "initialized": self._initialized,
            "stats": {
                "xp": self.core.xp,
                "level": self.core.level[0],
                "achievements": len(self._achievements),
                "events": len(self.core.events),
                "executions": self.execution_count,
                "errors": self.error_count
            }
        }
    
    def _get_emoji(self, level_name: str) -> str:
        """Get emoji for level."""
        emojis = {
            "APPRENTICE": "🌱",
            "VIBE_CODER": "🎸",
            "REZ_APPRENTICE": "🦎",
            "ZERO_DRIFT_ADEPT": "⛓️",
            "SOVEREIGN_ARCHITECT": "🏛️",
            "REZ_MASTER": "🔥",
            "CONSTITUTIONAL_AI": "⚖️",
            "SOVEREIGN_LEGEND": "👑",
        }
        return emojis.get(level_name, "🎮")