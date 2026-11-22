"""
Thread-safe TTL Cache for Cutshort MCP Server.
Reduces redundant API roundtrips and handles transient response caching.
"""
import time
from threading import Lock
from typing import Any, Dict, Optional, Tuple


class TTLCache:
    """Thread-safe in-memory cache with time-to-live expiration."""

    def __init__(self, default_ttl: int = 180, default_ttl_seconds: Optional[int] = None, max_size: int = 500):
        self.default_ttl = default_ttl_seconds if default_ttl_seconds is not None else default_ttl
        self.max_size = max_size
        self._store: Dict[str, Tuple[Any, float]] = {}
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value if key exists and has not expired."""
        with self._lock:
            if key not in self._store:
                return None
            value, expiry = self._store[key]
            if time.time() > expiry:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None, ttl_seconds: Optional[int] = None) -> None:
        """Store value with specified TTL (in seconds) or default TTL."""
        effective_ttl = ttl if ttl is not None else (ttl_seconds if ttl_seconds is not None else self.default_ttl)
        expiry = time.time() + effective_ttl
        with self._lock:
            if len(self._store) >= self.max_size:
                now = time.time()
                expired = [k for k, (_, exp) in self._store.items() if now > exp]
                for k in expired:
                    del self._store[k]
                if len(self._store) >= self.max_size:
                    oldest = min(self._store.keys(), key=lambda k: self._store[k][1])
                    del self._store[oldest]
            self._store[key] = (value, expiry)

    def invalidate(self, prefix: str = "") -> None:
        """Invalidate keys matching prefix, or all keys if prefix is empty."""
        with self._lock:
            if not prefix:
                self._store.clear()
            else:
                keys_to_del = [k for k in self._store if k.startswith(prefix)]
                for k in keys_to_del:
                    del self._store[k]

    def clear(self) -> None:
        """Purge all entries."""
        self.invalidate("")
