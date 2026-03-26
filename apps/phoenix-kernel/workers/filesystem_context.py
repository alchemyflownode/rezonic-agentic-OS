from base_worker import Worker

class FilesystemContext(Worker):
    def __init__(self):
        super().__init__("filesystem_context")
    
    async def execute(self, task: str, **kwargs):
        return {
            "success": True,
            "worker": "filesystem_context",
            "message": f"filesystem_context: {task[:100]}"
        }
