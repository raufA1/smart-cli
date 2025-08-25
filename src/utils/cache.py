"""Hybrid caching system for Smart CLI."""

import sqlite3
import pickle
import asyncio
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import json
import structlog

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from .config import ConfigManager


class MemoryCache:
    """In-memory LRU cache with TTL support."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_order: List[str] = []
        self.logger = structlog.get_logger()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache."""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # Check TTL
        if entry['expires_at'] < datetime.now():
            self.delete(key)
            return None
        
        # Update access order (LRU)
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
        
        entry['last_accessed'] = datetime.now()
        entry['access_count'] += 1
        
        return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in memory cache."""
        ttl = ttl or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        # Remove existing entry if present
        if key in self.cache:
            self.access_order.remove(key)
        
        # Add new entry
        self.cache[key] = {
            'value': value,
            'created_at': datetime.now(),
            'last_accessed': datetime.now(),
            'expires_at': expires_at,
            'access_count': 1,
        }
        
        self.access_order.append(key)
        
        # Evict if necessary
        self._evict_if_necessary()
    
    def delete(self, key: str) -> bool:
        """Delete key from memory cache."""
        if key in self.cache:
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)
            return True
        return False
    
    def clear(self) -> None:
        """Clear all entries from memory cache."""
        self.cache.clear()
        self.access_order.clear()
    
    def _evict_if_necessary(self) -> None:
        """Evict least recently used items if cache is full."""
        while len(self.cache) > self.max_size:
            if not self.access_order:
                break
            
            lru_key = self.access_order.pop(0)
            if lru_key in self.cache:
                del self.cache[lru_key]
                self.logger.debug("Evicted LRU entry", key=lru_key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self.cache)
        expired_entries = 0
        
        for entry in self.cache.values():
            if entry['expires_at'] < datetime.now():
                expired_entries += 1
        
        return {
            'total_entries': total_entries,
            'expired_entries': expired_entries,
            'memory_usage_estimate': len(str(self.cache)),  # Rough estimate
            'max_size': self.max_size,
            'usage_percentage': (total_entries / self.max_size) * 100,
        }


class SQLiteCache:
    """SQLite-based persistent cache."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.logger = structlog.get_logger()
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize SQLite database."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(self.db_path))
        conn.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value BLOB,
                created_at TIMESTAMP,
                last_accessed TIMESTAMP,
                expires_at TIMESTAMP,
                access_count INTEGER DEFAULT 1,
                size_bytes INTEGER
            )
        ''')
        
        # Create indexes for performance
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON cache(expires_at)
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_cache_last_accessed ON cache(last_accessed)
        ''')
        
        conn.commit()
        conn.close()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from SQLite cache."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Check if key exists and not expired
        cursor.execute('''
            SELECT value, expires_at FROM cache 
            WHERE key = ? AND expires_at > ?
        ''', (key, datetime.now()))
        
        result = cursor.fetchone()
        
        if result:
            # Update access information
            cursor.execute('''
                UPDATE cache SET 
                last_accessed = ?, 
                access_count = access_count + 1 
                WHERE key = ?
            ''', (datetime.now(), key))
            
            conn.commit()
            conn.close()
            
            try:
                return pickle.loads(result[0])
            except Exception as e:
                self.logger.warning("Failed to unpickle cached value", key=key, error=str(e))
                self.delete(key)
                return None
        
        conn.close()
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set value in SQLite cache."""
        try:
            serialized_value = pickle.dumps(value)
            size_bytes = len(serialized_value)
            expires_at = datetime.now() + timedelta(seconds=ttl)
            
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO cache 
                (key, value, created_at, last_accessed, expires_at, access_count, size_bytes) 
                VALUES (?, ?, ?, ?, ?, 1, ?)
            ''', (
                key, serialized_value, datetime.now(), 
                datetime.now(), expires_at, size_bytes
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error("Failed to cache value", key=key, error=str(e))
    
    def delete(self, key: str) -> bool:
        """Delete key from SQLite cache."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM cache WHERE key = ?', (key,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def clear_expired(self) -> int:
        """Clear expired entries and return count."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM cache WHERE expires_at < ?', (datetime.now(),))
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            self.logger.info("Cleared expired cache entries", count=deleted_count)
        
        return deleted_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Get basic stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_entries,
                SUM(size_bytes) as total_size,
                AVG(access_count) as avg_access_count,
                MAX(last_accessed) as last_access_time
            FROM cache
        ''')
        
        stats = cursor.fetchone()
        
        # Get expired count
        cursor.execute('SELECT COUNT(*) FROM cache WHERE expires_at < ?', (datetime.now(),))
        expired_count = cursor.fetchone()[0]
        
        # Get most accessed entries
        cursor.execute('''
            SELECT key, access_count FROM cache 
            ORDER BY access_count DESC 
            LIMIT 5
        ''')
        top_entries = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_entries': stats[0] or 0,
            'total_size_bytes': stats[1] or 0,
            'average_access_count': stats[2] or 0,
            'last_access_time': stats[3],
            'expired_entries': expired_count,
            'top_accessed_keys': [{'key': k, 'access_count': c} for k, c in top_entries],
        }


class HybridCache:
    """Hybrid cache combining memory, Redis, and SQLite layers."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config = config_manager or ConfigManager()
        self.logger = structlog.get_logger()
        
        # Initialize cache layers
        self.memory_cache = MemoryCache(
            max_size=self.config.get_config('memory_cache_size', 1000),
            default_ttl=self.config.get_config('cache_ttl', 3600)
        )
        
        # SQLite cache
        cache_dir = Path.home() / ".smart-cli"
        self.sqlite_cache = SQLiteCache(cache_dir / "cache.db")
        
        # Redis cache (optional)
        self.redis_client = None
        if REDIS_AVAILABLE and self.config.get_config('redis_url'):
            try:
                redis_url = self.config.get_config('redis_url')
                self.redis_client = redis.from_url(redis_url)
                # Test connection
                self.redis_client.ping()
                self.logger.info("Redis cache initialized")
            except Exception as e:
                self.logger.warning("Redis cache unavailable", error=str(e))
                self.redis_client = None
    
    def _generate_cache_key(self, key: str, namespace: str = "default") -> str:
        """Generate cache key with namespace and hashing."""
        full_key = f"{namespace}:{key}"
        
        # If key is too long, hash it
        if len(full_key) > 250:
            return f"{namespace}:{hashlib.sha256(full_key.encode()).hexdigest()}"
        
        return full_key
    
    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """Get value from cache with fallback layers."""
        cache_key = self._generate_cache_key(key, namespace)
        
        # Try memory cache first (fastest)
        value = self.memory_cache.get(cache_key)
        if value is not None:
            self.logger.debug("Cache hit (memory)", key=cache_key)
            return value
        
        # Try Redis cache (fast, shared)
        if self.redis_client:
            try:
                redis_value = self.redis_client.get(cache_key)
                if redis_value:
                    deserialized = pickle.loads(redis_value)
                    
                    # Store in memory cache for next access
                    self.memory_cache.set(cache_key, deserialized)
                    self.logger.debug("Cache hit (redis)", key=cache_key)
                    return deserialized
                    
            except Exception as e:
                self.logger.warning("Redis cache get failed", key=cache_key, error=str(e))
        
        # Try SQLite cache (persistent)
        value = self.sqlite_cache.get(cache_key)
        if value is not None:
            # Store in upper cache layers
            self.memory_cache.set(cache_key, value)
            
            if self.redis_client:
                try:
                    ttl = self.config.get_config('cache_ttl', 3600)
                    self.redis_client.setex(cache_key, ttl, pickle.dumps(value))
                except Exception as e:
                    self.logger.warning("Redis cache set failed", key=cache_key, error=str(e))
            
            self.logger.debug("Cache hit (sqlite)", key=cache_key)
            return value
        
        self.logger.debug("Cache miss", key=cache_key)
        return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: int = None, 
        namespace: str = "default"
    ) -> None:
        """Set value in all cache layers."""
        cache_key = self._generate_cache_key(key, namespace)
        ttl = ttl or self.config.get_config('cache_ttl', 3600)
        
        # Store in memory cache
        self.memory_cache.set(cache_key, value, ttl)
        
        # Store in Redis cache
        if self.redis_client:
            try:
                self.redis_client.setex(cache_key, ttl, pickle.dumps(value))
            except Exception as e:
                self.logger.warning("Redis cache set failed", key=cache_key, error=str(e))
        
        # Store in SQLite cache
        self.sqlite_cache.set(cache_key, value, ttl)
        
        self.logger.debug("Value cached", key=cache_key, ttl=ttl)
    
    async def delete(self, key: str, namespace: str = "default") -> bool:
        """Delete key from all cache layers."""
        cache_key = self._generate_cache_key(key, namespace)
        
        results = []
        
        # Delete from memory cache
        results.append(self.memory_cache.delete(cache_key))
        
        # Delete from Redis cache
        if self.redis_client:
            try:
                results.append(bool(self.redis_client.delete(cache_key)))
            except Exception as e:
                self.logger.warning("Redis cache delete failed", key=cache_key, error=str(e))
                results.append(False)
        
        # Delete from SQLite cache
        results.append(self.sqlite_cache.delete(cache_key))
        
        success = any(results)
        self.logger.debug("Cache key deleted", key=cache_key, success=success)
        
        return success
    
    async def clear(self, namespace: str = None) -> None:
        """Clear cache entries (optionally by namespace)."""
        if namespace:
            # This would require a more complex implementation
            # For now, we'll just log a warning
            self.logger.warning("Namespace-specific clearing not implemented")
            return
        
        # Clear memory cache
        self.memory_cache.clear()
        
        # Clear Redis cache (if available)
        if self.redis_client:
            try:
                self.redis_client.flushdb()
            except Exception as e:
                self.logger.warning("Redis cache clear failed", error=str(e))
        
        # Clear SQLite cache would require dropping all entries
        # For now, just clear expired entries
        self.sqlite_cache.clear_expired()
        
        self.logger.info("Cache cleared")
    
    async def cleanup_expired(self) -> Dict[str, int]:
        """Clean up expired entries from all cache layers."""
        results = {}
        
        # SQLite cleanup (memory cache auto-expires on access)
        results['sqlite'] = self.sqlite_cache.clear_expired()
        
        # Redis automatically expires keys with TTL
        results['redis'] = 0
        
        total_cleaned = sum(results.values())
        if total_cleaned > 0:
            self.logger.info("Cleaned up expired cache entries", results=results)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        stats = {
            'memory': self.memory_cache.get_stats(),
            'sqlite': self.sqlite_cache.get_stats(),
            'redis': {'available': self.redis_client is not None},
        }
        
        if self.redis_client:
            try:
                redis_info = self.redis_client.info('memory')
                stats['redis'].update({
                    'used_memory': redis_info.get('used_memory', 0),
                    'used_memory_human': redis_info.get('used_memory_human', '0B'),
                    'keyspace_hits': self.redis_client.info('stats').get('keyspace_hits', 0),
                    'keyspace_misses': self.redis_client.info('stats').get('keyspace_misses', 0),
                })
            except Exception as e:
                self.logger.warning("Failed to get Redis stats", error=str(e))
                stats['redis']['error'] = str(e)
        
        return stats


# Factory function for easy cache creation
def create_cache(config_manager: Optional[ConfigManager] = None) -> HybridCache:
    """Create and return a configured HybridCache instance."""
    return HybridCache(config_manager)