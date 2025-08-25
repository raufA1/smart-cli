"""Health check utilities for Smart CLI."""

import asyncio
import aiohttp
import sqlite3
from typing import Dict, Any, Callable
from pathlib import Path
import sys
import redis
from .config import ConfigManager


class HealthChecker:
    """Performs health checks on Smart CLI components."""
    
    def __init__(self):
        self.config = ConfigManager()
        self.checks = {}
        self._register_default_checks()
    
    def register_check(self, name: str, check_func: Callable):
        """Register a health check function."""
        self.checks[name] = check_func
    
    def _register_default_checks(self):
        """Register default health checks."""
        self.register_check('python', self._check_python)
        self.register_check('config', self._check_config)
        self.register_check('database', self._check_database)
        self.register_check('redis', self._check_redis)
        self.register_check('ai_service', self._check_ai_service)
        self.register_check('dependencies', self._check_dependencies)
    
    async def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks and return results."""
        results = {'status': 'healthy', 'checks': {}}
        
        for name, check_func in self.checks.items():
            try:
                result = await check_func()
                results['checks'][name] = {'status': 'healthy', 'details': result}
            except Exception as e:
                results['checks'][name] = {'status': 'unhealthy', 'error': str(e)}
                results['status'] = 'unhealthy'
        
        return results
    
    async def _check_python(self) -> Dict[str, Any]:
        """Check Python environment."""
        return {
            'version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'executable': sys.executable,
            'platform': sys.platform,
        }
    
    async def _check_config(self) -> Dict[str, Any]:
        """Check configuration status."""
        config_data = self.config.get_all_config()
        
        # Check for required configuration
        required_keys = ['default_model']
        missing_keys = [key for key in required_keys if not config_data.get(key)]
        
        if missing_keys:
            raise Exception(f"Missing required configuration: {missing_keys}")
        
        return {
            'config_file_exists': self.config.config_file.exists(),
            'secure_config_exists': self.config.secure_config_file.exists(),
            'config_keys_count': len(config_data),
            'has_api_key': bool(
                config_data.get('openrouter_api_key') or 
                config_data.get('anthropic_api_key') or
                config_data.get('openai_api_key')
            ),
        }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            # Check SQLite (used for caching)
            cache_db = Path.home() / ".smart-cli" / "cache.db"
            conn = sqlite3.connect(cache_db)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            
            return {
                'type': 'sqlite',
                'path': str(cache_db),
                'accessible': True,
            }
        except Exception as e:
            raise Exception(f"Database health check failed: {e}")
    
    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity."""
        redis_url = self.config.get_config('redis_url')
        
        if not redis_url:
            return {
                'configured': False,
                'status': 'Redis not configured (optional)',
            }
        
        try:
            r = redis.from_url(redis_url)
            r.ping()
            info = r.info()
            return {
                'configured': True,
                'connected': True,
                'version': info.get('redis_version'),
                'memory_usage': info.get('used_memory_human'),
            }
        except Exception as e:
            raise Exception(f"Redis connection failed: {e}")
    
    async def _check_ai_service(self) -> Dict[str, Any]:
        """Check AI service connectivity."""
        api_key = (
            self.config.get_config('openrouter_api_key') or
            self.config.get_config('anthropic_api_key') or
            self.config.get_config('openai_api_key')
        )
        
        if not api_key:
            return {
                'configured': False,
                'status': 'No AI API key configured',
            }
        
        try:
            # Simple health check to OpenRouter (if configured)
            if self.config.get_config('openrouter_api_key'):
                async with aiohttp.ClientSession() as session:
                    headers = {
                        'Authorization': f'Bearer {self.config.get_config("openrouter_api_key")}',
                        'Content-Type': 'application/json',
                    }
                    
                    # Test with a simple request
                    data = {
                        'model': self.config.get_config('default_model'),
                        'messages': [{'role': 'user', 'content': 'test'}],
                        'max_tokens': 5,
                    }
                    
                    timeout = aiohttp.ClientTimeout(total=10)
                    async with session.post(
                        'https://openrouter.ai/api/v1/chat/completions',
                        json=data,
                        headers=headers,
                        timeout=timeout
                    ) as response:
                        if response.status == 200:
                            return {
                                'service': 'openrouter',
                                'status': 'connected',
                                'model': self.config.get_config('default_model'),
                            }
                        else:
                            raise Exception(f"AI service returned status {response.status}")
            
            return {
                'configured': True,
                'status': 'API key present but not tested',
            }
            
        except asyncio.TimeoutError:
            raise Exception("AI service connection timeout")
        except Exception as e:
            raise Exception(f"AI service check failed: {e}")
    
    async def _check_dependencies(self) -> Dict[str, Any]:
        """Check required dependencies."""
        required_packages = [
            'typer', 'rich', 'click', 'pydantic', 
            'aiohttp', 'cryptography', 'pyjwt'
        ]
        
        missing_packages = []
        installed_packages = {}
        
        for package in required_packages:
            try:
                module = __import__(package)
                version = getattr(module, '__version__', 'unknown')
                installed_packages[package] = version
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            raise Exception(f"Missing required packages: {missing_packages}")
        
        return {
            'all_installed': len(missing_packages) == 0,
            'installed_packages': installed_packages,
            'missing_packages': missing_packages,
        }