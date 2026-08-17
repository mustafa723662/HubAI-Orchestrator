from slowapi import Limiter
from slowapi.util import get_remote_address

# Single shared Limiter instance (per-IP token buckets, in-memory).
# In-memory means limits reset on restart and aren't shared across multiple
# worker processes — fine for a single Render free-tier instance; move to a
# Redis storage backend (slowapi supports it) if you ever scale to >1 worker.
limiter = Limiter(key_func=get_remote_address)
