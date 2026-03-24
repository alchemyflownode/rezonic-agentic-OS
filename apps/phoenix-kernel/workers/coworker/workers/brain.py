"""
Brain Worker for Phoenix Coworker

Handles LLM interactions and intelligent processing.
Supports Ollama (local) and OpenAI (cloud) backends.
"""

import os
import json
import aiohttp
from typing import Dict, List, Optional, Any
from .base import BaseWorker


class BrainWorker(BaseWorker):
    """
    Brain worker for LLM interactions.
    
    Supports:
    - Ollama (local models)
    - OpenAI (cloud API)
    """
    
    def __init__(self, kernel: Any):
        super().__init__(kernel, "brain")
        self.config = kernel.config
        
        # Ollama config
        self.ollama_url = self.config.ollama_url
        self.ollama_model = self.config.ollama_model
        
        # OpenAI config (if available)
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = "gpt-4"
        
        # Conversation history
        self._history: List[Dict] = []
        self._max_history = 20
        
        # System prompt
        self._system_prompt = """You are Phoenix, a helpful AI coworker running on the user's personal computer.
You have access to:
- File system operations
- Code execution
- Memory (you can remember and recall information)
- Task planning

Be concise, helpful, and proactive. When appropriate, suggest actions the user might want to take.
"""
    
    async def run(self):
        """Brain worker doesn't need a continuous loop"""
        while self._running:
            await asyncio.sleep(1)
    
    async def process(self, command: str, context: Dict = None) -> Dict:
        """Process a command using LLM"""
        context = context or {}
        
        # Check which backend to use
        if self.config.default_llm == "ollama":
            return await self._ollama_chat(command, context)
        elif self.config.default_llm == "openai" and self.openai_key:
            return await self._openai_chat(command, context)
        else:
            return {
                "success": False,
                "error": f"LLM backend '{self.config.default_llm}' not available"
            }
    
    async def _ollama_chat(self, prompt: str, context: Dict) -> Dict:
        """Chat with Ollama"""
        try:
            # Build messages
            messages = [
                {"role": "system", "content": self._system_prompt}
            ]
            
            # Add history
            for msg in self._history[-self._max_history:]:
                messages.append(msg)
            
            # Add current prompt
            messages.append({"role": "user", "content": prompt})
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/chat",
                    json={
                        "model": self.ollama_model,
                        "messages": messages,
                        "stream": False
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        reply = data["message"]["content"]
                        
                        # Update history
                        self._history.append({"role": "user", "content": prompt})
                        self._history.append({"role": "assistant", "content": reply})
                        
                        return {
                            "success": True,
                            "response": reply,
                            "model": self.ollama_model
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Ollama returned {response.status}"
                        }
        
        except aiohttp.ClientError as e:
            return {
                "success": False,
                "error": f"Cannot connect to Ollama: {e}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _openai_chat(self, prompt: str, context: Dict) -> Dict:
        """Chat with OpenAI"""
        try:
            import openai
            
            client = openai.AsyncOpenAI(api_key=self.openai_key)
            
            messages = [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response = await client.chat.completions.create(
                model=self.openai_model,
                messages=messages
            )
            
            reply = response.choices[0].message.content
            
            return {
                "success": True,
                "response": reply,
                "model": self.openai_model
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def execute(self, action: str, parameters: Dict) -> Any:
        """Execute a brain action (for task planner)"""
        if action == "summarize":
            content = parameters.get("content", "")
            return await self._summarize(content)
        
        elif action == "classify_files":
            files = parameters.get("files", [])
            return self._classify_files(files)
        
        elif action == "review_code":
            code = parameters.get("code", "")
            return await self._review_code(code)
        
        elif action == "generate_briefing":
            data = parameters.get("data", {})
            return await self._generate_briefing(data)
        
        elif action == "breakdown_goal":
            goal = parameters.get("goal", "")
            return await self._breakdown_goal(goal)
        
        return f"[Brain action '{action}' not implemented]"
    
    async def _summarize(self, content: str) -> str:
        """Summarize content"""
        prompt = f"Please summarize the following content concisely:\n\n{content[:4000]}"
        result = await self._ollama_chat(prompt, {})
        return result.get("response", "Could not generate summary")
    
    def _classify_files(self, files: List[str]) -> Dict[str, List[str]]:
        """Classify files by type"""
        categories = {
            "documents": [],
            "images": [],
            "videos": [],
            "archives": [],
            "code": [],
            "other": []
        }
        
        doc_exts = ['.pdf', '.doc', '.docx', '.txt', '.md', '.rtf']
        img_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']
        vid_exts = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        arc_exts = ['.zip', '.tar', '.gz', '.bz2', '.7z', '.rar']
        code_exts = ['.py', '.js', '.ts', '.html', '.css', '.java', '.cpp', '.c', '.go', '.rs']
        
        for file in files:
            path = str(file).lower()
            if any(path.endswith(ext) for ext in doc_exts):
                categories["documents"].append(file)
            elif any(path.endswith(ext) for ext in img_exts):
                categories["images"].append(file)
            elif any(path.endswith(ext) for ext in vid_exts):
                categories["videos"].append(file)
            elif any(path.endswith(ext) for ext in arc_exts):
                categories["archives"].append(file)
            elif any(path.endswith(ext) for ext in code_exts):
                categories["code"].append(file)
            else:
                categories["other"].append(file)
        
        return categories
    
    async def _review_code(self, code: str) -> Dict:
        """Review code for issues"""
        prompt = f"Review this code for bugs, security issues, and improvements:\n\n```\n{code[:3000]}\n```"
        result = await self._ollama_chat(prompt, {})
        
        return {
            "review": result.get("response", "Could not review code"),
            "issues": [],  # Would parse from response
            "suggestions": []
        }
    
    async def _generate_briefing(self, data: Dict) -> str:
        """Generate morning briefing"""
        calendar = data.get("calendar", [])
        emails = data.get("emails", [])
        tasks = data.get("tasks", [])
        weather = data.get("weather", {})
        
        prompt = f"""Generate a concise morning briefing:

Calendar ({len(calendar)} events):
{json.dumps(calendar[:5], indent=2)}

Emails ({len(emails)} unread):
{json.dumps(emails[:3], indent=2)}

Pending tasks ({len(tasks)}):
{json.dumps(tasks[:5], indent=2)}

Weather: {json.dumps(weather)}

Provide a brief, helpful summary."""
        
        result = await self._ollama_chat(prompt, {})
        return result.get("response", "Could not generate briefing")
    
    async def _breakdown_goal(self, goal: str) -> Dict:
        """Break down a goal into steps"""
        prompt = f"""Break down this goal into specific, actionable steps:

Goal: {goal}

Respond with a JSON array of steps, each with:
- name: short identifier
- description: what to do
- tool: which tool to use (filesystem, brain, execution, memory, system)
- action: specific action
- parameters: any parameters needed
- depends_on: list of step names this depends on (can be empty)

Example:
[
  {{"name": "analyze", "description": "Analyze the situation", "tool": "brain", "action": "analyze", "parameters": {{}}, "depends_on": []}},
  {{"name": "execute", "description": "Execute the plan", "tool": "execution", "action": "run", "parameters": {{}}, "depends_on": ["analyze"]}}
]"""
        
        result = await self._ollama_chat(prompt, {})
        
        try:
            # Try to parse JSON from response
            response = result.get("response", "[]")
            # Extract JSON if wrapped in code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            steps = json.loads(response.strip())
            return {"steps": steps}
        except json.JSONDecodeError:
            # Fallback: return generic steps
            return {
                "steps": [
                    {
                        "name": "analyze",
                        "description": f"Analyze how to achieve: {goal}",
                        "tool": "brain",
                        "action": "analyze",
                        "parameters": {"goal": goal},
                        "depends_on": []
                    },
                    {
                        "name": "execute",
                        "description": "Execute the plan",
                        "tool": "execution",
                        "action": "execute",
                        "parameters": {"goal": goal},
                        "depends_on": ["analyze"]
                    }
                ]
            }
