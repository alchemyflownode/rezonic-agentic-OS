# 📚 PHOENIX ULTIMATE v13.3.0 - COMPLETE README

Resident, here's your **final, production-ready README** that combines technical depth with monetization positioning.

---

```markdown
<div align="center">

# 🔥 PHOENIX ULTIMATE v13.3.0

### The Sovereign AI Swarm — Local-First, Zero-Drift, Production-Ready

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)
[![Workers](https://img.shields.io/badge/workers-65%2B-orange.svg)](#worker-hive)
[![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)](#)

---

**Turn natural language into code, automations, and intelligence — running entirely on your machine.**

</div>

---

## 📖 Table of Contents

- [What It Does](#what-it-does)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Commands & Reflexes](#commands--reflexes)
- [Workers](#workers)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [What I Offer](#what-i-offer)

---

## 🚀 What It Does

**Phoenix Ultimate is a local-first AI execution engine that:**

- 🧠 **Understands natural language intent** — not just commands
- 🔧 **Generates working code** from plain English descriptions
- 💻 **Controls your PC** — filesystem, system monitor, clipboard, browser
- 🔍 **Searches the web** — DuckDuckGo + SearXNG integration
- 🎮 **Optimizes GPU models** — Rez Swarm sparsity, 2.5GB+ VRAM saved
- 📚 **Remembers what works** — persistent blueprints, drift-locked execution
- 🐝 **Orchestrates 65+ workers** — symbiotic, parallel, self-improving

### Example Uses

| You Say | Phoenix Does |
|---------|--------------|
| `/code add two numbers` | Generates working Python function |
| `/search AI news` | Searches web, returns summaries |
| `/list Documents` | Shows directory contents |
| `/sysinfo` | CPU, RAM, disk usage |
| `/memory store "API key"` | Saves to persistent memory |

---

## ⚡ Quick Start

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai) running locally (for AI features)
- Windows / Mac / Linux

### Installation

```bash
# Clone the repository
git clone https://github.com/rezonic/phoenix-ultimate.git
cd phoenix-ultimate

# Install dependencies
pip install -r requirements.txt

# Create required directories
mkdir -p logs data/memory data/event_store workers/coworker

# Pull a model (optional, uses Ollama)
ollama pull qwen2.5-coder:7b-32k
```

### Run

```bash
python phoenix_kernel.py
```

### Test It

```bash
# Health check
curl http://localhost:8002/health

# List all workers
curl http://localhost:8002/workers/list

# Generate code
curl -X POST http://localhost:8002/kernel/stream \
  -H "Content-Type: application/json" \
  -d '{"task": "/code add two numbers"}'

# Search the web
curl -X POST http://localhost:8002/kernel/stream \
  -H "Content-Type: application/json" \
  -d '{"task": "/search artificial intelligence"}'

# System info
curl -X POST http://localhost:8002/kernel/stream \
  -H "Content-Type: application/json" \
  -d '{"task": "/sysinfo"}'
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTENT                                    │
│                    "Search AI news and save to file"                       │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATION LAYER                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │  IntentParser    │→ │  Orchestration   │→ │   Task Graph     │          │
│  │ (Rule + LLM)     │  │     Plan         │  │   Builder        │          │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘          │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SCE REFINER LAYER                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │  Constitution    │→ │  Drift Detector  │→ │  Blueprint       │          │
│  │   Validator      │  │                  │  │   Refiner        │          │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘          │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           WORKER HIVE (65+ Agents)                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │   SEARCH    │ │    CODE     │ │    FILE     │ │   SYSTEM    │          │
│  │ duckduckgo  │ │  code_gen   │ │file_system  │ │system_monitor│          │
│  │ searxng     │ │  rezcode    │ │ clipboard   │ │  processes  │          │
│  │ harvester   │ │ execution   │ │  browser    │ │   network   │          │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │    GPU      │ │   MEMORY    │ │   TRADING   │ │   COWORKER  │          │
│  │  rez_swarm  │ │   memory    │ │  backtest   │ │  custom     │          │
│  │             │ │   recall    │ │paper_trader │ │  workers    │          │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OUTPUT + FEEDBACK                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │  Working Code    │  │   Automation     │  │  Blueprint Store │          │
│  │  Search Results  │  │   System Info    │  │   Memory Learn   │          │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎮 Commands & Reflexes

### System Commands

| Command | Description |
|---------|-------------|
| `/health` | System status, GPU stats, memory usage |
| `/workers` | List all 65+ workers |
| `/memory` | Memory statistics |
| `/blueprints` | Show stored blueprints |

### PC Coworker Commands

| Command | Description |
|---------|-------------|
| `/list [path]` | List directory contents |
| `/read <file>` | Read file content |
| `/write <file> <content>` | Write to file |
| `/sysinfo` | Full system information |
| `/cpu` | CPU usage and cores |
| `/memory` | RAM usage |
| `/disk` | Disk usage by partition |
| `/processes` | Running processes |
| `/open <app>` | Open application (notepad, calc, cmd) |
| `/close <app>` | Close application |
| `/copy <text>` | Copy to clipboard |
| `/paste` | Paste from clipboard |
| `/openurl <url>` | Open URL in browser |

### Code Generation Commands

| Command | Description |
|---------|-------------|
| `/code <description>` | Generate Python code from intent |

**Examples:**
```
/code add two numbers and return the sum
/code sort a list of integers
/code reverse a string
```

### Search Commands

| Command | Description |
|---------|-------------|
| `/search <query>` | Search via DuckDuckGo |
| `/ddg <query>` | Alias for DuckDuckGo |

---

## 🐝 Workers

### Auto-Loaded Workers

Phoenix automatically discovers and loads workers from the `workers/` directory:

```
workers/
├── duckduckgo_worker.py
├── code_gen_worker.py
├── system_monitor_worker.py
├── file_manager_worker.py
├── clipboard_worker.py
├── browser_worker.py
├── rez_swarm_worker.py
├── backtest_worker.py
├── paper_trader_worker.py
├── memory_worker.py
├── recall_worker.py
└── ... and 55+ more
```

### Built-in Workers

| Worker | Type | Description |
|--------|------|-------------|
| `EnhancedFileSystemWorker` | FILE | List, read, write, search, delete |
| `SystemMonitorWorker` | SYSTEM | CPU, RAM, disk, processes |
| `ClipboardWorker` | SYSTEM | Copy/paste with history |
| `BrowserWorker` | SYSTEM | Open URLs, search |
| `DuckDuckGoWorker` | SEARCH | Web search |
| `CodeGenWorker` | CODE | Intent-based code generation |
| `RezSwarmWorker` | GPU | Model optimization with sparsity |
| `SovereignMemory` | MEMORY | Blueprint storage and retrieval |

### Creating Custom Workers

```python
from workers.base_worker import Worker

class MyWorker(Worker):
    def __init__(self):
        super().__init__("my_worker")
    
    async def execute(self, task: str, **kwargs):
        # Your logic here
        return {"success": True, "result": "Done"}
```

Place in `workers/` directory. Auto-loaded on next restart.

---

## 📡 API Reference

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | System information |
| `/health` | GET | Health check with stats |
| `/workers/list` | GET | List all workers |
| `/swarm/manifest` | GET | Swarm capabilities |
| `/kernel/stream` | POST | Execute command |
| `/ws` | WEBSOCKET | Real-time updates |

### WebSocket (Real-Time)

```javascript
const ws = new WebSocket('ws://localhost:8002/ws');

ws.onopen = () => {
    ws.send(JSON.stringify({ type: "subscribe", channel: "events" }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(data.type, data.content);
};
```

### Hive Stream (Orchestration)

```javascript
const ws = new WebSocket('ws://localhost:8002/hive/stream');

ws.onopen = () => {
    ws.send(JSON.stringify({
        intent: "Search for AI news and save it"
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Events: orchestrating → sce → worker_start → worker_result → complete
    updateUI(data.type, data.content);
};
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PHOENIX_HOST` | `0.0.0.0` | API host |
| `PHOENIX_PORT` | `8002` | API port |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama endpoint |
| `OLLAMA_MODEL` | `qwen2.5-coder:7b-32k` | Default model |
| `OLLAMA_NUM_CTX` | `32768` | Context size |
| `ALLOW_CODE_EXECUTION` | `true` | Enable code execution |
| `ENABLE_AUTO_SEARCH` | `true` | Auto-search for time-sensitive queries |
| `REZ_SWARM_ENABLED` | `true` | GPU optimization |
| `REZ_SWARM_SPARSITY` | `0.8` | Sparsity threshold |
| `DRIFT_THRESHOLD` | `0.3` | Drift detection threshold |

