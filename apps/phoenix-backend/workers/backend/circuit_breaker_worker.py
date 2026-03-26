# backend/workers/circuit_breaker_worker.py
class CircuitBreakerWorker:
    def __init__(self, max_failures=3, cooldown=10):
        self.max_failures = max_failures
        self.cooldown = cooldown
        self.failure_count = 0
        self.last_failure = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def execute_with_protection(self, func, *args, **kwargs):
        now = time.time()
        
        # Check if circuit is OPEN
        if self.state == "OPEN":
            if now - self.last_failure > self.cooldown:
                self.state = "HALF_OPEN"
                print("🔄 Circuit HALF-OPEN - testing recovery")
            else:
                raise Exception("Circuit OPEN - rejecting request")
        
        try:
            result = await func(*args, **kwargs)
            
            # Success - reset if HALF_OPEN
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                print("✅ Circuit CLOSED - recovered successfully")
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure = now
            
            if self.failure_count >= self.max_failures:
                self.state = "OPEN"
                print(f"🔴 Circuit OPEN after {self.failure_count} failures")
            
            raise e