"""Intelligent AI Response Cache System for Smart CLI."""

import asyncio
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional


class AIResponseCache:
    """High-performance AI response caching with intelligent invalidation."""

    def __init__(
        self, cache_dir: str = None, max_age_hours: int = 24, max_size_mb: int = 100
    ):
        self.cache_dir = Path(cache_dir or "cache/ai_responses")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.max_age_seconds = max_age_hours * 3600
        self.max_size_bytes = max_size_mb * 1024 * 1024

        # Cache statistics
        self.stats = {"hits": 0, "misses": 0, "invalidations": 0, "size_cleanups": 0}

        # Background cleanup task - will be started when needed
        self._cleanup_task = None

    def _generate_cache_key(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Generate unique cache key for prompt + context."""
        # Include context in hash for better cache precision
        cache_data = {"prompt": prompt, "context": context or {}}

        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_string.encode()).hexdigest()

    def _get_cache_file_path(self, cache_key: str) -> Path:
        """Get cache file path for given key."""
        return self.cache_dir / f"{cache_key}.json"

    async def get(self, prompt: str, context: Dict[str, Any] = None) -> Optional[str]:
        """Get cached AI response if available and valid."""
        try:
            cache_key = self._generate_cache_key(prompt, context)
            cache_file = self._get_cache_file_path(cache_key)

            if not cache_file.exists():
                self.stats["misses"] += 1
                return None

            # Read cache entry
            with open(cache_file, "r", encoding="utf-8") as f:
                cache_entry = json.load(f)

            # Check expiration
            if time.time() - cache_entry["timestamp"] > self.max_age_seconds:
                cache_file.unlink()  # Delete expired entry
                self.stats["invalidations"] += 1
                self.stats["misses"] += 1
                return None

            # Update access time for LRU
            cache_entry["last_accessed"] = time.time()
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_entry, f)

            self.stats["hits"] += 1
            return cache_entry["response"]

        except Exception:
            self.stats["misses"] += 1
            return None

    async def set(
        self,
        prompt: str,
        response: str,
        context: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
    ):
        """Cache AI response with metadata."""
        try:
            cache_key = self._generate_cache_key(prompt, context)
            cache_file = self._get_cache_file_path(cache_key)

            cache_entry = {
                "prompt": prompt,
                "response": response,
                "context": context or {},
                "metadata": metadata or {},
                "timestamp": time.time(),
                "last_accessed": time.time(),
                "cache_key": cache_key,
            }

            # Write to cache
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_entry, f, ensure_ascii=False, indent=2)

            # Check if cleanup needed
            await self._check_size_limit()

        except Exception as e:
            # Cache errors shouldn't break the main flow
            pass

    async def _check_size_limit(self):
        """Check and enforce cache size limits."""
        try:
            total_size = sum(f.stat().st_size for f in self.cache_dir.rglob("*.json"))

            if total_size > self.max_size_bytes:
                # Get all cache files with access times
                cache_files = []
                for cache_file in self.cache_dir.glob("*.json"):
                    try:
                        with open(cache_file, "r") as f:
                            cache_entry = json.load(f)
                        cache_files.append(
                            (
                                cache_file,
                                cache_entry.get("last_accessed", 0),
                                cache_file.stat().st_size,
                            )
                        )
                    except:
                        continue

                # Sort by last accessed (LRU)
                cache_files.sort(key=lambda x: x[1])

                # Remove oldest files until under limit
                removed_size = 0
                for cache_file, _, size in cache_files:
                    if (
                        total_size - removed_size <= self.max_size_bytes * 0.8
                    ):  # 80% threshold
                        break

                    cache_file.unlink()
                    removed_size += size
                    self.stats["size_cleanups"] += 1

        except Exception:
            pass

    def _start_background_cleanup(self):
        """Start background cleanup task if event loop is running."""
        if self._cleanup_task is None:
            try:
                loop = asyncio.get_running_loop()
                if loop and not loop.is_closed():
                    self._cleanup_task = asyncio.create_task(self._background_cleanup())
            except RuntimeError:
                # No event loop running, skip background task
                pass

    async def _background_cleanup(self):
        """Background task for periodic cache maintenance."""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour
                await self._cleanup_expired()
                await self._check_size_limit()
            except asyncio.CancelledError:
                break
            except Exception:
                continue

    async def _cleanup_expired(self):
        """Remove expired cache entries."""
        try:
            current_time = time.time()
            expired_count = 0

            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, "r") as f:
                        cache_entry = json.load(f)

                    if current_time - cache_entry["timestamp"] > self.max_age_seconds:
                        cache_file.unlink()
                        expired_count += 1

                except Exception:
                    continue

            self.stats["invalidations"] += expired_count

        except Exception:
            pass

    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (
            (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        )

        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            total_size = sum(f.stat().st_size for f in cache_files)
            total_size_mb = total_size / (1024 * 1024)
        except:
            cache_files = []
            total_size_mb = 0

        return {
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests,
            "cache_entries": len(cache_files),
            "cache_size_mb": round(total_size_mb, 2),
            **self.stats,
        }

    async def clear_cache(self, pattern: str = None):
        """Clear cache entries, optionally matching a pattern."""
        try:
            if pattern:
                # Clear specific pattern
                for cache_file in self.cache_dir.glob(f"*{pattern}*.json"):
                    cache_file.unlink()
            else:
                # Clear all cache
                for cache_file in self.cache_dir.glob("*.json"):
                    cache_file.unlink()

        except Exception:
            pass

    def close(self):
        """Close cache and cleanup background tasks."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None


# Global cache instance
_global_cache = None


def get_ai_cache() -> AIResponseCache:
    """Get global AI cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = AIResponseCache()
    return _global_cache
