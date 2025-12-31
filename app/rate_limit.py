import time
from collections import deque
from typing import Deque

WINDOW_SECONDS = 60
MAX_REQUESTS = 5

# In-memory per-tenant sliding window rate limiter.
# Designed for this exercise; production systems should use a shared store
# (e.g. Redis) or an API gateway for distributed enforcement.
_requests: dict[str, Deque[float]] = {}


def check_rate_limit(tenant_id: str) -> None:
    now = time.time()
    q = _requests.setdefault(tenant_id, deque())

    # Evict timestamps outside the current window
    while q and (now - q[0]) > WINDOW_SECONDS:
        q.popleft()

    # Enforce per-tenant quota
    if len(q) >= MAX_REQUESTS:
        raise RuntimeError("Rate limit exceeded")

    q.append(now)
