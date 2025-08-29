"""Performance and benchmark tests for Smart CLI."""

import pytest
import time
import asyncio
import tempfile
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch
import psutil
import sys

from src.utils.config import ConfigManager
from src.utils.cache import MemoryCache, HybridCache, create_cache
from src.utils.ai_client import OpenRouterClient, ChatMessage


@pytest.mark.slow
class TestConfigPerformance:
    """Test configuration management performance."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Temporary config directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_config_load_performance(self, temp_config_dir):
        """Test configuration loading performance."""
        config_manager = ConfigManager(config_dir=temp_config_dir)
        
        # Set many config values
        start_time = time.time()
        for i in range(1000):
            config_manager.set_config(f'key_{i}', f'value_{i}')
        set_time = time.time() - start_time
        
        # Reload configuration
        start_time = time.time()
        new_config = ConfigManager(config_dir=temp_config_dir)
        load_time = time.time() - start_time
        
        # Performance assertions
        assert set_time < 5.0, f"Setting 1000 configs too slow: {set_time:.2f}s"
        assert load_time < 2.0, f"Loading 1000 configs too slow: {load_time:.2f}s"
        
        # Verify all configs loaded
        all_config = new_config.get_all_config()
        assert len([k for k in all_config.keys() if k.startswith('key_')]) == 1000
    
    def test_config_concurrent_access(self, temp_config_dir):
        """Test concurrent configuration access."""
        config_manager = ConfigManager(config_dir=temp_config_dir)
        
        def worker_function(worker_id):
            """Worker function for concurrent testing."""
            for i in range(100):
                key = f'worker_{worker_id}_key_{i}'
                value = f'worker_{worker_id}_value_{i}'
                config_manager.set_config(key, value)
                
                # Verify immediately
                retrieved = config_manager.get_config(key)
                assert retrieved == value, f"Concurrent access failed for {key}"
        
        # Run concurrent workers
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker_function, i) for i in range(5)]
            for future in futures:
                future.result()
        
        concurrent_time = time.time() - start_time
        
        # Should complete within reasonable time
        assert concurrent_time < 10.0, f"Concurrent config access too slow: {concurrent_time:.2f}s"
        
        # Verify all data is present
        all_config = config_manager.get_all_config()
        worker_keys = [k for k in all_config.keys() if k.startswith('worker_')]
        assert len(worker_keys) == 500  # 5 workers * 100 keys each


@pytest.mark.slow
class TestCachePerformance:
    """Test caching system performance."""
    
    def test_memory_cache_performance(self):
        """Test memory cache performance characteristics."""
        cache = MemoryCache(max_size=10000, default_ttl=3600)
        
        # Test set performance
        start_time = time.time()
        for i in range(5000):
            cache.set(f'key_{i}', f'value_{i}_{"x" * 100}')  # 100+ char values
        set_time = time.time() - start_time
        
        # Test get performance
        start_time = time.time()
        for i in range(5000):
            result = cache.get(f'key_{i}')
            assert result is not None
        get_time = time.time() - start_time
        
        # Test random access performance
        import random
        keys = [f'key_{i}' for i in range(5000)]
        random.shuffle(keys)
        
        start_time = time.time()
        for key in keys[:1000]:  # Test 1000 random accesses
            cache.get(key)
        random_access_time = time.time() - start_time
        
        # Performance assertions
        assert set_time < 2.0, f"Memory cache set too slow: {set_time:.2f}s for 5000 items"
        assert get_time < 1.0, f"Memory cache get too slow: {get_time:.2f}s for 5000 items"
        assert random_access_time < 0.5, f"Random access too slow: {random_access_time:.2f}s for 1000 items"
        
        print(f"Memory Cache Performance:")
        print(f"  Set: {set_time:.3f}s ({5000/set_time:.0f} ops/sec)")
        print(f"  Get: {get_time:.3f}s ({5000/get_time:.0f} ops/sec)")
        print(f"  Random Access: {random_access_time:.3f}s ({1000/random_access_time:.0f} ops/sec)")
    
    def test_memory_cache_lru_performance(self):
        """Test LRU eviction performance."""
        cache = MemoryCache(max_size=1000, default_ttl=3600)
        
        # Fill cache to capacity
        for i in range(1000):
            cache.set(f'key_{i}', f'value_{i}')
        
        # Test eviction performance by adding more items
        start_time = time.time()
        for i in range(1000, 2000):  # Add 1000 more items
            cache.set(f'key_{i}', f'value_{i}')
        eviction_time = time.time() - start_time
        
        # Should handle eviction efficiently
        assert eviction_time < 2.0, f"LRU eviction too slow: {eviction_time:.2f}s"
        assert len(cache.cache) == 1000  # Should maintain max size
        
        print(f"LRU Eviction Performance: {eviction_time:.3f}s for 1000 evictions")
    
    @pytest.mark.asyncio
    async def test_hybrid_cache_performance(self):
        """Test hybrid cache system performance."""
        cache = create_cache()
        
        # Test concurrent set operations
        async def set_worker(worker_id, count):
            for i in range(count):
                await cache.set(f'worker_{worker_id}_key_{i}', f'data_{worker_id}_{i}')
        
        start_time = time.time()
        await asyncio.gather(*[set_worker(i, 200) for i in range(5)])
        concurrent_set_time = time.time() - start_time
        
        # Test concurrent get operations
        async def get_worker(worker_id, count):
            for i in range(count):
                result = await cache.get(f'worker_{worker_id}_key_{i}')
                assert result == f'data_{worker_id}_{i}'
        
        start_time = time.time()
        await asyncio.gather(*[get_worker(i, 200) for i in range(5)])
        concurrent_get_time = time.time() - start_time
        
        # Performance assertions
        assert concurrent_set_time < 5.0, f"Concurrent cache set too slow: {concurrent_set_time:.2f}s"
        assert concurrent_get_time < 2.0, f"Concurrent cache get too slow: {concurrent_get_time:.2f}s"
        
        print(f"Hybrid Cache Concurrent Performance:")
        print(f"  Concurrent Set: {concurrent_set_time:.3f}s (1000 items, 5 workers)")
        print(f"  Concurrent Get: {concurrent_get_time:.3f}s (1000 items, 5 workers)")


@pytest.mark.slow  
class TestCLIPerformance:
    """Test CLI command performance."""
    
    def test_cli_import_time(self):
        """Test CLI module import performance."""
        import subprocess
        import sys
        
        # Measure import time
        start_time = time.time()
        result = subprocess.run([
            sys.executable, '-c',
            'from src.cli import app; print("Import successful")'
        ], capture_output=True, text=True, cwd=Path.cwd())
        import_time = time.time() - start_time
        
        assert result.returncode == 0, f"Import failed: {result.stderr}"
        assert import_time < 3.0, f"CLI import too slow: {import_time:.2f}s"
        
        print(f"CLI Import Time: {import_time:.3f}s")
    
    def test_cli_command_startup_overhead(self):
        """Test CLI command startup overhead."""
        from typer.testing import CliRunner
        from src.cli import app
        
        runner = CliRunner()
        
        # Test multiple command executions
        commands_to_test = [
            ['version'],
            ['--help'],
            ['config', '--help'],
            ['generate', '--help'],
        ]
        
        startup_times = []
        
        for cmd in commands_to_test:
            start_time = time.time()
            result = runner.invoke(app, cmd)
            end_time = time.time()
            
            startup_time = end_time - start_time
            startup_times.append(startup_time)
            
            # Commands should start quickly
            assert startup_time < 2.0, f"Command {' '.join(cmd)} startup too slow: {startup_time:.2f}s"
        
        avg_startup = sum(startup_times) / len(startup_times)
        print(f"Average CLI Command Startup: {avg_startup:.3f}s")
        print(f"Command Startup Times: {[f'{t:.3f}s' for t in startup_times]}")


@pytest.mark.slow
class TestMemoryUsage:
    """Test memory usage characteristics."""
    
    def test_config_manager_memory_usage(self):
        """Test ConfigManager memory efficiency."""
        import tracemalloc
        
        tracemalloc.start()
        
        # Create config manager and add data
        config_manager = ConfigManager()
        
        # Measure memory after adding configs
        snapshot1 = tracemalloc.take_snapshot()
        
        # Add many configurations
        for i in range(1000):
            config_manager.set_config(f'test_key_{i}', f'test_value_{i}' * 10)
        
        snapshot2 = tracemalloc.take_snapshot()
        
        # Calculate memory usage
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        total_memory = sum(stat.size for stat in top_stats)
        
        # Memory should be reasonable (less than 10MB for 1000 config items)
        assert total_memory < 10 * 1024 * 1024, f"Config memory usage too high: {total_memory / 1024 / 1024:.2f}MB"
        
        print(f"Config Manager Memory Usage: {total_memory / 1024 / 1024:.2f}MB for 1000 items")
        
        tracemalloc.stop()
    
    def test_cache_memory_efficiency(self):
        """Test cache memory efficiency."""
        import sys
        
        # Create caches and measure memory
        initial_memory = psutil.Process().memory_info().rss
        
        # Create memory cache with data
        cache = MemoryCache(max_size=5000)
        for i in range(2000):
            cache.set(f'key_{i}', f'value_{i}' * 50)  # ~50 char values
        
        after_cache_memory = psutil.Process().memory_info().rss
        cache_memory_usage = after_cache_memory - initial_memory
        
        # Memory per item should be reasonable
        memory_per_item = cache_memory_usage / 2000
        
        # Should use less than 1KB per cached item on average
        assert memory_per_item < 1024, f"Memory per cache item too high: {memory_per_item:.0f} bytes"
        
        print(f"Cache Memory Efficiency: {memory_per_item:.0f} bytes per item")
        print(f"Total Cache Memory: {cache_memory_usage / 1024 / 1024:.2f}MB for 2000 items")
    
    def test_memory_cleanup_after_operations(self):
        """Test that memory is properly cleaned up."""
        import gc
        
        initial_memory = psutil.Process().memory_info().rss
        
        # Perform memory-intensive operations
        for iteration in range(3):
            # Create temporary objects
            config = ConfigManager()
            cache = MemoryCache(max_size=1000)
            
            # Add data
            for i in range(500):
                config.set_config(f'iter_{iteration}_key_{i}', f'value_{i}' * 20)
                cache.set(f'iter_{iteration}_cache_{i}', f'cached_value_{i}' * 20)
            
            # Explicit cleanup
            del config
            del cache
            gc.collect()
        
        final_memory = psutil.Process().memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be minimal (less than 20MB)
        assert memory_growth < 20 * 1024 * 1024, f"Memory leak detected: {memory_growth / 1024 / 1024:.2f}MB growth"
        
        print(f"Memory Growth After Cleanup: {memory_growth / 1024 / 1024:.2f}MB")


@pytest.mark.slow
class TestScalabilityBenchmarks:
    """Test system scalability characteristics."""
    
    @pytest.mark.asyncio
    async def test_cache_scalability(self):
        """Test cache performance at different scales."""
        scales = [100, 500, 1000, 2000]
        results = {}
        
        for scale in scales:
            cache = create_cache()
            
            # Test set performance at scale
            start_time = time.time()
            for i in range(scale):
                await cache.set(f'scale_key_{i}', f'scale_value_{i}' * 10)
            set_time = time.time() - start_time
            
            # Test get performance at scale
            start_time = time.time()
            for i in range(scale):
                await cache.get(f'scale_key_{i}')
            get_time = time.time() - start_time
            
            results[scale] = {
                'set_time': set_time,
                'get_time': get_time,
                'set_ops_per_sec': scale / set_time,
                'get_ops_per_sec': scale / get_time
            }
        
        # Print scalability results
        print("Cache Scalability Results:")
        print("Scale\tSet Time\tGet Time\tSet Ops/sec\tGet Ops/sec")
        for scale, metrics in results.items():
            print(f"{scale}\t{metrics['set_time']:.3f}s\t\t{metrics['get_time']:.3f}s\t\t"
                  f"{metrics['set_ops_per_sec']:.0f}\t\t{metrics['get_ops_per_sec']:.0f}")
        
        # Performance should scale reasonably (not exponentially worse)
        # Check that larger scales don't have disproportionately worse performance
        small_scale_set_rate = results[100]['set_ops_per_sec']
        large_scale_set_rate = results[2000]['set_ops_per_sec']
        
        # Large scale should be at least 30% of small scale performance
        performance_ratio = large_scale_set_rate / small_scale_set_rate
        assert performance_ratio > 0.3, f"Cache doesn't scale well: {performance_ratio:.2f} performance ratio"
    
    def test_concurrent_load_handling(self):
        """Test system performance under concurrent load."""
        from concurrent.futures import ThreadPoolExecutor
        import threading
        
        def worker_load_test(worker_id, iterations=100):
            """Simulate work load for concurrent testing."""
            config = ConfigManager()
            cache = MemoryCache(max_size=200)
            
            start_time = time.time()
            
            # Simulate mixed operations
            for i in range(iterations):
                # Config operations
                config.set_config(f'worker_{worker_id}_key_{i}', f'value_{i}')
                config.get_config(f'worker_{worker_id}_key_{i}')
                
                # Cache operations
                cache.set(f'cache_key_{i}', f'cache_value_{i}')
                cache.get(f'cache_key_{i}')
            
            end_time = time.time()
            return {
                'worker_id': worker_id,
                'duration': end_time - start_time,
                'operations': iterations * 4  # 4 operations per iteration
            }
        
        # Test with increasing concurrent load
        worker_counts = [1, 2, 5, 10]
        results = {}
        
        for worker_count in worker_counts:
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=worker_count) as executor:
                futures = [executor.submit(worker_load_test, i) for i in range(worker_count)]
                worker_results = [future.result() for future in futures]
            
            total_time = time.time() - start_time
            total_operations = sum(r['operations'] for r in worker_results)
            avg_worker_time = sum(r['duration'] for r in worker_results) / worker_count
            
            results[worker_count] = {
                'total_time': total_time,
                'avg_worker_time': avg_worker_time,
                'total_operations': total_operations,
                'ops_per_second': total_operations / total_time,
                'efficiency': total_operations / (worker_count * avg_worker_time)
            }
        
        print("Concurrent Load Test Results:")
        print("Workers\tTotal Time\tAvg Worker Time\tOps/sec\t\tEfficiency")
        for workers, metrics in results.items():
            print(f"{workers}\t{metrics['total_time']:.2f}s\t\t{metrics['avg_worker_time']:.2f}s\t\t"
                  f"{metrics['ops_per_second']:.0f}\t\t{metrics['efficiency']:.0f}")
        
        # System should handle concurrent load reasonably
        # 10 workers should not be more than 5x slower than 1 worker
        single_worker_rate = results[1]['ops_per_second']
        multi_worker_rate = results[10]['ops_per_second']
        
        efficiency_ratio = multi_worker_rate / single_worker_rate
        assert efficiency_ratio > 0.2, f"Poor concurrent performance: {efficiency_ratio:.2f} efficiency ratio"


@pytest.mark.benchmark
class TestBenchmarkSuite:
    """Comprehensive benchmark suite."""
    
    def test_full_system_benchmark(self):
        """Run comprehensive system benchmark."""
        print("\n" + "="*50)
        print("SMART CLI PERFORMANCE BENCHMARK SUITE")
        print("="*50)
        
        benchmarks = {
            'config_operations': self._benchmark_config_operations,
            'cache_operations': self._benchmark_cache_operations,
            'memory_usage': self._benchmark_memory_usage,
            'startup_time': self._benchmark_startup_time,
        }
        
        results = {}
        for benchmark_name, benchmark_func in benchmarks.items():
            print(f"\nRunning {benchmark_name}...")
            try:
                result = benchmark_func()
                results[benchmark_name] = result
                print(f"✅ {benchmark_name}: PASSED")
            except Exception as e:
                print(f"❌ {benchmark_name}: FAILED - {e}")
                results[benchmark_name] = {'error': str(e)}
        
        # Print summary
        print(f"\n{'='*50}")
        print("BENCHMARK SUMMARY")
        print(f"{'='*50}")
        
        for name, result in results.items():
            if 'error' not in result:
                print(f"✅ {name}: {result.get('summary', 'PASSED')}")
            else:
                print(f"❌ {name}: {result['error']}")
    
    def _benchmark_config_operations(self):
        """Benchmark configuration operations."""
        config = ConfigManager()
        
        # Time config operations
        start_time = time.time()
        for i in range(1000):
            config.set_config(f'bench_key_{i}', f'bench_value_{i}')
        set_time = time.time() - start_time
        
        start_time = time.time()
        for i in range(1000):
            config.get_config(f'bench_key_{i}')
        get_time = time.time() - start_time
        
        return {
            'set_ops_per_sec': 1000 / set_time,
            'get_ops_per_sec': 1000 / get_time,
            'summary': f'{1000/set_time:.0f} set ops/sec, {1000/get_time:.0f} get ops/sec'
        }
    
    def _benchmark_cache_operations(self):
        """Benchmark cache operations."""
        cache = MemoryCache(max_size=2000)
        
        # Time cache operations
        start_time = time.time()
        for i in range(1500):
            cache.set(f'bench_cache_key_{i}', f'bench_cache_value_{i}' * 10)
        set_time = time.time() - start_time
        
        start_time = time.time()
        for i in range(1500):
            cache.get(f'bench_cache_key_{i}')
        get_time = time.time() - start_time
        
        return {
            'set_ops_per_sec': 1500 / set_time,
            'get_ops_per_sec': 1500 / get_time,
            'summary': f'{1500/set_time:.0f} cache ops/sec'
        }
    
    def _benchmark_memory_usage(self):
        """Benchmark memory usage."""
        import tracemalloc
        
        tracemalloc.start()
        initial_memory = psutil.Process().memory_info().rss
        
        # Create objects and use memory
        config = ConfigManager()
        cache = MemoryCache(max_size=1000)
        
        for i in range(500):
            config.set_config(f'mem_test_{i}', f'value_{i}' * 20)
            cache.set(f'cache_mem_{i}', f'cached_{i}' * 20)
        
        final_memory = psutil.Process().memory_info().rss
        memory_usage = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        tracemalloc.stop()
        
        return {
            'memory_usage_mb': memory_usage,
            'summary': f'{memory_usage:.1f}MB used for 1000 items'
        }
    
    def _benchmark_startup_time(self):
        """Benchmark CLI startup time."""
        import subprocess
        import sys
        
        times = []
        for _ in range(5):  # Average over 5 runs
            start_time = time.time()
            result = subprocess.run([
                sys.executable, '-c',
                'import sys; sys.path.insert(0, "."); from src.cli import app'
            ], capture_output=True, text=True, cwd=Path.cwd())
            end_time = time.time()
            
            if result.returncode == 0:
                times.append(end_time - start_time)
        
        avg_startup_time = sum(times) / len(times) if times else float('inf')
        
        return {
            'avg_startup_time': avg_startup_time,
            'summary': f'{avg_startup_time:.3f}s average startup'
        }