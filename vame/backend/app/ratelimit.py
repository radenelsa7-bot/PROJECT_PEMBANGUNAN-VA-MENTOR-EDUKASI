"""Rate limiting sederhana in-memory (NFR-11). Untuk produksi multi-proses gunakan Redis."""
import time
from collections import defaultdict, deque

from fastapi import HTTPException


class RateLimiter:
    def __init__(self, limit: int, window: int = 60):
        self.limit, self.window = limit, window
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        q = self.hits[key]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.limit:
            raise HTTPException(
                status_code=429,
                detail={"code": "RATE_LIMITED", "message": "Terlalu banyak permintaan. Coba lagi sebentar lagi."},
            )
        q.append(now)

    def reset(self) -> None:
        self.hits.clear()


ai_limiter = RateLimiter(limit=20)
login_limiter = RateLimiter(limit=15)
