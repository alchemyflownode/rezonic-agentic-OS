📖 Usage Guide
Basic Commands
bash
# Start kernel
python phoenix_kernel.py

# Access API
curl http://localhost:8002/health

# WebSocket connection
wscat -c ws://localhost:8002

# Terminal commands
/list Documents
/read config.json
/search "AI news"
/sysinfo
Natural Language Examples
bash
# Auto-search triggers
"What's the weather today?"
"Latest AI news"
"Bitcoin price"

# PC control
"Open Chrome"
"Show me system info"
"Copy this text to clipboard"

# File operations
"List files in Documents"
"Create a folder called Projects"
"Read my notes.txt file"
API Endpoints
Endpoint	Method	Description
/	GET	System info
/health	GET	Health check
/workers/list	GET	List all workers
/memory/blueprints	GET	Memory blueprints
/constitution/history	GET	Ruling history
/search/ddg	POST	DuckDuckGo search
/kernel/stream	POST	Streaming responses
🔌 API Reference
REST API Examples
python
# Health check
import httpx
response = httpx.get('http://localhost:8002/health')
print(response.json())

# Get workers
response = httpx.get('http://localhost:8002/workers/list')
workers = response.json()

# Search
response = httpx.post('http://localhost:8002/search/ddg', 
                      json={'query': 'AI news'})
results = response.json()

# Streaming response
async with httpx.stream('POST', 'http://localhost:8002/kernel/stream',
                       json={'task': 'What is AI?'}) as response:
    async for line in response.aiter_lines():
        print(line)
WebSocket API
javascript
const socket = io('http://localhost:8002');

socket.on('connect', () => {
    console.log('Connected');
    socket.emit('command', { command: '/health' });
});

socket.on('kernel_response', (data) => {
    console.log('Response:', data);
});

socket.on('workers_update', (data) => {
    console.log('Workers:', data);
});
👷 Worker System
Built-in Workers
Worker	Function	Status
BrainWorker	Reasoning, intent detection	✅
ExecutionWorker	Code execution	✅
FilesystemWorker	File operations	✅
SearchWorker	Web search	✅
SystemMonitorWorker	System monitoring	✅
ClipboardWorker	Clipboard management	✅
BrowserWorker	Browser control	✅
VisionWorker	Image processing	🚧 Beta
VoiceWorker	Speech recognition	🚧 Beta
Creating Custom Workers
python
# workers/my_worker.py
from workers.base_worker import BaseWorker

class MyCustomWorker(BaseWorker):
    def __init__(self):
        super().__init__("my_custom_worker")
    
    async def execute(self, task: str, **kwargs):
        """Your worker logic here"""
        return {
            "success": True,
            "message": f"Processed: {task}",
            "data": kwargs
        }
🔒 Security & Privacy
Protection Layers
Layer	Protection
Constitutional	User-defined rules enforced before actions
Cryptographic	SCE locks verify memory integrity
Network	Local-only by default
Storage	Encrypted blueprints
Audit	Full action logs with hashes
Security Features
✅ No telemetry - Zero data leaves your machine

✅ No cloud dependencies - Runs 100% local

✅ Encrypted storage - AES-256-GCM for blueprints

✅ Constitutional enforcement - Rules before actions

✅ Audit trails - Every action logged and hashed

✅ Sandboxed execution - Isolated code execution

Privacy Guarantees
yaml
Data Storage: Local only, encrypted
Network Calls: None by default (opt-in search)
Telemetry: Zero
Third-party: None
User Control: Full
🔧 Troubleshooting
Common Issues
Issue: Kernel won't start

bash
# Check Python version
python --version  # Should be 3.10+

# Check dependencies
pip list | grep -E "fastapi|uvicorn|httpx"

# Check port availability
netstat -an | findstr :8002
Issue: WebSocket connection failed

bash
# Check if kernel is running
curl http://localhost:8002/health

# Check firewall
# Allow port 8002 in Windows Firewall
Issue: Search not working

bash
# Check internet connection
ping duckduckgo.com

# Test search API
curl http://localhost:8002/search/status
Issue: Workers not loading

bash
# Check workers directory
ls workers/

