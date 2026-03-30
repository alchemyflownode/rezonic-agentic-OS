# core/circuit_breaker.py
import time
import threading
import logging

logger = logging.getLogger(__name__)

class CircuitBreaker:
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(self, max_failures=5, cooldown=60, half_open_max_calls=3):
        self.failures = 0
        self.max_failures = max_failures
        self.cooldown = cooldown
        self.half_open_max_calls = half_open_max_calls
        self.last_failure_time = 0
        self.state = self.CLOSED
        self.half_open_calls = 0
        self._lock = threading.Lock()

    def record_failure(self):
        """Record a failure - thread safe"""
        with self._lock:
            self.failures += 1
            self.last_failure_time = time.time()
            
            if self.failures >= self.max_failures:
                old_state = self.state
                self.state = self.OPEN
                if old_state != self.OPEN:
                    logger.critical(f"CIRCUIT BREAKER OPENED after {self.failures} failures")

    def record_success(self):
        """Record a success - thread safe"""
        with self._lock:
            if self.state == self.HALF_OPEN:
                self.half_open_calls += 1
                if self.half_open_calls >= self.half_open_max_calls:
                    self.reset()
                    logger.info("Circuit breaker CLOSED after successful half-open period")
            elif self.state == self.CLOSED:
                self.failures = 0  # Reset on success

    def reset(self):
        """Reset circuit breaker - thread safe"""
        with self._lock:
            self.failures = 0
            self.state = self.CLOSED
            self.half_open_calls = 0

    def should_stop(self) -> bool:
        """Check if execution should be blocked"""
        with self._lock:
            if self.state == self.OPEN:
                if time.time() - self.last_failure_time > self.cooldown:
                    self.state = self.HALF_OPEN
                    self.half_open_calls = 0
                    logger.warning("Circuit breaker HALF_OPEN - testing recovery")
                    return False
                return True
            return False

    def allow_request(self) -> bool:
        """Check if a request should be allowed (for half-open state)"""
        with self._lock:
            if self.state == self.HALF_OPEN:
                if self.half_open_calls < self.half_open_max_calls:
                    return True
                return False
            return self.state == self.CLOSED

    def get_state(self) -> dict:
        """Observability - current state"""
        return {
            "state": self.state,
            "failures": self.failures,
            "last_failure": self.last_failure_time,
            "half_open_calls": self.half_open_calls
        }