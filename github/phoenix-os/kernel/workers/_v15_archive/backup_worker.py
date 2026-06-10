# workers/backup_worker.py
"""Backup worker for sovereign memory and state"""

import asyncio
import json
import shutil
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

from workers.base_worker import Worker
from logging_config import get_logger

logger = get_logger("backup_worker")


class BackupWorker(Worker):
    """Worker that handles backup of sovereign memory and state"""
    
    def __init__(self):
        super().__init__("backup_worker")
        self.backup_root = Path("data/backups")
        self.memory_dir = Path("data/memory")
        self.event_store = Path("data/event_store/events.db")
        self.retention_days = 30
        self.backup_root.mkdir(parents=True, exist_ok=True)
    
    async def execute(self, task: str = None, **kwargs) -> Dict[str, Any]:
        """Execute backup task"""
        if task == "backup" or not task:
            return await self._create_backup()
        elif task == "restore":
            backup_id = kwargs.get("backup_id")
            return await self._restore_backup(backup_id)
        elif task == "list":
            return await self._list_backups()
        elif task == "clean":
            return await self._clean_old_backups()
        else:
            return {"error": f"Unknown task: {task}", "success": False}
    
    async def _create_backup(self) -> Dict[str, Any]:
        """Create a full backup of the system"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_root / timestamp
        
        logger.info(f"Creating backup at {backup_path}")
        
        try:
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup memory (11,577 blueprints)
            memory_backup = backup_path / "memory"
            if self.memory_dir.exists():
                shutil.copytree(self.memory_dir, memory_backup)
                memory_count = len(list(memory_backup.rglob("*.json")))
                logger.info(f"  Backed up {memory_count} memory blueprints")
            
            # Backup event store
            if self.event_store.exists():
                shutil.copy2(self.event_store, backup_path / "events.db")
                size_mb = self.event_store.stat().st_size / (1024 * 1024)
                logger.info(f"  Backed up event store ({size_mb:.1f} MB)")
            
            # Backup configuration
            env_file = Path(".env")
            if env_file.exists():
                shutil.copy2(env_file, backup_path / ".env")
                logger.info("  Backed up .env configuration")
            
            # Create manifest
            manifest = {
                "timestamp": timestamp,
                "backup_id": timestamp,
                "files_backed_up": len(list(backup_path.rglob("*"))),
                "size_mb": sum(f.stat().st_size for f in backup_path.rglob("*")) / (1024 * 1024),
                "memory_count": memory_count if 'memory_count' in dir() else 0
            }
            
            # Add integrity hash
            manifest["integrity_hash"] = hashlib.sha256(
                json.dumps(manifest, sort_keys=True).encode()
            ).hexdigest()[:16]
            
            with open(backup_path / "manifest.json", "w") as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"✅ Backup complete: {timestamp} ({manifest['size_mb']:.1f} MB)")
            
            # Clean old backups
            await self._clean_old_backups()
            
            return {
                "success": True,
                "backup_id": timestamp,
                "path": str(backup_path),
                "size_mb": manifest["size_mb"],
                "files": manifest["files_backed_up"],
                "integrity_hash": manifest["integrity_hash"]
            }
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _restore_backup(self, backup_id: str) -> Dict[str, Any]:
        """Restore from a backup"""
        backup_path = self.backup_root / backup_id
        
        if not backup_path.exists():
            return {"success": False, "error": f"Backup not found: {backup_id}"}
        
        logger.info(f"Restoring from backup: {backup_id}")
        
        try:
            # Restore memory
            memory_backup = backup_path / "memory"
            if memory_backup.exists():
                # Backup current state first
                await self._create_backup()
                # Restore
                shutil.rmtree(self.memory_dir)
                shutil.copytree(memory_backup, self.memory_dir)
                logger.info("  Restored memory blueprints")
            
            # Restore event store
            event_backup = backup_path / "events.db"
            if event_backup.exists():
                shutil.copy2(event_backup, self.event_store)
                logger.info("  Restored event store")
            
            return {
                "success": True,
                "restored_from": backup_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _list_backups(self) -> Dict[str, Any]:
        """List all available backups"""
        backups = []
        
        for backup_dir in sorted(self.backup_root.glob("*"), reverse=True):
            if backup_dir.is_dir():
                manifest_file = backup_dir / "manifest.json"
                if manifest_file.exists():
                    with open(manifest_file) as f:
                        manifest = json.load(f)
                    backups.append(manifest)
                else:
                    backups.append({
                        "backup_id": backup_dir.name,
                        "timestamp": backup_dir.name,
                        "size_mb": sum(f.stat().st_size for f in backup_dir.rglob("*")) / (1024 * 1024),
                        "files_backed_up": len(list(backup_dir.rglob("*")))
                    })
        
        return {
            "success": True,
            "backups": backups[:20],
            "total": len(backups)
        }
    
    async def _clean_old_backups(self) -> Dict[str, Any]:
        """Clean backups older than retention_days"""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        deleted = []
        
        for backup_dir in self.backup_root.glob("*"):
            if backup_dir.is_dir():
                try:
                    # Parse timestamp from directory name
                    backup_time = datetime.strptime(backup_dir.name, '%Y%m%d_%H%M%S')
                    
                    if backup_time < cutoff:
                        shutil.rmtree(backup_dir)
                        deleted.append(backup_dir.name)
                        logger.info(f"Deleted old backup: {backup_dir.name}")
                        
                except ValueError:
                    # Not a timestamp directory, skip
                    continue
        
        return {
            "success": True,
            "deleted": deleted,
            "deleted_count": len(deleted)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Return worker health status"""
        return {
            "worker": self.name,
            "status": "healthy",
            "backup_root": str(self.backup_root),
            "backups": len(list(self.backup_root.glob("*"))),
            "retention_days": self.retention_days
        }