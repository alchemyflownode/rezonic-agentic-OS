#!/usr/bin/env python3
"""
Migration script from Phoenix Backend to Phoenix Coworker

Helps migrate data from the old trading-focused system to the new
personal coworker system.
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime


def migrate_memory(old_data_dir: Path, new_data_dir: Path):
    """Migrate memory data from old system"""
    print("\n📦 Migrating memory data...")
    
    # Old memory locations
    old_locations = [
        old_data_dir / "hive_memory",
        old_data_dir / "memory",
        old_data_dir / "cortex_memory.json",
    ]
    
    migrated_count = 0
    
    for location in old_locations:
        if not location.exists():
            continue
        
        print(f"  Found: {location}")
        
        if location.is_dir():
            # Copy directory contents
            dest = new_data_dir / "memory_legacy" / location.name
            shutil.copytree(location, dest, dirs_exist_ok=True)
            print(f"  Copied to: {dest}")
            migrated_count += 1
        
        elif location.is_file():
            # Copy file
            dest = new_data_dir / "memory_legacy" / location.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(location, dest)
            print(f"  Copied to: {dest}")
            migrated_count += 1
    
    if migrated_count == 0:
        print("  No old memory data found")
    else:
        print(f"  Migrated {migrated_count} items")
    
    return migrated_count


def migrate_config(old_config: Path, new_config: Path):
    """Migrate configuration"""
    print("\n⚙️  Migrating configuration...")
    
    if not old_config.exists():
        print("  No old config found")
        return False
    
    try:
        # Read old config
        with open(old_config, 'r') as f:
            old_data = json.load(f)
        
        # Extract relevant settings
        new_data = {
            "data_dir": "~/.phoenix",
            "hotkey": old_data.get("hotkey", "ctrl+shift+space"),
            "enable_desktop": old_data.get("enable_desktop", True),
            "enable_file_watching": old_data.get("enable_file_watching", True),
            "safety_profile": "balanced",
            "default_llm": old_data.get("llm_backend", "ollama"),
            "ollama_model": old_data.get("ollama_model", "llama3.2"),
            "ollama_url": old_data.get("ollama_url", "http://localhost:11434"),
        }
        
        # Write new config
        import yaml
        with open(new_config, 'w') as f:
            yaml.dump(new_data, f, default_flow_style=False)
        
        print(f"  Migrated config to: {new_config}")
        return True
    
    except Exception as e:
        print(f"  Could not migrate config: {e}")
        return False


def create_backup(source: Path, backup_dir: Path):
    """Create backup of old system"""
    print("\n💾 Creating backup...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"phoenix_backup_{timestamp}"
    
    if source.exists():
        shutil.copytree(source, backup_path, dirs_exist_ok=True)
        print(f"  Backup created: {backup_path}")
        return backup_path
    else:
        print("  No data to backup")
        return None


def print_migration_report(old_dir: Path, new_dir: Path, backup_path: Path):
    """Print migration report"""
    print("\n" + "="*50)
    print("  Migration Report")
    print("="*50)
    
    print(f"\n📁 Old data: {old_dir}")
    print(f"📁 New data: {new_dir}")
    if backup_path:
        print(f"💾 Backup: {backup_path}")
    
    print("\n✅ Migration complete!")
    print("\nNext steps:")
    print("  1. Review your new config: ~/.phoenix/config.yaml")
    print("  2. Install new dependencies: pip install -r requirements.txt")
    print("  3. Start Phoenix Coworker: python main.py")
    print("\n⚠️  Note: Old trading workers have been deprecated.")
    print("   If you need them, they're in the backup.")


def main():
    """Main migration function"""
    print("\n" + "="*50)
    print("  Phoenix Migration Tool")
    print("  From: Trading AI System")
    print("  To: Personal Coworker")
    print("="*50)
    
    # Default paths
    old_data_dir = Path.home() / ".phoenix_legacy"
    new_data_dir = Path.home() / ".phoenix"
    backup_dir = Path.home() / ".phoenix_backups"
    
    # Allow custom paths
    if len(sys.argv) > 1:
        old_data_dir = Path(sys.argv[1]).expanduser()
    
    print(f"\nSource: {old_data_dir}")
    print(f"Destination: {new_data_dir}")
    
    # Confirm
    response = input("\nProceed with migration? (yes/no): ").lower().strip()
    if response not in ('yes', 'y'):
        print("Migration cancelled")
        return
    
    # Create directories
    new_data_dir.mkdir(parents=True, exist_ok=True)
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Create backup
    backup_path = create_backup(old_data_dir, backup_dir)
    
    # Migrate data
    migrate_memory(old_data_dir, new_data_dir)
    
    # Migrate config
    old_config = old_data_dir / "config.json"
    new_config = new_data_dir / "config.yaml"
    migrate_config(old_config, new_config)
    
    # Print report
    print_migration_report(old_data_dir, new_data_dir, backup_path)
    
    print("\n🐦 Welcome to Phoenix Coworker!")


if __name__ == "__main__":
    main()
