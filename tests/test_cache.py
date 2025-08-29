"""Tests for hybrid caching system."""

import pytest
import tempfile
import shutil
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.utils.cache import MemoryCache, SQLiteCache, HybridCache, create_cache
from src.utils.config import ConfigManager


class TestMemoryCache:
    """Test MemoryCache functionality."""
    
    @pytest.fixture
    def memory_cache(self):
        """Create MemoryCache instance."""
        return MemoryCache(max_size=5, default_ttl=3600)
    
    def test_cache_initialization(self, memory_cache):
        """Test cache initialization."""
        assert memory_cache.max_size == 5
        assert memory_cache.default_ttl == 3600
        assert len(memory_cache.cache) == 0
        assert len(memory_cache.access_order) == 0
    
    def test_set_and_get_value(self, memory_cache):
        """Test setting and getting cache values."""
        memory_cache.set("key1", "value1")
        
        result = memory_cache.get("key1")
        assert result == "value1"
    
    def test_get_nonexistent_key(self, memory_cache):
        """Test getting non-existent key returns None."""
        result = memory_cache.get("nonexistent")
        assert result is None
    
    def test_ttl_expiration(self, memory_cache):
        """Test TTL expiration."""
        # Set with very short TTL
        memory_cache.set("expire_key", "expire_value", ttl=1)
        
        # Should be available immediately
        assert memory_cache.get("expire_key") == "expire_value"
        
        # Mock datetime to simulate expiration
        future_time = datetime.now() + timedelta(seconds=2)
        with patch('src.utils.cache.datetime') as mock_datetime:
            mock_datetime.now.return_value = future_time
            result = memory_cache.get("expire_key")
            assert result is None
    
    def test_lru_eviction(self, memory_cache):
        """Test LRU eviction when cache is full."""
        # Fill cache to capacity
        for i in range(5):
            memory_cache.set(f"key{i}", f"value{i}")
        
        # Add one more item - should evict least recently used
        memory_cache.set("key5", "value5")
        
        # key0 should be evicted (least recently used)
        assert memory_cache.get("key0") is None
        assert memory_cache.get("key5") == "value5"
        assert len(memory_cache.cache) == 5
    
    def test_access_updates_lru_order(self, memory_cache):
        """Test that accessing items updates LRU order."""
        # Add items
        memory_cache.set("key1", "value1")
        memory_cache.set("key2", "value2")
        memory_cache.set("key3", "value3")
        
        # Access key1 to make it most recently used
        memory_cache.get("key1")
        
        # Fill cache and add more
        memory_cache.set("key4", "value4")
        memory_cache.set("key5", "value5")
        memory_cache.set("key6", "value6")  # Should evict key2
        
        assert memory_cache.get("key1") == "value1"  # Should still exist
        assert memory_cache.get("key2") is None      # Should be evicted
    
    def test_delete_key(self, memory_cache):
        """Test deleting cache keys."""
        memory_cache.set("delete_me", "value")
        assert memory_cache.get("delete_me") == "value"
        
        success = memory_cache.delete("delete_me")
        assert success is True
        assert memory_cache.get("delete_me") is None
        
        # Delete non-existent key
        success = memory_cache.delete("non_existent")
        assert success is False
    
    def test_clear_cache(self, memory_cache):
        """Test clearing all cache entries."""
        memory_cache.set("key1", "value1")
        memory_cache.set("key2", "value2")
        
        memory_cache.clear()
        
        assert len(memory_cache.cache) == 0
        assert len(memory_cache.access_order) == 0
        assert memory_cache.get("key1") is None
        assert memory_cache.get("key2") is None
    
    def test_get_stats(self, memory_cache):
        """Test getting cache statistics."""
        memory_cache.set("key1", "value1")
        memory_cache.set("key2", "value2")
        
        stats = memory_cache.get_stats()
        
        assert stats['total_entries'] == 2
        assert stats['max_size'] == 5
        assert stats['usage_percentage'] == 40.0
        assert 'memory_usage_estimate' in stats
        assert 'expired_entries' in stats


