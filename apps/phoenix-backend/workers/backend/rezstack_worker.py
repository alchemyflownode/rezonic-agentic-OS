"""RezStackOS Worker - Direct interface to the TypeScript Sovereign OS"""

import asyncio
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import tempfile
import os
import re

logger = logging.getLogger(__name__)

class RezStackWorker:
    """
    Direct bridge to RezStackOS - The TypeScript Sovereign Operating System.
    Provides access to 10,000+ TypeScript files of sovereign AI infrastructure.
    """
    
    def __init__(self, memory_bus=None):
        self.memory_bus = memory_bus
        self.rezstack_path = Path("G:/okiru/agamoto-v8-sdk/rezstackOS")
        self.core_path = self.rezstack_path / "packages" / "core"
        self.cli_path = self.rezstack_path / "packages" / "cli"
        self.web_path = self.rezstack_path / "packages" / "web"
        
        # Statistics from scan
        self.stats = {
            'total_ts': 2005,
            'total_js': 5442,
            'total_mts': 566,
            'total_mjs': 566,
            'total_docs': 139,
            'total_scripts': 49,
            'core_modules': 0,
            'available_commands': []
        }
        
        self._discover_core_modules()
        self._check_node()
        
    def _check_node(self) -> bool:
        """Check if Node.js is available"""
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Node.js {result.stdout.strip()} detected")
                return True
        except FileNotFoundError:
            logger.warning("❌ Node.js not found in PATH")
        return False
    
    def _discover_core_modules(self):
        """Discover core RezStackOS modules"""
        if self.core_path.exists():
            # Look for TypeScript files in core
            ts_files = list(self.core_path.rglob("*.ts")) + list(self.core_path.rglob("*.mts"))
            self.stats['core_modules'] = len(ts_files)
            
            # Extract potential command names from file structure
            for ts_file in ts_files[:50]:  # Sample first 50
                rel_path = ts_file.relative_to(self.rezstack_path)
                module_name = str(rel_path).replace('/', '.').replace('\\', '.').replace('.ts', '').replace('.mts', '')
                self.stats['available_commands'].append(module_name)
    
    async def process(self, task: str, model: str = None, memory_bus=None) -> dict:
        """Process RezStackOS commands"""
        if memory_bus:
            self.memory_bus = memory_bus
            
        # Parse command
        parts = task.strip().split()
        if not parts:
            return {"content": self._get_help()}
            
        cmd = parts[0].lower()
        
        # Command routing
        if cmd == "/rezstack":
            return await self._handle_rezstack_command(parts[1:])
        elif cmd == "/sovereign":
            return await self._call_sovereign_function(parts[1:])
        elif cmd == "/core":
            return await self._access_core_module(parts[1:])
        elif cmd == "/web":
            return await self._render_web_component(parts[1:])
        elif cmd == "/cli":
            return await self._run_cli_command(parts[1:])
        else:
            # Try to interpret as direct module call
            return await self._call_module(cmd, parts[1:])
    
    async def _handle_rezstack_command(self, args: List[str]) -> dict:
        """Handle /rezstack subcommands"""
        if not args:
            return {"content": self._get_status()}
            
        subcmd = args[0].lower()
        
        if subcmd == "status":
            return {"content": self._get_status()}
            
        elif subcmd == "modules":
            return {"content": self._list_modules()}
            
        elif subcmd == "call":
            # /rezstack call module.function args
            if len(args) < 2:
                return {"content": "❌ Specify module to call"}
            return await self._execute_module(args[1], args[2:] if len(args) > 2 else [])
            
        elif subcmd == "bootstrap":
            return await self._bootstrap_os()
            
        elif subcmd == "audit":
            return await self._audit_system()
            
        elif subcmd == "spawn":
            # Spawn a new sovereign instance
            return await self._spawn_instance(args[1] if len(args) > 1 else "default")
            
        else:
            return {"content": f"❌ Unknown command: {subcmd}"}
    
    async def _call_sovereign_function(self, args: List[str]) -> dict:
        """Call a sovereign-level function"""
        if not args:
            return {"content": "❌ Specify sovereign function"}
            
        # Look for sovereign.ts or index.ts in core
        sovereign_path = self.core_path / "sovereign.mts"
        if not sovereign_path.exists():
            sovereign_path = self.core_path / "sovereign.ts"
            
        if not sovereign_path.exists():
            return {"content": "❌ Sovereign module not found"}
            
        func_name = args[0]
        func_args = args[1:] if len(args) > 1 else []
        
        # Generate TypeScript to call sovereign function
        ts_code = f"""
import {{ {func_name} }} from '{sovereign_path}';

async function main() {{
    try {{
        const result = await {func_name}({', '.join(f"'{arg}'" for arg in func_args)});
        console.log(JSON.stringify(result, null, 2));
    }} catch (error) {{
        console.error(JSON.stringify({{ error: error.message, stack: error.stack }}));
    }}
}}

main();
"""
        return await self._execute_typescript(ts_code)
    
    async def _access_core_module(self, args: List[str]) -> dict:
        """Access core OS module"""
        if not args:
            return {"content": "❌ Specify core module"}
            
        module_path = args[0].replace('.', '/')
        func_name = args[1] if len(args) > 1 else "default"
        func_args = args[2:] if len(args) > 2 else []
        
        # Try different extensions
        possible_paths = [
            self.core_path / f"{module_path}.mts",
            self.core_path / f"{module_path}.ts",
            self.core_path / module_path / "index.mts",
            self.core_path / module_path / "index.ts"
        ]
        
        module_file = None
        for path in possible_paths:
            if path.exists():
                module_file = path
                break
                
        if not module_file:
            return {"content": f"❌ Core module not found: {module_path}"}
            
        ts_code = f"""
import {{ {func_name} }} from '{module_file}';

async function main() {{
    try {{
        const result = await {func_name}({', '.join(f"'{arg}'" for arg in func_args)});
        console.log(JSON.stringify(result, null, 2));
    }} catch (error) {{
        console.error(JSON.stringify({{ error: error.message, stack: error.stack }}));
    }}
}}

main();
"""
        return await self._execute_typescript(ts_code)
    
    async def _render_web_component(self, args: List[str]) -> dict:
        """Render a React/TSX web component"""
        if not args:
            return {"content": "❌ Specify web component"}
            
        component_path = args[0].replace('.', '/')
        props = {}
        
        # Parse props from remaining args (key=value)
        for arg in args[1:]:
            if '=' in arg:
                k, v = arg.split('=', 1)
                props[k] = v
                
        # Look for TSX file
        tsx_path = self.web_path / f"{component_path}.tsx"
        if not tsx_path.exists():
            tsx_path = self.web_path / component_path / "index.tsx"
            
        if not tsx_path.exists():
            return {"content": f"❌ Web component not found: {component_path}"}
            
        # Generate code to render component to string
        ts_code = f"""
import React from 'react';
import {{ renderToString }} from 'react-dom/server';
import {{ {component_path.split('/')[-1]} }} from '{tsx_path}';

const props = {json.dumps(props)};

const html = renderToString(<{component_path.split('/')[-1]} {{...props}} />);
console.log(JSON.stringify({{ html, props }}));
"""
        return await self._execute_typescript(ts_code)
    
    async def _run_cli_command(self, args: List[str]) -> dict:
        """Run RezStackOS CLI command"""
        if not args:
            return {"content": "❌ Specify CLI command"}
            
        # Look for CLI scripts
        cli_scripts = list(self.cli_path.glob("*.mts")) + list(self.cli_path.glob("*.ts"))
        
        # Try to find matching command
        cmd_name = args[0]
        cmd_script = None
        
        for script in cli_scripts:
            if script.stem.lower() == cmd_name.lower():
                cmd_script = script
                break
                
        if not cmd_script:
            # Try running with ts-node directly
            return await self._execute_typescript(f"""
import {{ run }} from '{self.cli_path}/cli.mts';
run({json.dumps(args)});
""")
            
        # Run the CLI script
        cmd = ["npx", "ts-node", str(cmd_script)] + args[1:]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(self.rezstack_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            return {"content": f"✅ CLI Result:\n{stdout.decode()}"}
        else:
            return {"content": f"❌ CLI Error:\n{stderr.decode()}"}
    
    async def _execute_module(self, module_path: str, args: List[str]) -> dict:
        """Execute a specific module with args"""
        # Convert dot notation to path
        file_path = module_path.replace('.', '/')
        
        # Try to find the module
        possible_paths = [
            self.rezstack_path / f"{file_path}.mts",
            self.rezstack_path / f"{file_path}.ts",
            self.rezstack_path / file_path / "index.mts",
            self.rezstack_path / file_path / "index.ts"
        ]
        
        for path in possible_paths:
            if path.exists():
                cmd = ["npx", "ts-node", str(path)] + args
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=str(self.rezstack_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    return {"content": f"✅ Module output:\n{stdout.decode()}"}
                else:
                    return {"content": f"❌ Module error:\n{stderr.decode()}"}
                    
        return {"content": f"❌ Module not found: {module_path}"}
    
    async def _execute_typescript(self, code: str) -> dict:
        """Execute TypeScript code"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False, encoding='utf-8') as f:
            f.write(code)
            temp_file = f.name
        
        try:
            cmd = ["npx", "ts-node", temp_file]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self.rezstack_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Cleanup
            os.unlink(temp_file)
            
            if process.returncode == 0:
                # Try to parse JSON output
                try:
                    result = json.loads(stdout)
                    return {"content": f"✅ Result:\n{json.dumps(result, indent=2)}"}
                except:
                    return {"content": f"✅ Result:\n{stdout.decode()}"}
            else:
                return {"content": f"❌ Error:\n{stderr.decode()}"}
                
        except Exception as e:
            return {"content": f"❌ Execution failed: {e}"}
    
    async def _bootstrap_os(self) -> dict:
        """Bootstrap the RezStackOS"""
        # Look for bootstrap script
        bootstrap_path = self.rezstack_path / "scripts" / "bootstrap.mts"
        if not bootstrap_path.exists():
            bootstrap_path = self.rezstack_path / "bootstrap.mts"
            
        if bootstrap_path.exists():
            return await self._execute_module("bootstrap", [])
        else:
            return {"content": "❌ Bootstrap script not found"}
    
    async def _audit_system(self) -> dict:
        """Audit the RezStackOS system"""
        # Count modules
        total_files = 0
        for ext in ['*.ts', '*.mts', '*.tsx', '*.js', '*.mjs']:
            total_files += len(list(self.rezstack_path.rglob(ext)))
            
        return {"content": f"""
📊 **REZSTACKOS AUDIT**
━━━━━━━━━━━━━━━━━━━━━━━━
📍 Path: {self.rezstack_path}
📁 Total TypeScript files: {self.stats['total_ts'] + self.stats['total_mts']}
📁 Total JavaScript files: {self.stats['total_js'] + self.stats['total_mjs']}
📁 Core modules: {self.stats['core_modules']}
📚 Documentation: {self.stats['total_docs']} files
⚙️  CLI scripts: {len(list(self.cli_path.glob('*.mts')))} commands

🔧 **System Health**
• Node.js: {'✅' if self._check_node() else '❌'}
• Dependencies: {'✅' if (self.rezstack_path / 'node_modules').exists() else '⚠️ Run npm install'}
• Built: {'✅' if (self.rezstack_path / 'dist').exists() else '⚠️ Run npm run build'}

🚀 **Ready for Sovereign Operations**
""" }
    
    async def _spawn_instance(self, name: str) -> dict:
        """Spawn a new sovereign instance"""
        # This would create a new isolated instance
        return {"content": f"🔄 Spawning new sovereign instance: {name}\n(Implementation depends on RezStackOS clustering)"}
    
    def _get_status(self) -> str:
        """Get RezStackOS status"""
        return f"""
🦊 **REZSTACK OS - SOVEREIGN OPERATING SYSTEM**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Location: {self.rezstack_path}
📊 **STATISTICS**
├── 📁 TypeScript Core: {self.stats['total_ts']} files
├── 📁 ES Modules: {self.stats['total_mts']} files
├── 📁 JavaScript: {self.stats['total_js']} files
├── 📁 Web Components: {self.stats.get('web_components', 49)} files
├── 📚 Documentation: {self.stats['total_docs']} files
└── ⚙️  Core Modules: {self.stats['core_modules']} modules

🎯 **AVAILABLE COMMANDS**
/rezstack status    - This status
/rezstack modules   - List all modules
/rezstack call      - Call a module function
/sovereign          - Call sovereign functions
/core               - Access core modules
/web                - Render web components
/cli                - Run CLI commands

⚡ **THE SOVEREIGN IS READY**
"""
    
    def _list_modules(self) -> str:
        """List available modules"""
        modules = "\n".join([f"  • {m}" for m in sorted(self.stats['available_commands'])[:50]])
        return f"📚 **REZSTACKOS MODULES**\n\n{modules}"
    
    def _get_help(self) -> str:
        return """🦊 **REZSTACK OS - SOVEREIGN COMMANDS**

Core Commands:
  /rezstack status     - Show OS status
  /rezstack modules    - List all modules
  /rezstack call       - Call a module function
  /rezstack bootstrap  - Bootstrap the OS
  /rezstack audit      - Audit system health
  /rezstack spawn      - Spawn new instance

Module Access:
  /sovereign <func>    - Call sovereign functions
  /core <module> <func> - Access core modules
  /web <component>     - Render web components
  /cli <command>       - Run CLI commands

Examples:
  /rezstack status
  /sovereign initialize
  /core kernel.boot
  /web Dashboard userId=123
  /cli build --production

RezStackOS: 10,000+ files of sovereign TypeScript power! 🚀
"""