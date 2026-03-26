"""Agentic Audit Skills Package"""
from .agentic_audit import AgenticAuditAgent

class RezHiveAgenticAuditSkill:
    def __init__(self, hive_instance):
        self.hive = hive_instance
        self.skill_name = "agentic_audit"
        self.version = "1.0.0"
        
    def audit_app(self, app_path: str, config=None, callback=None):
        agent = AgenticAuditAgent(app_path, rez_trader_callback=callback)
        return agent.run_audit()

__all__ = ['AgenticAuditAgent', 'RezHiveAgenticAuditSkill']
