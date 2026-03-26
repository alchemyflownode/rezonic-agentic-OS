# Add to imports
from backend.security.quarantine import quarantine
from backend.constitution.scanner import scanner

# Add to create_fastapi_app:

# ===== QUARANTINE ENDPOINTS =====
@app.get("/quarantine/workers")
async def list_quarantined_workers():
    """List all quarantined workers"""
    return {
        'quarantined': quarantine.get_quarantined_workers(),
        'count': len(quarantine.get_quarantined_workers())
    }

@app.get("/quarantine/files")
async def list_quarantined_files():
    """List all quarantined files"""
    return {
        'quarantined': quarantine.get_quarantined_files(),
        'count': len(quarantine.get_quarantined_files())
    }

@app.get("/quarantine/review")
async def get_review_queue():
    """Get items awaiting human review"""
    return {
        'review_queue': quarantine.get_review_queue(),
        'count': len(quarantine.get_review_queue())
    }

@app.post("/quarantine/restore/{quarantine_id}")
async def restore_worker(quarantine_id: str, target_path: Optional[str] = None):
    """Restore a worker from quarantine"""
    success = quarantine.restore_worker(quarantine_id, target_path)
    if success:
        return {'status': 'restored', 'id': quarantine_id}
    return {'error': 'Restore failed'}, 400

@app.post("/quarantine/scan/{worker_name}")
async def scan_worker(worker_name: str):
    """Manually scan a worker"""
    worker_path = Path(f"workers/{worker_name}.py")
    if not worker_path.exists():
        worker_path = Path(f"backend/workers/{worker_name}.py")
    
    if not worker_path.exists():
        return {'error': 'Worker not found'}, 404
    
    violations = scanner.scan_worker(worker_path)
    
    return {
        'worker': worker_name,
        'violations': violations,
        'violation_count': len(violations),
        'quarantined': any(v['severity'] in ['high', 'critical'] for v in violations)
    }

@app.get("/quarantine/compare/{quarantine_id}")
async def compare_worker(quarantine_id: str):
    """Compare quarantined version with current"""
    return quarantine.compare_with_original(quarantine_id)

@app.post("/quarantine/review/{quarantine_id}")
async def add_to_review(quarantine_id: str, notes: str = ""):
    """Add quarantined item to review queue"""
    success = quarantine.add_to_review(quarantine_id, notes)
    if success:
        return {'status': 'added_to_review', 'id': quarantine_id}
    return {'error': 'Failed to add to review'}, 400