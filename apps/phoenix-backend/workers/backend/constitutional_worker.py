"""Constitutional Worker - Enforces system laws using the discovered framework"""

import logging
from pathlib import Path
import sys

# Add constitutional path
sys.path.append(str(Path(__file__).parent.parent / 'constitutional'))

from constitutional_governor import ConstitutionalGovernor
from constitutional_evaluator import ConstitutionalEvaluator
from ollama_constitutional_enhanced import OllamaConstitutional

logger = logging.getLogger(__name__)

class ConstitutionalWorker:
    """
    The Conscience of RezHiveOS - Uses the discovered constitutional framework
    to ensure all actions comply with system laws.
    """
    
    def __init__(self, hive_bus=None):
        self.governor = ConstitutionalGovernor()
        self.evaluator = ConstitutionalEvaluator()
        self.ollama_constitutional = OllamaConstitutional()
        self.violations = []
        
    async def process(self, task: str, memory_bus=None) -> dict:
        """Evaluate actions against the constitution"""
        
        # Parse the action
        # Format: /constitution evaluate "action description"
        
        if "evaluate" in task:
            action = task.replace("/constitution evaluate", "").strip()
            result = await self._evaluate_action(action)
            return {"content": result}
            
        elif "violations" in task:
            return {"content": self._get_violations_report()}
            
        elif "import" in task:
            # Import constitutional documents into Hive
            return {"content": await self._import_constitutional_docs(memory_bus)}
            
        else:
            return {"content": self._get_help()}
    
    async def _evaluate_action(self, action: str) -> str:
        """Evaluate an action against constitutional laws"""
        
        # Use the constitutional evaluator
        evaluation = self.evaluator.evaluate(action)
        
        if evaluation['approved']:
            return f"✅ **ACTION APPROVED**\n\nReasoning: {evaluation['reasoning']}"
        else:
            self.violations.append({
                'action': action,
                'reason': evaluation['reasoning'],
                'severity': evaluation['severity']
            })
            return f"❌ **ACTION DENIED**\n\nViolation: {evaluation['reasoning']}\nSeverity: {evaluation['severity']}"
    
    async def _import_constitutional_docs(self, memory_bus) -> str:
        """Import constitutional documents into the Hive Mind"""
        if not memory_bus:
            return "❌ No memory bus available"
            
        docs_path = Path(__file__).parent.parent / 'constitutional' / 'docs'
        imported = 0
        
        for doc_file in docs_path.glob('*.md'):
            with open(doc_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            await memory_bus.store(
                content=content,
                metadata={
                    'source': 'constitution',
                    'document': doc_file.name,
                    'type': 'governance'
                }
            )
            imported += 1
            
        return f"✅ Imported {imported} constitutional documents into Hive Mind"
    
    def _get_violations_report(self) -> str:
        """Generate violations report"""
        if not self.violations:
            return "✅ No constitutional violations recorded"
            
        report = "📋 **CONSTITUTIONAL VIOLATIONS**\n\n"
        for v in self.violations[-10:]:  # Last 10
            report += f"• {v['action']}: {v['reason']} (Severity: {v['severity']})\n"
            
        return report
    
    def _get_help(self) -> str:
        return """⚖️ **CONSTITUTIONAL WORKER**

Commands:
  /constitution evaluate <action>  - Check if action follows laws
  /constitution violations          - Show recent violations
  /constitution import              - Import constitutional docs into Hive
"""
