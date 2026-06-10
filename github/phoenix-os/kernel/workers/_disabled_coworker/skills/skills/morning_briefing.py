"""
Morning Briefing Skill for Phoenix Coworker

Generates a daily morning briefing with relevant information.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


class MorningBriefingSkill:
    """
    Skill for generating morning briefings.
    
    Compiles:
    - Calendar events
    - Recent emails
    - Pending tasks
    - Weather
    - News (optional)
    """
    
    def __init__(self, kernel=None):
        self.kernel = kernel
    
    async def generate(self) -> Dict:
        """
        Generate a morning briefing.
        
        Returns:
            Briefing content
        """
        # Gather data
        calendar = await self._get_calendar_events()
        emails = await self._get_emails()
        tasks = await self._get_pending_tasks()
        weather = await self._get_weather()
        
        # Compile briefing
        briefing_data = {
            "calendar": calendar,
            "emails": emails,
            "tasks": tasks,
            "weather": weather,
            "date": datetime.now().strftime("%Y-%m-%d %A"),
            "time": datetime.now().strftime("%H:%M")
        }
        
        # Generate narrative
        narrative = await self._generate_narrative(briefing_data)
        
        # Save briefing
        await self._save_briefing(briefing_data, narrative)
        
        return {
            "success": True,
            "date": briefing_data["date"],
            "narrative": narrative,
            "data": briefing_data
        }
    
    async def _get_calendar_events(self) -> List[Dict]:
        """Get today's calendar events"""
        # Placeholder - would integrate with calendar API
        # For now, return mock data or check memory
        
        if self.kernel and hasattr(self.kernel, 'memory'):
            results = await self.kernel.memory.recall(
                "calendar event today meeting",
                limit=10
            )
            
            events = []
            for r in results:
                if 'calendar' in r.content.lower() or 'meeting' in r.content.lower():
                    events.append({
                        "title": r.content[:50],
                        "time": r.timestamp.strftime("%H:%M") if r.timestamp else "TBD"
                    })
            
            return events
        
        return []
    
    async def _get_emails(self) -> List[Dict]:
        """Get recent unread emails"""
        # Placeholder - would integrate with email API
        
        if self.kernel and hasattr(self.kernel, 'memory'):
            results = await self.kernel.memory.recall(
                "email unread important",
                limit=5
            )
            
            emails = []
            for r in results:
                emails.append({
                    "subject": r.content[:50],
                    "from": r.source,
                    "time": r.timestamp.strftime("%H:%M") if r.timestamp else ""
                })
            
            return emails
        
        return []
    
    async def _get_pending_tasks(self) -> List[Dict]:
        """Get pending tasks from memory"""
        if self.kernel and hasattr(self.kernel, 'memory'):
            results = await self.kernel.memory.recall(
                "task todo pending",
                limit=10
            )
            
            tasks = []
            for r in results:
                tasks.append({
                    "task": r.content[:60],
                    "created": r.timestamp.strftime("%Y-%m-%d") if r.timestamp else ""
                })
            
            return tasks
        
        return []
    
    async def _get_weather(self) -> Dict:
        """Get weather information"""
        # Placeholder - would integrate with weather API
        return {
            "location": "Your Location",
            "temperature": "--",
            "condition": "Check weather app",
            "high": "--",
            "low": "--"
        }
    
    async def _generate_narrative(self, data: Dict) -> str:
        """Generate narrative briefing using brain worker"""
        if self.kernel and hasattr(self.kernel, 'get_worker'):
            brain = self.kernel.get_worker('brain')
            if brain:
                prompt = f"""Generate a friendly morning briefing for {data['date']}.

Calendar: {len(data['calendar'])} events
Emails: {len(data['emails'])} unread
Tasks: {len(data['tasks'])} pending

Keep it concise and encouraging."""
                
                result = await brain.process(prompt, {})
                return result.get('response', self._fallback_narrative(data))
        
        return self._fallback_narrative(data)
    
    def _fallback_narrative(self, data: Dict) -> str:
        """Fallback narrative when brain not available"""
        lines = [
            f"Good morning! Here's your briefing for {data['date']}:",
            "",
            f"📅 You have {len(data['calendar'])} events today.",
            f"📧 {len(data['emails'])} unread emails.",
            f"✅ {len(data['tasks'])} pending tasks.",
            "",
            "Have a productive day!"
        ]
        
        return '\n'.join(lines)
    
    async def _save_briefing(self, data: Dict, narrative: str):
        """Save briefing to notes"""
        notes_dir = Path.home() / "Documents" / "Notes" / "Briefings"
        notes_dir.mkdir(parents=True, exist_ok=True)
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        briefing_file = notes_dir / f"briefing_{date_str}.md"
        
        content = f"""# Morning Briefing - {data['date']}

{narrative}

## Details

### Calendar Events ({len(data['calendar'])})
"""
        for event in data['calendar']:
            content += f"- {event.get('time', 'TBD')}: {event.get('title', 'Event')}\n"
        
        content += f"\n### Unread Emails ({len(data['emails'])})\n"
        for email in data['emails']:
            content += f"- {email.get('from', 'Unknown')}: {email.get('subject', 'No subject')}\n"
        
        content += f"\n### Pending Tasks ({len(data['tasks'])})\n"
        for task in data['tasks']:
            content += f"- {task.get('task', 'Task')}\n"
        
        content += "\n---\n*Generated by Phoenix Coworker*\n"
        
        briefing_file.write_text(content)


# Convenience function
async def generate_briefing() -> Dict:
    """Quick function to generate a morning briefing"""
    skill = MorningBriefingSkill()
    return await skill.generate()
