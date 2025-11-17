import time
import constants

class TokenBucket:
    def __init__(self, capacity: int = constants.DEFAULT_BURST, refill_rate: float = constants.DEFAULT_REFILL_RATE):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.timestamp = time.monotonic()

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.timestamp
        self.timestamp = now
        self.tokens = min(self.capacity, int(self.tokens + elapsed * self.refill_rate))

    def consume(self, tokens: float = 1.0):
        while True:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return
            need = tokens - self.tokens
            sleep_for = max(need / self.refill_rate, 0.05)
            time.sleep(sleep_for)
