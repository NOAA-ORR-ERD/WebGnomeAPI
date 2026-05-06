"""
Acquires a Redis distributed lock and writes the lock value to a temp file
so the caller can release it on exit.

Exit codes:
  0 - lock acquired, lock value written to /tmp/.redis_lock_<PPID>
  1 - error (missing env var, Redis connection failure, etc.)
  2 - lock already held by another process
"""
import os
import sys
import uuid

import redis

cache_uri = os.environ.get("CACHE_URI")
if not cache_uri:
    print("ERROR: CACHE_URI environment variable is not set", file=sys.stderr)
    sys.exit(1)

client = redis.from_url(cache_uri)
lock_key = os.environ["LOCK_KEY"]
lock_ttl = int(os.environ["LOCK_TTL"])
lock_value = str(uuid.uuid4())

acquired = client.set(lock_key, lock_value, nx=True, ex=lock_ttl)
if not acquired:
    print(f"Lock '{lock_key}' is already held. Another instance is running. Exiting.")
    sys.exit(2)

lock_file = f"/tmp/.redis_lock_{os.getppid()}"
with open(lock_file, "w") as f:
    f.write(lock_value)

print(f"Lock acquired: {lock_key}")