class TestSQLiteCache:
    """Test SQLiteCache functionality."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        temp_dir = Path(tempfile.mkdtemp())
        db_path = temp_dir / "test_cache.db"
        yield db_path
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sqlite_cache(self, temp_db_path):
        """Create SQLiteCache instance."""
        return SQLiteCache(temp_db_path)
    
    def test_cache_initialization(self, sqlite_cache, temp_db_path):
        """Test SQLite cache initialization."""
        assert temp_db_path.exists()
        
        # Check that tables were created
        import sqlite3
        conn = sqlite3.connect(str(temp_db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        assert 'cache' in tables
    
    def test_set_and_get_value(self, sqlite_cache):
        """Test setting and getting values."""
        sqlite_cache.set("test_key", {"data": "test_value"})
        
        result = sqlite_cache.get("test_key")
        assert result == {"data": "test_value"}
    
    def test_get_nonexistent_key(self, sqlite_cache):
        """Test getting non-existent key."""
        result = sqlite_cache.get("nonexistent")
        assert result is None
    
    def test_ttl_expiration(self, sqlite_cache):
        """Test TTL expiration in SQLite cache."""
        sqlite_cache.set("expire_key", "expire_value", ttl=1)
        
        # Should be available immediately
        assert sqlite_cache.get("expire_key") == "expire_value"
        
        # Mock datetime for expiration test
        future_time = datetime.now() + timedelta(seconds=2)
        with patch('src.utils.cache.datetime') as mock_datetime:
            mock_datetime.now.return_value = future_time
            result = sqlite_cache.get("expire_key")
            assert result is None
    
    def test_delete_key(self, sqlite_cache):
        """Test deleting keys from SQLite cache."""
        sqlite_cache.set("delete_me", "value")
        assert sqlite_cache.get("delete_me") == "value"
        
        success = sqlite_cache.delete("delete_me")
        assert success is True
        assert sqlite_cache.get("delete_me") is None
        
        # Delete non-existent key
        success = sqlite_cache.delete("non_existent")
        assert success is False
    
    def test_access_count_tracking(self, sqlite_cache):
        """Test that access counts are tracked."""
        sqlite_cache.set("access_test", "value")
        
        # Access multiple times
        sqlite_cache.get("access_test")
        sqlite_cache.get("access_test")
        sqlite_cache.get("access_test")
        
        stats = sqlite_cache.get_stats()
        assert stats['total_entries'] == 1
    
    def test_clear_expired_entries(self, sqlite_cache):
        """Test clearing expired entries."""
        # Add expired and non-expired entries
        sqlite_cache.set("expired", "value", ttl=1)
        sqlite_cache.set("valid", "value", ttl=3600)
        
        # Mock time to make first entry expired
        future_time = datetime.now() + timedelta(seconds=2)
        with patch('src.utils.cache.datetime') as mock_datetime:
            mock_datetime.now.return_value = future_time
            
            cleared_count = sqlite_cache.clear_expired()
            assert cleared_count >= 1  # At least expired entry cleared
            assert sqlite_cache.get("expired") is None
            assert sqlite_cache.get("valid") == "value"
    
    def test_get_stats(self, sqlite_cache):
        """Test getting SQLite cache statistics."""
        sqlite_cache.set("key1", "value1")
        sqlite_cache.set("key2", {"nested": "data"})
        
        stats = sqlite_cache.get_stats()
        
        assert stats['total_entries'] == 2
        assert 'total_size_bytes' in stats
        assert 'average_access_count' in stats
        assert 'expired_entries' in stats
        assert 'top_accessed_keys' in stats
    
    def test_serialization_error_handling(self, sqlite_cache):
        """Test handling of serialization errors."""
        # Try to store non-serializable object
        class NonSerializable:
            def __reduce__(self):
                raise TypeError("Cannot pickle")
        
        sqlite_cache.set("bad_key", NonSerializable())
        
        # Should handle gracefully and not crash
        result = sqlite_cache.get("bad_key")
        assert result is None  # Should not be stored due to serialization error


class TestHybridCache:
    """Test HybridCache functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration manager."""
        config = Mock(spec=ConfigManager)
        config.get_config.side_effect = lambda key, default=None: {
            'memory_cache_size': 100,
            'cache_ttl': 3600,
            'redis_url': None  # No Redis for basic tests
        }.get(key, default)
        return config
    
    @pytest.fixture
    def hybrid_cache(self, mock_config):
        """Create HybridCache instance."""
        return HybridCache(mock_config)
    
    def test_cache_initialization(self, hybrid_cache):
        """Test hybrid cache initialization."""
        assert hybrid_cache.memory_cache is not None
        assert hybrid_cache.sqlite_cache is not None
        assert hybrid_cache.redis_client is None  # Not configured
    
    @pytest.mark.asyncio
    async def test_cache_key_generation(self, hybrid_cache):
        """Test cache key generation."""
        key1 = hybrid_cache._generate_cache_key("simple_key")
        assert key1 == "default:simple_key"
        
        key2 = hybrid_cache._generate_cache_key("simple_key", "custom_ns")
        assert key2 == "custom_ns:simple_key"
        
        # Test long key hashing
        long_key = "x" * 300
        hashed_key = hybrid_cache._generate_cache_key(long_key)
        assert len(hashed_key) < 300
        assert "default:" in hashed_key
    
    @pytest.mark.asyncio
    async def test_set_and_get_memory_cache(self, hybrid_cache):
        """Test setting and getting from memory cache layer."""
        await hybrid_cache.set("test_key", "test_value")
        result = await hybrid_cache.get("test_key")
        
        assert result == "test_value"
    
    @pytest.mark.asyncio
    async def test_cache_fallback_to_sqlite(self, hybrid_cache):
        """Test fallback to SQLite when not in memory."""
        # Set value (goes to all layers)
        await hybrid_cache.set("fallback_key", "fallback_value")
        
        # Clear memory cache to test SQLite fallback
        hybrid_cache.memory_cache.clear()
        
        # Should still get value from SQLite
        result = await hybrid_cache.get("fallback_key")
        assert result == "fallback_value"
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, hybrid_cache):
        """Test cache miss across all layers."""
        result = await hybrid_cache.get("nonexistent_key")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_from_all_layers(self, hybrid_cache):
        """Test deleting from all cache layers."""
        await hybrid_cache.set("delete_test", "value")
        
        # Verify it exists
        assert await hybrid_cache.get("delete_test") == "value"
        
        # Delete
        success = await hybrid_cache.delete("delete_test")
        assert success is True
        
        # Verify it's gone
        assert await hybrid_cache.get("delete_test") is None
    
    @pytest.mark.asyncio
    async def test_namespace_support(self, hybrid_cache):
        """Test namespace isolation."""
        await hybrid_cache.set("key", "value1", namespace="ns1")
        await hybrid_cache.set("key", "value2", namespace="ns2")
        
        result1 = await hybrid_cache.get("key", namespace="ns1")
        result2 = await hybrid_cache.get("key", namespace="ns2")
        
        assert result1 == "value1"
        assert result2 == "value2"
    
    @pytest.mark.asyncio
    async def test_ttl_parameter(self, hybrid_cache):
        """Test TTL parameter handling."""
        await hybrid_cache.set("ttl_test", "value", ttl=1800)  # 30 minutes
        
        # Verify it's stored (we can't easily test expiration in unit test)
        result = await hybrid_cache.get("ttl_test")
        assert result == "value"
    
    @pytest.mark.asyncio
    async def test_cleanup_expired(self, hybrid_cache):
        """Test cleaning up expired entries."""
        results = await hybrid_cache.cleanup_expired_contexts()
        
        # Should return dictionary with cleanup results
        assert isinstance(results, dict)
        assert 'sqlite' in results
        assert 'redis' in results
    
    def test_get_stats(self, hybrid_cache):
        """Test getting comprehensive cache statistics."""
        stats = hybrid_cache.get_stats()
        
        assert 'memory' in stats
        assert 'sqlite' in stats
        assert 'redis' in stats
        
        # Memory cache stats
        assert 'total_entries' in stats['memory']
        
        # SQLite cache stats
        assert 'total_entries' in stats['sqlite']
        
        # Redis stats (should indicate unavailable)
        assert stats['redis']['available'] is False


class TestHybridCacheWithRedis:
    """Test HybridCache with Redis support."""
    
    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client."""
        redis_mock = MagicMock()
        redis_mock.ping.return_value = True
        redis_mock.get.return_value = None
        redis_mock.setex.return_value = True
        redis_mock.delete.return_value = 1
        redis_mock.flushdb.return_value = True
        redis_mock.info.return_value = {
            'used_memory': 1024,
            'used_memory_human': '1KB'
        }
        return redis_mock
    
    @pytest.fixture
    def mock_config_with_redis(self):
        """Mock configuration with Redis enabled."""
        config = Mock(spec=ConfigManager)
        config.get_config.side_effect = lambda key, default=None: {
            'memory_cache_size': 100,
            'cache_ttl': 3600,
            'redis_url': 'redis://localhost:6379'
        }.get(key, default)
        return config
    
    @pytest.mark.skipif(not hasattr(pytest, "importorskip"), 
                       reason="Redis tests require redis package")
    def test_redis_initialization(self, mock_config_with_redis, mock_redis_client):
        """Test Redis initialization."""
        with patch('src.utils.cache.redis') as mock_redis_module:
            mock_redis_module.from_url.return_value = mock_redis_client
            
            hybrid_cache = HybridCache(mock_config_with_redis)
            
            assert hybrid_cache.redis_client is not None
            mock_redis_client.ping.assert_called_once()
    
    @pytest.mark.skipif(not hasattr(pytest, "importorskip"),
                       reason="Redis tests require redis package")
    @pytest.mark.asyncio
    async def test_redis_cache_layer(self, mock_config_with_redis, mock_redis_client):
        """Test Redis cache layer functionality."""
        import pickle
        
        with patch('src.utils.cache.redis') as mock_redis_module:
            mock_redis_module.from_url.return_value = mock_redis_client
            
            hybrid_cache = HybridCache(mock_config_with_redis)
            
            # Mock Redis get to return pickled data
            test_data = "redis_cached_value"
            mock_redis_client.get.return_value = pickle.dumps(test_data)
            
            # Clear memory cache to force Redis lookup
            hybrid_cache.memory_cache.clear()
            
            result = await hybrid_cache.get("redis_test")
            
            # Should call Redis and return unpickled data
            mock_redis_client.get.assert_called()
            assert result == test_data


