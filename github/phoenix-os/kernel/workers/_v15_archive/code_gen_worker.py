#!/usr/bin/env python3
"""
Code Generation Worker — Generate actual code from blueprint or intent.
"""

import hashlib
import json
from typing import Any, Dict, List, Optional

try:
    from workers.base_worker import Worker
except ImportError:
    try:
        from base_worker import Worker
    except ImportError:
        class Worker:
            def __init__(self, name: str = "worker") -> None:
                self.name = name
                self.execution_count = 0
                self.error_count = 0
            async def initialize(self) -> None:
                pass
            async def execute(self, task: str, **kwargs: Any) -> Dict[str, Any]:
                return {"error": "not implemented"}
            async def health_check(self) -> Dict[str, Any]:
                return {"status": "unknown"}


class CodeGenWorker(Worker):
    def __init__(self) -> None:
        super().__init__("code_gen")
        self.description = "Code generation from blueprints and intents"

    async def initialize(self) -> None:
        pass

    async def execute(self, task: str, **kwargs: Any) -> Dict[str, Any]:
        self.execution_count += 1
        blueprint = kwargs.get("blueprint", {})
        intent = kwargs.get("intent", "")

        if blueprint:
            return await self._generate_from_blueprint(blueprint)
        elif intent or (task and task != "generate"):
            actual_intent = intent if intent else task
            return await self._generate_from_intent(actual_intent, kwargs)
        else:
            self.error_count += 1
            return {"success": False, "error": "Provide blueprint or intent", "worker": self.name}

    async def _generate_from_blueprint(self, blueprint: Dict[str, Any]) -> Dict[str, Any]:
        if not self._verify_blueprint(blueprint):
            return {"success": False, "error": "Blueprint integrity failed", "worker": self.name}
        files = await self._generate_files(blueprint)
        code_hash = hashlib.sha256(json.dumps(files).encode()).hexdigest()[:16]
        return {"success": True, "files": files, "code_hash": code_hash, "worker": self.name}

    async def _generate_from_intent(self, intent: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        language = kwargs.get("language", "python")
        if language == "python":
            code = f'"""Generated stub for: {intent}"""\n\ndef generated():\n    # TODO: implement\n    pass\n'
        else:
            code = f"// Generated stub for: {intent}\nfunction generated() {{\n    // TODO: implement\n}}\n"
        code_hash = hashlib.sha256(code.encode()).hexdigest()[:16]
        return {"success": True, "code": code, "language": language, "code_hash": code_hash, "worker": self.name}

    def _verify_blueprint(self, blueprint: Dict[str, Any]) -> bool:
        stored_lock = blueprint.get("drift_lock")
        if not stored_lock:
            return False
        data = {k: v for k, v in blueprint.items() if k != "drift_lock"}
        computed = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]
        return stored_lock == computed

    async def _generate_files(self, blueprint: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []

    async def health_check(self) -> Dict[str, Any]:
        return {"name": self.name, "status": "healthy", "executions": self.execution_count, "errors": self.error_count}
