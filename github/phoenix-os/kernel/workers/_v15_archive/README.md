# Phoenix Workers

This directory contains 47 worker modules that extend Phoenix kernel functionality.

## Worker Categories

### Core System
- system_monitor - CPU, memory, GPU monitoring
- code_execution - Sandboxed Python code execution
- code_gen - Code generation from natural language
- vscode_integration - VS Code and Copilot integration

### Trading
- paper_trader - Paper trading simulation
- backtest - Strategy backtesting
- exchange_worker - Exchange connectivity

### Constitutional AI
- ConstitutionalCouncilWorker - Safety council
- ConstitutionalGovernorWorker - Governance enforcement
- ConstitutionalRouterWorker - Request routing

### Memory & Storage
- memory_worker - Blueprint storage and retrieval
- sovereign_mcp_server - MCP protocol server

### Media & Generation
- comfyui_generator - Image generation
- audio_worker - Audio processing
- vision_worker - Computer vision

### Integration
- rezcoder - Code review and fixing
- mastery_worker - XP and achievement system
- file_manager - File operations

## Adding New Workers

1. Create a new Python file in this directory
2. Implement the Worker base class
3. Define execute() method
4. Worker will be auto-discovered on restart

## Disabled Workers

Move unused workers to _disabled/ folder to prevent loading.