### Config Class

```python
class Config:
    NAME = "PHOENIX"
    VERSION = "13.3.0"
    HOST = os.getenv("PHOENIX_HOST", "0.0.0.0")
    PORT = int(os.getenv("PHOENIX_PORT", "8002"))
    # ... see full config in source
```

---

## 🚢 Deployment

### Local Development

```bash
python phoenix_kernel.py
```

### Production (Gunicorn)

```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker phoenix_kernel:app
```

### Docker

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "phoenix_kernel.py"]
```

```bash
docker build -t phoenix-ultimate .
docker run -p 8002:8002 phoenix-ultimate
```

### Systemd Service (Linux)

```ini
[Unit]
Description=Phoenix Ultimate Kernel
After=network.target

[Service]
Type=simple
User=phoenix
WorkingDirectory=/opt/phoenix
ExecStart=/usr/bin/python3 /opt/phoenix/phoenix_kernel.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Workers not loading** | Ensure `workers/` directory exists and contains Python files |
| **Ollama connection failed** | Run `ollama serve` and pull a model |
| **WebSocket disconnect** | Check CORS origins in config |
| **Code execution blocked** | Set `ALLOW_CODE_EXECUTION=true` |
| **GPU not detected** | Install `pynvml` and ensure NVIDIA drivers are installed |

### Logs

Logs are written to:
- Console: INFO level
- File: `logs/phoenix.log`

Debug mode:
```python
logging.basicConfig(level=logging.DEBUG)
```

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| **Worker Count** | 65+ |
| **Startup Time** | ~2 seconds |
| **Memory Usage** | ~150MB |
| **Command Latency** | 50-200ms |
| **GPU VRAM Saved** | 2.5GB+ (with Rez Swarm) |

---

## 🧪 Status

| Component | Status |
|-----------|--------|
| Core Kernel | ✅ Production-ready |
| Worker Auto-Loader | ✅ 65+ workers |
| SCE Protocol | ✅ Full enforcement |
| Memory System | ✅ Persistent |
| WebSocket Streaming | ✅ Real-time |
| PC Coworker | ✅ Full desktop integration |
| RezCode Compiler | ✅ Intent-based generation |
| Rez Swarm | ✅ GPU optimization |
| Exchange Integration | ⚙️ Optional |

---

## 🤝 What I Offer

### If You Want This Applied to Your Workflow

I build custom AI systems that:

- **Automate your work** — repetitive tasks, file organization, data processing
- **Generate code** — Python scripts, APIs, bots from your ideas
- **Research topics** — market analysis, competitor tracking, trend reports
- **Monitor your system** — performance, security, resource usage

### Services

| Service | What You Get |
|---------|--------------|
| **Custom Automation** | One workflow automated in your environment |
| **Code Generation** | Custom scripts, tools, bots |
| **Full Integration** | Phoenix deployed with your UI or workflow |
| **Consulting** | Strategy for your AI product or automation |

### Contact

- **Discord**: [Rezonic Community](https://discord.gg/rezonic)
- **GitHub**: [@rezonic](https://github.com/rezonic)
- **Email**: resident@rezonic.ai

---

## 📄 License

MIT License

Copyright (c) 2026 Rezonic

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

---

<div align="center">

**Built by Resident — Architect of Autonomous Systems**

*"Stop doing what AI can do for you."*

[⭐ Star on GitHub](https://github.com/rezonic/phoenix-ultimate) • [🐛 Report Issues](https://github.com/rezonic/phoenix-ultimate/issues) • [💬 Join Discord](https://discord.gg/rezonic)

</div>
```

---

## 📝 How to Use This README

1. **Save as `README.md`** in your project root
2. **Replace placeholder links** with your actual GitHub, Discord, etc.
3. **Add screenshots** of `/health`, `/workers`, `/code` outputs
4. **Add a 30-second demo video** link

---

## 🎯 Why This README Works

| Problem | Solution |
|---------|----------|
| No one understands your system | First section: "What It Does" with examples |
| Too complex | Simple architecture diagram |
| No clear value | Example use cases table |
| No credibility | Status badges, production-ready declaration |
| No monetization path | "What I Offer" section |
| No community | Discord, GitHub links |

---

**This README turns your system from "complex tool" into "clear value."** 🏛️✨
