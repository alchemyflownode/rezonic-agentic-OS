#!/usr/bin/env python3
"""
Phoenix Coworker - Main Entry Point

A personal AI coworker for your desktop.

Usage:
    python main.py                    # Start interactive mode
    python main.py --command "organize downloads"
    python main.py --daemon           # Run in background
    python main.py --config custom.yaml
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from core import PhoenixKernel, KernelConfig


def load_config(config_path: Path = None) -> KernelConfig:
    """Load configuration from file or use defaults"""
    import yaml
    
    # Default config locations
    config_locations = [
        config_path,
        Path.home() / ".phoenix" / "config.yaml",
        Path(__file__).parent / "config" / "coworker.yaml",
    ]
    
    config_data = {}
    
    for loc in config_locations:
        if loc and loc.exists():
            try:
                with open(loc, 'r') as f:
                    config_data = yaml.safe_load(f)
                    print(f"Loaded config from: {loc}")
                    break
            except Exception as e:
                print(f"Could not load config from {loc}: {e}")
    
    # Create config with overrides
    kwargs = {}
    
    if config_data:
        if 'data_dir' in config_data:
            kwargs['data_dir'] = Path(config_data['data_dir']).expanduser()
        if 'hotkey' in config_data:
            kwargs['hotkey'] = config_data['hotkey']
        if 'enable_desktop' in config_data:
            kwargs['enable_desktop'] = config_data['enable_desktop']
        if 'enable_file_watching' in config_data:
            kwargs['enable_file_watching'] = config_data['enable_file_watching']
        if 'safety_profile' in config_data:
            kwargs['safety_profile'] = config_data['safety_profile']
        if 'default_llm' in config_data:
            kwargs['default_llm'] = config_data['default_llm']
        if 'ollama_model' in config_data:
            kwargs['ollama_model'] = config_data['ollama_model']
        if 'ollama_url' in config_data:
            kwargs['ollama_url'] = config_data['ollama_url']
        if 'proactive_tasks' in config_data:
            kwargs['proactive_tasks'] = config_data['proactive_tasks']
    
    return KernelConfig(**kwargs)


def print_banner():
    """Print startup banner"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🐦 Phoenix Coworker                                     ║
    ║                                                           ║
    ║   Your personal AI assistant for desktop productivity     ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)


def print_help():
    """Print help message"""
    print("""
Available Commands:
  organize [path]           Organize files in directory (default: ~/Downloads)
  summarize <file>          Summarize a document
  search <query>            Search your memory
  remember <fact>           Store a fact in memory
  recall <query>            Recall information from memory
  plan <goal>               Create and execute a task plan
  run <command>             Execute a shell command
  status                    Show system status
  help                      Show this help message
  exit/quit                 Exit Phoenix

Quick Actions:
  Press Ctrl+Shift+Space    Open quick command overlay
  Right-click tray icon     Access menu options

Examples:
  organize                  Organize Downloads folder
  summarize report.pdf      Summarize a PDF document
  remember "Meeting at 3pm" Store a reminder
  search "project ideas"    Search your memory
    """)


async def run_command(kernel: PhoenixKernel, command: str):
    """Run a single command and exit"""
    result = await kernel.execute(command)
    
    if result.get('success'):
        if 'message' in result:
            print(f"✓ {result['message']}")
        if 'response' in result:
            print(result['response'])
        if 'results' in result:
            for r in result['results']:
                content = r.get('content', r) if isinstance(r, dict) else r
                print(f"  - {str(content)[:80]}...")
        if 'summary' in result:
            print(f"\nSummary:\n{result['summary']}")
        if 'key_points' in result:
            print("\nKey Points:")
            for point in result['key_points']:
                print(f"  • {point}")
    else:
        print(f"✗ {result.get('error', 'Unknown error')}")
    
    await kernel.stop()


async def interactive_mode(kernel: PhoenixKernel):
    """Run in interactive mode"""
    print_banner()
    print_help()
    
    await kernel.start()
    
    try:
        while kernel._running:
            try:
                # Get input
                command = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input("\n🐦 phoenix> ")
                )
                command = command.strip()
                
                if not command:
                    continue
                
                # Handle special commands
                if command.lower() in ['exit', 'quit', 'q']:
                    break
                
                if command.lower() == 'help':
                    print_help()
                    continue
                
                if command.lower() == 'status':
                    kernel._show_status()
                    continue
                
                # Execute command
                result = await kernel.execute(command)
                
                if result.get('success'):
                    if 'message' in result:
                        print(f"✓ {result['message']}")
                    if 'response' in result:
                        print(result['response'])
                    if 'results' in result:
                        for r in result['results']:
                            content = r.get('content', r) if isinstance(r, dict) else r
                            print(f"  - {str(content)[:80]}...")
                    if 'summary' in result:
                        print(f"\nSummary:\n{result['summary']}")
                else:
                    print(f"✗ {result.get('error', 'Unknown error')}")
            
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except Exception as e:
                print(f"Error: {e}")
    
    finally:
        await kernel.stop()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Phoenix Coworker - Your personal AI assistant"
    )
    
    parser.add_argument(
        '-c', '--command',
        help='Execute a single command and exit'
    )
    
    parser.add_argument(
        '--config',
        type=Path,
        help='Path to config file'
    )
    
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run in daemon mode (background)'
    )
    
    parser.add_argument(
        '--no-desktop',
        action='store_true',
        help='Disable desktop integration'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    if args.no_desktop:
        config.enable_desktop = False
    
    # Create kernel
    kernel = PhoenixKernel(config)
    
    # Run based on mode
    if args.command:
        # Single command mode
        await run_command(kernel, args.command)
    
    elif args.daemon:
        # Daemon mode
        print("Starting Phoenix Coworker in daemon mode...")
        await kernel.start()
        
        try:
            # Keep running
            while kernel._running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            await kernel.stop()
    
    else:
        # Interactive mode
        await interactive_mode(kernel)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
