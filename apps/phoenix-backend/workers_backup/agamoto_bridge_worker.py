from .base_worker import BaseWorker
﻿import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
"""Agamoto Bridge Worker - Connects Python RezHive to TypeScript Agamoto SDK"""

import asyncio
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import tempfile
import os

logger = logging.getLogger(__name__)

class AgamotoBridgeWorker(BaseWorker):
    """
    Bridges RezHiveOS (Python) with Agamoto V8 SDK (TypeScript/JavaScript).
    Executes TypeScript code via Node.js and returns results to the Hive Mind.
    """
    
    def __init__(self, memory_bus=None, hive_bus=None):
        self.memory_bus = memory_bus
        super().__init__('agamotobridge', hive_bus)
        self.sdk_path = Path("G:/okiru/agamoto-v8-sdk")
        self.node_modules = self.sdk_path / "node_modules"
        self.has_node = self._check_node()
        self.sdk_modules = self._discover_sdk_modules()
        
    def _check_node(self) -> bool:
        """Check if Node.js is available"""
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"âœ… Node.js {result.stdout.strip()} detected")
                return True
        except FileNotFoundError:
            logger.warning("âŒ Node.js not found in PATH")
        return False
    
    def _discover_sdk_modules(self) -> List[str]:
        """Discover available Agamoto SDK modules"""
        modules = []
        src_path = self.sdk_path / "src"
        if src_path.exists():
            for ts_file in src_path.rglob("*.ts"):
                if "node_modules" not in str(ts_file):
                    rel_path = ts_file.relative_to(self.sdk_path)
                    modules.append(str(rel_path))
        logger.info(f"ðŸ“¦ Discovered {len(modules)} Agamoto SDK modules")
        return modules[:20]  # Limit for display
    
    async def process(self, task: str, model: str = None, memory_bus=None) -> dict:
        """Process Agamoto SDK commands"""
        if memory_bus:
            self.memory_bus = memory_bus
            
        if not self.has_node:
            return {"content": self._get_node_instructions()}
            
        # Parse command
        parts = task.strip().split()
        if not parts:
            return {"content": self._get_help()}
            
        cmd = parts[0].lower()
        
        if cmd == "/agamoto":
            return await self._handle_agamoto_command(parts[1:])
        elif cmd == "/ts":
            return await self._execute_typescript(' '.join(parts[1:]))
        elif cmd == "/sdk":
            return await self._call_sdk_function(parts[1:])
        else:
            return {"content": self._get_help()}
    
    async def _handle_agamoto_command(self, args: List[str]) -> dict:
        """Handle /agamoto subcommands"""
        if not args:
            return {"content": self._get_help()}
            
        subcmd = args[0].lower()
        
        if subcmd == "status":
            return {"content": self._get_status()}
            
        elif subcmd == "modules":
            return {"content": self._list_modules()}
            
        elif subcmd == "run":
            # /agamoto run module.function args
            if len(args) < 2:
                return {"content": "âŒ Specify module to run"}
            return await self._run_sdk_module(args[1], args[2:] if len(args) > 2 else [])
            
        elif subcmd == "build":
            return await self._build_sdk()
            
        elif subcmd == "test":
            return await self._run_tests()
            
        else:
            return {"content": f"âŒ Unknown command: {subcmd}"}
    
    async def _execute_typescript(self, code: str) -> dict:
        """Execute TypeScript code snippet"""
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
            # Add imports for Agamoto SDK
            wrapped_code = f"""
import * as agamoto from '{self.sdk_path}/src/index';

async function main() {{
    try {{
        {code}
    }} catch (error) {{
        console.error(JSON.stringify({{ error: error.message }}));
    }}
}}

main().then(() => process.exit(0));
"""
            f.write(wrapped_code)
            temp_file = f.name
        
        try:
            # Execute with ts-node
            cmd = ["npx", "ts-node", temp_file]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self.sdk_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Cleanup
            os.unlink(temp_file)
            
            if process.returncode == 0:
                return {"content": f"âœ… Result:\n{stdout.decode()}"}
            else:
                return {"content": f"âŒ Error:\n{stderr.decode()}"}
                
        except Exception as e:
            return {"content": f"âŒ Execution failed: {e}"}
    
    async def _call_sdk_function(self, args: List[str]) -> dict:
        """Call a specific SDK function"""
        if not args:
            return {"content": "âŒ Specify function to call"}
            
        func_path = args[0]
        func_args = args[1:] if len(args) > 1 else []
        
        # Generate TypeScript to call the function
        ts_code = f"""
const result = await agamoto.{func_path}({', '.join(f"'{arg}'" for arg in func_args)});
console.log(JSON.stringify(result, null, 2));
"""
        return await self._execute_typescript(ts_code)
    
    async def _run_sdk_module(self, module_path: str, args: List[str]) -> dict:
        """Run an SDK module directly"""
        # Look for the module file
        module_file = self.sdk_path / "src" / f"{module_path.replace('.', '/')}.ts"
        if not module_file.exists():
            # Try with index.ts
            module_file = self.sdk_path / "src" / module_path.replace('.', '/') / "index.ts"
            
        if not module_file.exists():
            return {"content": f"âŒ Module not found: {module_path}"}
            
        # Run the module with ts-node
        cmd = ["npx", "ts-node", str(module_file)] + args
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(self.sdk_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            # Try to parse as JSON
            try:
                result = json.loads(stdout)
                return {"content": f"âœ… Result:\n{json.dumps(result, indent=2)}"}
            except:
                return {"content": f"âœ… Result:\n{stdout.decode()}"}
        else:
            return {"content": f"âŒ Error:\n{stderr.decode()}"}
    
    async def _build_sdk(self) -> dict:
        """Build the TypeScript SDK"""
        cmd = ["npm", "run", "build"]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(self.sdk_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            return {"content": "âœ… SDK built successfully"}
        else:
            return {"content": f"âŒ Build failed:\n{stderr.decode()}"}
    
    async def _run_tests(self) -> dict:
        """Run SDK tests"""
        cmd = ["npm", "test"]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(self.sdk_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        return {"content": f"Test results:\n{stdout.decode()}"}
    
    def _get_status(self) -> str:
        """Get SDK status"""
        status = f"""
ðŸ“Š **AGAMOTO V8 SDK STATUS**
â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
ðŸ“ Path: {self.sdk_path}
ðŸŸ¢ Node.js: {'âœ… Available' if self.has_node else 'âŒ Not found'}
ðŸ“¦ SDK Modules: {len(self.sdk_modules)} discovered
ðŸ“ TypeScript files: {len(list(self.sdk_path.rglob('*.ts')))} 
ðŸ“ JavaScript files: {len(list(self.sdk_path.rglob('*.js')))}
ðŸ”§ Build ready: {'âœ…' if (self.sdk_path / 'dist').exists() else 'âŒ Not built'}

Run '/agamoto modules' to see available modules.
"""
        return status
    
    def _list_modules(self) -> str:
        """List available SDK modules"""
        if not self.sdk_modules:
            return "âŒ No modules discovered"
            
        modules = "\n".join([f"  â€¢ {m}" for m in sorted(self.sdk_modules)[:30]])
        if len(self.sdk_modules) > 30:
            modules += f"\n  ... and {len(self.sdk_modules) - 30} more"
            
        return f"ðŸ“š **AGAMOTO SDK MODULES**\n\n{modules}"
    
    def _get_node_instructions(self) -> str:
        return """âŒ **Node.js Required**

To use the Agamoto V8 SDK, install Node.js:

1. Download from: https://nodejs.org/
2. Install (include in PATH)
3. Restart terminal
4. Run: npm install -g ts-node typescript

Then cd to SDK and install dependencies:
  cd G:\\okiru\\agamoto-v8-sdk
  npm install
"""
    
    def _get_help(self) -> str:
        return """ðŸ¤– **AGAMOTO V8 SDK BRIDGE**

Commands:
  /agamoto status           - Show SDK status
  /agamoto modules          - List available modules
  /agamoto run <module>     - Run an SDK module
  /agamoto build           - Build the SDK
  /agamoto test            - Run tests
  /ts <code>               - Execute TypeScript code
  /sdk <function> <args>   - Call SDK function

Examples:
  /agamoto status
  /ts const result = await agamoto.core.initialize();
  /sdk core.version
  /agamoto run examples/basic

The Agamoto V8 SDK provides sovereign AI capabilities in TypeScript!
"""

    async def process(self, task: str, memory_bus=None):
        """Process task – auto-generated stub"""
        return {"content": f"Processed: {task[:50]}", "worker": self.name}
    
    async def health_check(self):
        """Return worker health status"""
        return {"worker": self.name, "status": "healthy", "timestamp": __import__('time').time()}

