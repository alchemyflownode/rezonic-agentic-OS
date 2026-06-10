# 🐦 Phoenix Coworker

A personal AI coworker for your desktop. Phoenix helps you stay organized, remembers important information, and automates routine tasks.

## Features

- **🧠 Unified Memory** - Remembers conversations, files, and facts with semantic search
- **🛡️ Safety First** - Built-in safety guard prevents dangerous actions
- **📋 Task Planning** - Breaks down complex goals into executable steps
- **🖥️ Desktop Integration** - System tray, global hotkeys, and file watching
- **🔧 Essential Workers** - Brain, filesystem, execution, vision, and voice
- **📁 Smart Organization** - Automatically organizes your Downloads folder
- **📝 Document Summarization** - Summarizes PDFs and documents
- **🌅 Morning Briefings** - Daily summary of calendar, emails, and tasks

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd phoenix-coworker

# Install dependencies
pip install -r requirements.txt

# For full functionality (optional)
pip install chromadb sentence-transformers networkx  # Memory
pip install pystray Pillow keyboard watchdog          # Desktop
pip install pyttsx3 SpeechRecognition PyAudio         # Voice
pip install PyAutoGUI                                 # Vision
```

### Configuration

Edit `config/coworker.yaml` or create `~/.phoenix/config.yaml`:

```yaml
# LLM Configuration
default_llm: ollama
ollama_model: llama3.2
ollama_url: http://localhost:11434

# Desktop integration
hotkey: ctrl+shift+space
enable_desktop: true
enable_file_watching: true
```

### Running

```bash
# Interactive mode
python main.py

# Execute a single command
python main.py --command "organize downloads"

# Daemon mode (background)
python main.py --daemon

# Custom config
python main.py --config myconfig.yaml
```

## Architecture

```
phoenix-coworker/
├── core/                   # Core components
│   ├── kernel.py          # Main orchestrator
│   ├── event_bus.py       # Event system
│   ├── unified_memory.py  # Memory consolidation
│   ├── safety.py          # Safety guard
│   └── task_planner.py    # Task planning
├── workers/               # Specialized workers
│   ├── base.py            # Base worker class
│   ├── brain.py           # LLM integration
│   ├── filesystem.py      # File operations
│   ├── execution.py       # Code execution
│   ├── vision.py          # Screen capture
│   └── voice.py           # TTS/STT
├── desktop/               # Desktop integration
│   └── presence.py        # Tray, hotkeys, watchers
├── skills/                # Task-specific skills
│   ├── organize_files.py
│   ├── summarize.py
│   ├── morning_briefing.py
│   └── code_review.py
├── config/
│   └── coworker.yaml      # Default configuration
├── main.py                # Entry point
└── requirements.txt
```

## Commands

### File Operations
```
organize [path]           # Organize files by type
summarize <file>          # Summarize a document
search <query>            # Search your memory
```

### Memory
```
remember <fact>           # Store a fact
recall <query>            # Recall information
```

### Tasks
```
plan <goal>               # Create and execute a plan
run <command>             # Execute shell command
```

### System
```
status                    # Show system status
help                      # Show help
exit/quit                 # Exit Phoenix
```

## Comparison: Old vs New

| Aspect | Before (Trading AI) | After (Personal Coworker) |
|--------|--------------------|---------------------------|
| Workers | 56 files | 6 essential workers |
| Governance | 4 constitutional files | 1 simple safety guard |
| Memory | 4 fragmented systems | 1 unified memory |
| Architecture | Distributed trading system | Unified desktop assistant |
| Desktop | None | Full integration |
| Proactive | None | File watching, scheduled tasks |

## Migration from Phoenix Backend

If you're migrating from the old Phoenix backend:

1. **Backup your data**:
   ```bash
   cp -r ~/.phoenix ~/.phoenix.backup
   ```

2. **Install new dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Migrate memory** (optional):
   ```python
   from core.unified_memory import UnifiedMemory
   # Your old memory will be preserved in new format
   ```

4. **Update configuration**:
   - Copy your old settings to `~/.phoenix/config.yaml`
   - Remove trading-specific settings

## License

MIT License - See LICENSE file

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Acknowledgments

- Built with ❤️ for personal productivity
- Inspired by the original Phoenix project
- Uses Ollama for local LLM inference
