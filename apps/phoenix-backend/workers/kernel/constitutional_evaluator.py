class ConstitutionalEvaluator:
    def evaluate(self, action: str) -> dict:
        dangerous = ['rm -rf', 'format', 'delete']
        if any(d in action.lower() for d in dangerous):
            return {"approved": False, "reason": "Dangerous action"}
        return {"approved": True, "reason": "All laws satisfied"}
