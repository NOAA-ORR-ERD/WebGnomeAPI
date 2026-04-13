"""
Releases a Redis distributed lock if the stored value matches LOCK_VALUE.
Intended to be called from an EXIT trap in a shell script.
"""
import os
import sys

import redis

cache_uri = os.environ.get("CACHE_URI")
if not cache_uri:
    print("ERROR: CACHE_URI environment variable is not set", file=sys.stderr)
    sys.exit(1)

client = redis.from_url(cache_uri)
lock_key = os.environ["LOCK_KEY"]
lock_value = os.environ["LOCK_VALUE"]

stored = client.get(lock_key)
if stored and stored.decode() == lock_value:
    client.delete(lock_key)
    print(f"Lock released: {lock_key}")
else:
    print(f"Lock '{lock_key}' was not ours or already expired; skipping release.")
