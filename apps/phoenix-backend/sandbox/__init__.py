"""Windows Sandbox Package"""
from .windows_sandbox import WindowsSandboxExecutor

# Create a placeholder config if needed
class WindowsSandboxConfig:
    def __init__(self, config_dict=None):
        self.disable_network = True
        self.max_memory_mb = 2048
        self.max_execution_time_sec = 300

__all__ = ['WindowsSandboxExecutor', 'WindowsSandboxConfig']