class TestCacheFactory:
    """Test cache factory function."""
    
    def test_create_cache_default(self):
        """Test creating cache with default config."""
        cache = create_cache()
        
        assert isinstance(cache, HybridCache)
        assert cache.config is not None
    
    def test_create_cache_with_config(self):
        """Test creating cache with custom config."""
        mock_config = Mock(spec=ConfigManager)
        cache = create_cache(mock_config)
        
        assert isinstance(cache, HybridCache)
        assert cache.config == mock_config


@pytest.mark.integration
class TestCacheIntegration:
    """Integration tests for cache system."""
    
    @pytest.mark.asyncio
    async def test_full_cache_workflow(self):
        """Test complete cache workflow with all layers."""
        cache = create_cache()
        
        # Test data
        test_data = {
            "complex": "data",
            "with": ["nested", "structures"],
            "and": {"numbers": 42}
        }
        
        # Set data
        await cache.set("integration_test", test_data)
        
        # Get data (should come from memory)
        result1 = await cache.get("integration_test")
        assert result1 == test_data
        
        # Clear memory, should fallback to SQLite
        cache.memory_cache.clear()
        result2 = await cache.get("integration_test")
        assert result2 == test_data
        
        # Delete data
        await cache.delete("integration_test")
        result3 = await cache.get("integration_test")
        assert result3 is None
    
    @pytest.mark.asyncio
    async def test_concurrent_cache_access(self):
        """Test concurrent access to cache."""
        cache = create_cache()
        
        async def cache_worker(worker_id):
            for i in range(10):
                key = f"worker_{worker_id}_item_{i}"
                await cache.set(key, f"data_{worker_id}_{i}")
                result = await cache.get(key)
                assert result == f"data_{worker_id}_{i}"
        
        # Run multiple workers concurrently
        tasks = [cache_worker(i) for i in range(5)]
        await asyncio.gather(*tasks)
        
        # Verify all data is accessible
        for worker_id in range(5):
            for i in range(10):
                key = f"worker_{worker_id}_item_{i}"
                result = await cache.get(key)
                assert result == f"data_{worker_id}_{i}"
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_cache_performance(self):
        """Test cache performance characteristics."""
        cache = create_cache()
        
        # Measure set performance
        import time
        start_time = time.time()
        
        for i in range(1000):
            await cache.set(f"perf_test_{i}", f"value_{i}")
        
        set_time = time.time() - start_time
        
        # Measure get performance
        start_time = time.time()
        
        for i in range(1000):
            result = await cache.get(f"perf_test_{i}")
            assert result == f"value_{i}"
        
        get_time = time.time() - start_time
        
        # Performance assertions (adjust thresholds as needed)
        assert set_time < 5.0  # Should set 1000 items in less than 5 seconds
        assert get_time < 2.0  # Should get 1000 items in less than 2 seconds
        
        print(f"Set performance: {set_time:.2f}s for 1000 items")
        print(f"Get performance: {get_time:.2f}s for 1000 items")