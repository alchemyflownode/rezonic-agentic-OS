import json
import time
from pathlib import Path

# Fix mastery state
state_path = Path("data/mastery_state.json")
if state_path.exists():
    with open(state_path, 'r', encoding='utf-8') as f:
        state = json.load(f)
    
    # Add missing achievements
    if state.get("xp", 0) >= 1000 and "VIBE_CODER" not in str(state.get("achievements", [])):
        achievement = {
            "name": "Reached VIBE_CODER",
            "description": f"Earned {state['xp']} XP total",
            "emoji": "🎸",
            "timestamp": state.get("timestamp", time.time()),
            "xp_attained": state["xp"]
        }
        state.setdefault("achievements", []).append(achievement)
        
        # Save back
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
        print("✅ Added missing VIBE_CODER achievement")
    
    # Also add to event log
    events_path = Path("data/mastery_events.json")
    if events_path.exists():
        with open(events_path, 'r', encoding='utf-8') as f:
            events = json.load(f)
        
        # Check if level up event exists
        has_level_up = any("level_up" in str(e) for e in events)
        if not has_level_up:
            level_up_event = {
                "id": "level_up_vibe_coder",
                "timestamp": state.get("timestamp", time.time()),
                "action": "level_up",
                "amount": 0,
                "description": "Reached VIBE_CODER level",
                "source": "system",
                "xp_after": 1000
            }
            events.append(level_up_event)
            with open(events_path, 'w', encoding='utf-8') as f:
                json.dump(events, f, indent=2)
            print("✅ Added level up event")

print("✅ Achievement fix applied. Restart kernel to see changes.")
