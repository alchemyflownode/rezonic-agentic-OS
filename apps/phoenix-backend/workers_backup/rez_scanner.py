from .base_worker import BaseWorker
﻿import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
"""
Rez Scanner Module - Omniscient Project Ingestion
Parses local codebases and injects structural awareness into the Hive Mind.
"""
import os
import ast
import hashlib
import logging
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

class RezScannerWorker(BaseWorker):
    def __init__(self, hive_bus=None):
        # Ignore heavy or irrelevant directories to prevent Memory bloat
        super().__init__('rezscanner', hive_bus)
        self.ignored_dirs = {'.git', '__pycache__', 'node_modules', 'venv', 'env', '.next', 'backup_src'}
        self.supported_text = {'.txt', '.md', '.csv', '.json', '.env', '.ps1'}
        logger.info("ðŸ” RezScanner Omniscient Module initialized")

    async def process(self, target_path, memory_bus=None):
        self.memory_bus = memory_bus
        
        logger.info(f"ðŸ” SCANNING: {target_path}")
        
        path = Path(target_path)
        if not path.exists():
            return {"content": f"âŒ Path not found: {target_path}"}

        self.stats = {
            'files': 0,
            'functions': 0,
            'classes': 0,
            'skipped': 0
        }

        # Route logic based on whether it's a file or folder
        if path.is_file():
            await self._process_file(path)
        else:
            for root, dirs, files in os.walk(path):
                # Filter out ignored directories
                dirs[:] =[d for d in dirs if d not in self.ignored_dirs]
                for file in files:
                    file_path = Path(root) / file
                    await self._process_file(file_path)

        report = (
            f"âš¡ **[Rez Scanner Complete]**\n\n"
            f"ðŸ“Š **SCAN REPORT**\n"
            f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            f"ðŸ“ Location: {target_path}\n"
            f"ðŸ“‚ Files scanned: {self.stats['files']}\n"
            f"â­ï¸ Skipped directories: {len(self.ignored_dirs)} patterns\n"
            f"âš™ï¸ Functions found: {self.stats['functions']}\n"
            f"ðŸ›ï¸ Classes found: {self.stats['classes']}\n\n"
            f"ðŸ’¡ The Hive Mind grows stronger... ðŸ\n"
        )
        
        logger.info(f"   âœ… Scanned: {self.stats['files']} files")
        return {"content": report, "worker": "scanner"}

    async def _process_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.stats['files'] += 1

            if file_path.suffix == '.py':
                await self._scan_python_file(file_path, content)
            elif file_path.suffix in self.supported_text or file_path.suffix in {'.ts', '.tsx', '.js', '.jsx', '.css'}:
                await self._scan_text_file(file_path, content)
            
        except UnicodeDecodeError:
            # Binary file or non-utf8
            self.stats['skipped'] += 1
        except Exception as e:
            logger.error(f"Error scanning {file_path.name}: {e}")

    async def _scan_python_file(self, file_path, content):
        try:
            tree = ast.parse(content)
            functions =[node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            classes =[node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            imports =[node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]

            self.stats['functions'] += len(functions)
            self.stats['classes'] += len(classes)

            # ========================================================
            # ðŸ”§ USER FIX 1: PROPER MEMORY BUS SIGNATURE
            # ========================================================
            if self.memory_bus and hasattr(self.memory_bus, 'store'):
                doc_id = hashlib.md5(content.encode()).hexdigest()
                
                # Extract docstrings
                docstrings =[]
                for node in functions + classes:
                    docstring = ast.get_docstring(node)
                    if docstring:
                        docstrings.append(docstring)
                
                # FIXED: Create a title and proper content for memory storage
                title = f"Code: {file_path.name}"
                memory_content = f"""
File: {file_path.name}
Path: {file_path}
Type: Python
Functions: {len(functions)}
Classes: {len(classes)}
Imports: {len(imports)}

Preview:
{content[:500]}...
"""
                # Handle both async cortex and sync hive bus seamlessly
                if asyncio.iscoroutinefunction(self.memory_bus.store):
                    await self.memory_bus.store(
                        title=title,
                        content=memory_content.strip(),
                        source="rez_scanner",
                        metadata={
                            'filename': file_path.name,
                            'path': str(file_path),
                            'type': 'python',
                            'functions': len(functions),
                            'classes': len(classes),
                            'imports': len(imports),
                            'has_docstrings': len(docstrings) > 0,
                            'doc_id': doc_id
                        }
                    )
                else:
                    self.memory_bus.store(title, memory_content.strip())

        except SyntaxError:
            pass # Not valid python, skip parsing

    async def _scan_text_file(self, file_path, content):
        # ========================================================
        # ðŸ”§ USER FIX 2: PROPER DOCUMENT STORAGE
        # ========================================================
        if self.memory_bus and hasattr(self.memory_bus, 'store'):
            title = f"Document: {file_path.name}"
            doc_content = f"""
File: {file_path.name}
Path: {file_path}
Type: {file_path.suffix[1:]}
Size: {len(content)} bytes

Preview:
{content[:500]}...
"""
            if asyncio.iscoroutinefunction(self.memory_bus.store):
                await self.memory_bus.store(
                    title=title,
                    content=doc_content.strip(),
                    source="rez_scanner",
                    metadata={
                        'filename': file_path.name,
                        'path': str(file_path),
                        'type': file_path.suffix[1:],
                        'size': len(content)
                    }
                )
            else:
                self.memory_bus.store(title, doc_content.strip())

    async def process(self, task: str, memory_bus=None):
        """Process task – auto-generated stub"""
        return {"content": f"Processed: {task[:50]}", "worker": self.name}
    
    async def health_check(self):
        """Return worker health status"""
        return {"worker": self.name, "status": "healthy", "timestamp": __import__('time').time()}

