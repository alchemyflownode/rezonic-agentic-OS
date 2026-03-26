import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
@app.get("/okiru/status")
async def okiru_status(request: Request):
    """Get system status"""
    return {
        "status": "OPERATIONAL",
        "workers_loaded": len(request.app.state.__dict__),
        "version": "1.0.0",
        "symbiote": "active"
    }

@app.get("/okiru/manifest")
async def okiru_manifest():
    """Get system manifest"""
    return {
        "workers": [
            "HiveMemoryBus", "HybridOrchestrator", "FilesystemContextWorker",
            "HandsWorker", "VisionWorker", "SystemWorker", "SandboxWorker",
            "RezScannerWorker", "BrainWorker", "ChronosWorker", "CryptoWorker",
            "EyesWorker", "DreamWorker", "AgamotoBridgeWorker", 
            "RezStackWorker", "AppBuilderWorker"
        ],
        "total": 16,
        "status": "ready"
    }

