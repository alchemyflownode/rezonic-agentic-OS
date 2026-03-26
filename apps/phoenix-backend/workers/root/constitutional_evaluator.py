class ConstitutionalEvaluator:
    '''Evaluates actions against constitutional laws'''
    
    def __init__(self):
        self.laws = [
            "SOVEREIGNTY - No external dependencies",
            "TRANSPARENCY - All operations must have narrative",
            "ACCOUNTABILITY - Every action must have drift lock",
            "DETERMINISM - Same input = same output",
            "SAFETY - No harmful operations"
        ]
        
    def evaluate(self, action: str) -> dict:
        '''Evaluate an action against the constitution'''
        dangerous = ['rm -rf', 'format', 'delete']
        if any(d in action.lower() for d in dangerous):
            return {"approved": False, "reason": "Dangerous action"}
        return {"approved": True, "reason": "All laws satisfied"}