# Check for errors in logs
tail -f logs/phoenix.log
Logs Location
text
logs/
├── phoenix.log      # Main kernel logs
├── workers.log      # Worker activity
├── errors.log       # Error reports
└── audit.log        # Action audit trail
🗺️ Roadmap
Phase 1: Personal Sovereign (Current - Q4 2026)
Feature	Status	ETA
Local-first architecture	✅ Complete	Now
Constitutional governance	✅ Complete	Now
SCE protocol	✅ Complete	Now
PC coworker capabilities	✅ Complete	Now
Web search integration	✅ Complete	Now
Modern frontend	✅ Complete	Now
43+ workers	✅ Complete	Now
One-command install	🚧 In Progress	Q2 2026
Docker support	🚧 In Progress	Q2 2026
PyPI package	📋 Planned	Q3 2026
Phase 2: Family/Team Sovereign (2027)
Feature	Status	ETA
Multi-user profiles	📋 Planned	Q1 2027
Encrypted sync across devices	📋 Planned	Q2 2027
Role-based permissions	📋 Planned	Q2 2027
Family audit logs	📋 Planned	Q3 2027
Shared constitution	📋 Planned	Q3 2027
iOS/Android apps	🔮 Research	Q4 2027
Phase 3: Community Sovereign (2028+)
Feature	Status	ETA
Sovereign-to-sovereign protocol	🔮 Research	2028
Worker marketplace	🔮 Research	2028
Cross-AI collaboration	🔮 Research	2028
Governance DAO	🔮 Research	2028
Enterprise federation	🔮 Research	2029
Feature Roadmap Details
Q2 2026
One-command install script

Docker container support

Example workflows library

Video tutorials

GitHub Actions CI/CD

Q3 2026
PyPI package (pip install rezhive-os)

Windows installer (.exe)

macOS installer (.dmg)

Linux packages (.deb, .rpm)

Enhanced documentation wiki

Q4 2026
Plugin system

Worker marketplace preview

Performance optimizations

1.0.0 stable release

🤝 Contributing
Development Setup
bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/rezhiveOS-demo.git
cd rezhiveOS-demo

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run linting
flake8 phoenix_kernel.py
black .
Contribution Guidelines
Fork the repository

Create a feature branch: git checkout -b feature/amazing-feature

Commit changes: git commit -m 'Add amazing feature'

Push: git push origin feature/amazing-feature

Open Pull Request

Code Standards
Python: PEP 8

TypeScript: ESLint + Prettier

Documentation: Markdown

Tests: pytest + Jest

📜 License
AGPLv3 License
text
REZ HIVE OS - Sovereign AI Swarm
Copyright (C) 2026 REZ HIVE Collective

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
Key License Terms
Term	Meaning
AGPLv3	Strong copyleft license
Network Copyleft	Running as a service requires open sourcing modifications
Patent Grant	Contributors grant patent rights to users
No Warranty	Software provided "as is"
Your Data	Remains yours, not licensed
📞 Support & Community
Official Channels
GitHub: alchemyflownode/rezhiveOS-demo

Discord: Join the Swarm

Twitter: @rez_hive

Website: rez-hive.io (Coming Soon)

Documentation
API Docs: http://localhost:8002/docs

Wiki: GitHub Wiki

Examples: /examples directory

Reporting Issues
markdown
**Bug Report Template:**
- Version: v13.3.0
- OS: Windows 11 / macOS / Linux
- Python: 3.10.11
- Description: [clear description]
- Steps to reproduce:
  1. ...
  2. ...
- Expected behavior: ...
- Actual behavior: ...
- Logs: [paste relevant logs]
📊 Statistics
Codebase Metrics
Metric	Value
Total Files	344
Lines of Code	47,812
Python	17.1%
TypeScript	61.0%
Workers	43+
API Endpoints	15+
UI Components	50+
Performance
Metric	Value
Startup Time	< 3 seconds
API Response	< 100ms
Search Latency	< 2 seconds
Memory Usage	~200MB
CPU Usage	5-15% idle
🎯 Version History
v13.3.0 (Current - March 2026)
Added:

Complete PC coworker system

Web search integration

43+ specialized workers

Constitutional governance

SCE protocol for memory

Next.js frontend

Legal protection files

Fixed:

Worker loading system

WebSocket connections

Search fallback mechanism

v13.2.0 (Previous)
Initial worker architecture

Basic file operations

System monitoring

Future Releases
See Roadmap section above.

🌟 Acknowledgments
Technologies
FastAPI - Web framework

Next.js - React framework

Ollama - Local LLM

Tailwind CSS - Styling

TypeScript - Type safety

Inspiration
Constitutional AI research

Sovereign computing movement

Privacy-first software philosophy

📝 Final Notes
Project Status
Aspect	Rating
Stability	⭐⭐⭐⭐ Production-ready
Documentation	⭐⭐⭐⭐ Comprehensive
Features	⭐⭐⭐⭐⭐ Revolutionary
Security	⭐⭐⭐⭐⭐ Excellent
Privacy	⭐⭐⭐⭐⭐ Unmatched
Community	⭐⭐ Growing
Get Started Today
bash
# Clone
git clone https://github.com/alchemyflownode/rezhiveOS-demo.git

# Install
cd rezhiveOS-demo && pip install -r requirements.txt

# Run
python phoenix_kernel.py
<div align="center">
Your AI. Your Rules. Your Sovereignty.

Built with 🔥 by the REZ HIVE collective

GitHub • Discord • Twitter

</div>