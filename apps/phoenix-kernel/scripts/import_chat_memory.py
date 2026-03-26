# Add this to your _setup_routes() method in phoenix_kernel_v14c.py

@self.app.post("/memory/store")
async def memory_store(request: Request):
    """Store a blueprint directly into sovereign memory"""
    try:
        data = await request.json()
        
        # Create blueprint if not already one
        if "master_drift_lock" not in data:
            blueprint = SCEProtocol.create_blueprint(
                intent={"type": data.get("type", "import"), "source": data.get("source", "api")},
                dna={"imported_at": datetime.now().isoformat()},
                execution={"data": data}
            )
        else:
            blueprint = data
        
        # Store in memory
        drift_lock = sovereign_memory.store_blueprint(blueprint)
        
        # Also store in memory manager if available
        if hasattr(self, 'memory_manager'):
            await self.memory_manager.store(blueprint, data.get("task", "API Import"), "import")
        
        return {
            "success": True,
            "drift_lock": drift_lock,
            "message": f"Stored blueprint with lock: {drift_lock}"
        }
        
    except Exception as e:
        logger.error(f"Failed to store memory: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )