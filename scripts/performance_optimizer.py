#!/usr/bin/env python3
"""
Performance Optimizer for Fraud Detection System
Implements advanced caching, connection pooling, and optimization strategies
"""

import time
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, OrderedDict
import hashlib
import pickle
import redis
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class CacheConfig:
    """Cache configuration"""
    max_size: int = 10000
    ttl_seconds: int = 3600  # 1 hour
    cleanup_interval: int = 300  # 5 minutes

@dataclass
class PerformanceMetrics:
    """Performance tracking metrics"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    avg_response_time: float = 0.0
    peak_memory_usage: float = 0.0
    concurrent_requests: int = 0
    error_rate: float = 0.0

class LRUCache:
    """Thread-safe LRU Cache implementation"""
    
    def __init__(self, max_size: int = 10000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = OrderedDict()
        self.timestamps = {}
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        if key not in self.timestamps:
            return True
        
        age = time.time() - self.timestamps[key]
        return age > self.ttl_seconds
    
    def _cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = []
        
        for key, timestamp in self.timestamps.items():
            if current_time - timestamp > self.ttl_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            self.cache.pop(key, None)
            self.timestamps.pop(key, None)
    
    def get(self, key: str) -> Any:
        """Get value from cache"""
        with self.lock:
            # Cleanup expired entries
            if len(self.cache) > self.max_size * 0.8:
                self._cleanup_expired()
            
            if key in self.cache and not self._is_expired(key):
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.hits += 1
                return self.cache[key]
            else:
                # Remove if expired
                self.cache.pop(key, None)
                self.timestamps.pop(key, None)
                self.misses += 1
                return None
    
    def put(self, key: str, value: Any):
        """Put value in cache"""
        with self.lock:
            current_time = time.time()
            
            # Remove if exists and expired
            if key in self.cache and self._is_expired(key):
                self.cache.pop(key, None)
                self.timestamps.pop(key, None)
            
            # Add new entry
            self.cache[key] = value
            self.timestamps[key] = current_time
            
            # Move to end
            self.cache.move_to_end(key)
            
            # Remove oldest if over capacity
            while len(self.cache) > self.max_size:
                oldest_key = next(iter(self.cache))
                self.cache.pop(oldest_key)
                self.timestamps.pop(oldest_key)
    
    def clear(self):
        """Clear cache"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = self.hits / max(total_requests, 1)
            
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "ttl_seconds": self.ttl_seconds
            }

class RedisCache:
    """Redis-based distributed cache"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, 
                 db: int = 0, ttl_seconds: int = 3600):
        self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=False)
        self.ttl_seconds = ttl_seconds
        self.hits = 0
        self.misses = 0
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for Redis storage"""
        return pickle.dumps(value)
    
    def _deserialize(self, value: bytes) -> Any:
        """Deserialize value from Redis storage"""
        return pickle.loads(value)
    
    def get(self, key: str) -> Any:
        """Get value from Redis cache"""
        try:
            value = self.redis_client.get(key)
            if value:
                self.hits += 1
                return self._deserialize(value)
            else:
                self.misses += 1
                return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            self.misses += 1
            return None
    
    def put(self, key: str, value: Any):
        """Put value in Redis cache"""
        try:
            serialized_value = self._serialize(value)
            self.redis_client.setex(key, self.ttl_seconds, serialized_value)
        except Exception as e:
            logger.error(f"Redis put error: {e}")
    
    def clear(self):
        """Clear all cache entries"""
        try:
            self.redis_client.flushdb()
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            info = self.redis_client.info()
            total_requests = self.hits + self.misses
            hit_rate = self.hits / max(total_requests, 1)
            
            return {
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "memory_usage": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "ttl_seconds": self.ttl_seconds
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {"error": str(e)}

class ConnectionPool:
    """Thread-safe HTTP connection pool"""
    
    def __init__(self, base_url: str, max_connections: int = 100):
        self.base_url = base_url
        self.max_connections = max_connections
        self.pool = ThreadPoolExecutor(max_workers=max_connections)
        self.active_connections = 0
        self.lock = threading.Lock()
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request using connection pool"""
        url = f"{self.base_url}{endpoint}"
        
        with self.lock:
            self.active_connections += 1
        
        try:
            future = self.pool.submit(
                lambda: requests.request(method, url, **kwargs)
            )
            response = future.result(timeout=30)
            return response
        finally:
            with self.lock:
                self.active_connections -= 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        return {
            "max_connections": self.max_connections,
            "active_connections": self.active_connections,
            "pool_size": self.pool._max_workers
        }

class FeatureCache:
    """Specialized cache for ML features"""
    
    def __init__(self, cache_backend: LRUCache, redis_cache: RedisCache = None):
        self.memory_cache = cache_backend
        self.redis_cache = redis_cache
        self.feature_stats = defaultdict(int)
    
    def _generate_key(self, customer_id: str, feature_type: str) -> str:
        """Generate cache key for customer features"""
        return f"features:{customer_id}:{feature_type}"
    
    def get_customer_features(self, customer_id: str) -> Dict[str, Any]:
        """Get cached customer features"""
        key = self._generate_key(customer_id, "profile")
        
        # Try memory cache first
        features = self.memory_cache.get(key)
        if features:
            self.feature_stats["memory_hits"] += 1
            return features
        
        # Try Redis cache
        if self.redis_cache:
            features = self.redis_cache.get(key)
            if features:
                self.feature_stats["redis_hits"] += 1
                # Store in memory cache for faster access
                self.memory_cache.put(key, features)
                return features
        
        self.feature_stats["misses"] += 1
        return None
    
    def put_customer_features(self, customer_id: str, features: Dict[str, Any]):
        """Cache customer features"""
        key = self._generate_key(customer_id, "profile")
        
        # Store in memory cache
        self.memory_cache.put(key, features)
        
        # Store in Redis cache
        if self.redis_cache:
            self.redis_cache.put(key, features)
    
    def get_transaction_features(self, transaction_id: str) -> Dict[str, Any]:
        """Get cached transaction features"""
        key = self._generate_key(transaction_id, "transaction")
        
        features = self.memory_cache.get(key)
        if features:
            return features
        
        if self.redis_cache:
            features = self.redis_cache.get(key)
            if features:
                self.memory_cache.put(key, features)
                return features
        
        return None
    
    def put_transaction_features(self, transaction_id: str, features: Dict[str, Any]):
        """Cache transaction features"""
        key = self._generate_key(transaction_id, "transaction")
        
        self.memory_cache.put(key, features)
        if self.redis_cache:
            self.redis_cache.put(key, features)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get feature cache statistics"""
        return {
            "memory_cache": self.memory_cache.get_stats(),
            "redis_cache": self.redis_cache.get_stats() if self.redis_cache else None,
            "feature_stats": dict(self.feature_stats)
        }

class PerformanceOptimizer:
    """Main performance optimization coordinator"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        
        # Initialize caches
        self.memory_cache = LRUCache(max_size=10000, ttl_seconds=3600)
        try:
            self.redis_cache = RedisCache(ttl_seconds=3600)
            logger.info("Redis cache initialized")
        except Exception as e:
            logger.warning(f"Redis cache not available: {e}")
            self.redis_cache = None
        
        # Initialize feature cache
        self.feature_cache = FeatureCache(self.memory_cache, self.redis_cache)
        
        # Initialize connection pool
        self.connection_pool = ConnectionPool(api_base_url, max_connections=50)
        
        # Performance metrics
        self.metrics = PerformanceMetrics()
        self.response_times = deque(maxlen=1000)
        
        # Optimization settings
        self.optimization_enabled = True
        self.batch_size = 10
        self.concurrency_limit = 20
    
    def optimize_prediction_request(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize single prediction request"""
        
        start_time = time.time()
        
        # Check cache first
        cache_key = self._generate_transaction_cache_key(transaction)
        cached_result = self.memory_cache.get(cache_key)
        
        if cached_result:
            self.metrics.cache_hits += 1
            self.metrics.total_requests += 1
            
            response_time = (time.time() - start_time) * 1000
            self.response_times.append(response_time)
            
            return cached_result
        
        self.metrics.cache_misses += 1
        
        # Make optimized request
        try:
            response = self.connection_pool.make_request(
                "POST", "/predict/single",
                json=transaction,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Cache the result
                self.memory_cache.put(cache_key, result)
                
                # Update metrics
                self.metrics.total_requests += 1
                response_time = (time.time() - start_time) * 1000
                self.response_times.append(response_time)
                
                return result
            else:
                self.metrics.error_rate += 1
                raise Exception(f"API error: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Prediction request failed: {e}")
            self.metrics.error_rate += 1
            raise
    
    def optimize_batch_prediction(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Optimize batch prediction request"""
        
        start_time = time.time()
        
        # Check cache for individual transactions
        cached_results = []
        uncached_transactions = []
        
        for tx in transactions:
            cache_key = self._generate_transaction_cache_key(tx)
            cached_result = self.memory_cache.get(cache_key)
            
            if cached_result:
                cached_results.append(cached_result)
                self.metrics.cache_hits += 1
            else:
                uncached_transactions.append(tx)
                self.metrics.cache_misses += 1
        
        # Make batch request for uncached transactions
        batch_results = []
        if uncached_transactions:
            try:
                response = self.connection_pool.make_request(
                    "POST", "/predict/batch",
                    json=uncached_transactions,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    batch_results = result['predictions']
                    
                    # Cache individual results
                    for tx, pred in zip(uncached_transactions, batch_results):
                        cache_key = self._generate_transaction_cache_key(tx)
                        self.memory_cache.put(cache_key, pred)
                
            except Exception as e:
                logger.error(f"Batch prediction failed: {e}")
                self.metrics.error_rate += 1
                raise
        
        # Combine results
        all_results = cached_results + batch_results
        
        # Update metrics
        self.metrics.total_requests += 1
        response_time = (time.time() - start_time) * 1000
        self.response_times.append(response_time)
        
        return {
            "predictions": all_results,
            "total_transactions": len(transactions),
            "cached_transactions": len(cached_results),
            "processed_transactions": len(uncached_transactions),
            "latency_ms": response_time,
            "cache_hit_rate": len(cached_results) / len(transactions)
        }
    
    def optimize_concurrent_requests(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize concurrent prediction requests"""
        
        start_time = time.time()
        results = []
        
        # Use thread pool for concurrent processing
        with ThreadPoolExecutor(max_workers=self.concurrency_limit) as executor:
            # Submit all requests
            future_to_tx = {
                executor.submit(self.optimize_prediction_request, tx): tx
                for tx in transactions
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_tx):
                tx = future_to_tx[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Concurrent request failed for {tx.get('transaction_id')}: {e}")
                    # Add error result
                    results.append({
                        "transaction_id": tx.get('transaction_id'),
                        "error": str(e)
                    })
        
        # Update metrics
        response_time = (time.time() - start_time) * 1000
        self.response_times.append(response_time)
        
        return results
    
    def _generate_transaction_cache_key(self, transaction: Dict[str, Any]) -> str:
        """Generate cache key for transaction"""
        # Create a deterministic key based on transaction features
        key_data = {
            "type": transaction.get("type"),
            "amount": transaction.get("amount"),
            "oldbalanceOrg": transaction.get("oldbalanceOrg"),
            "newbalanceOrig": transaction.get("newbalanceOrig"),
            "oldbalanceDest": transaction.get("oldbalanceDest"),
            "newbalanceDest": transaction.get("newbalanceDest"),
            "nameOrig": transaction.get("nameOrig"),
            "nameDest": transaction.get("nameDest")
        }
        
        # Create hash
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def precompute_customer_features(self, customer_ids: List[str]):
        """Precompute and cache customer features"""
        
        logger.info(f"Precomputing features for {len(customer_ids)} customers")
        
        for customer_id in customer_ids:
            # In a real system, this would compute actual features
            # For demo, we'll create mock features
            features = {
                "customer_id": customer_id,
                "transaction_count": np.random.randint(10, 1000),
                "avg_transaction_amount": np.random.uniform(100, 10000),
                "fraud_history": np.random.random() < 0.1,
                "account_age_days": np.random.randint(30, 3650),
                "last_transaction": (datetime.now() - timedelta(days=np.random.randint(0, 30))).isoformat()
            }
            
            self.feature_cache.put_customer_features(customer_id, features)
        
        logger.info("Customer features precomputed and cached")
    
    def warm_up_cache(self, sample_transactions: List[Dict[str, Any]]):
        """Warm up cache with sample transactions"""
        
        logger.info(f"Warming up cache with {len(sample_transactions)} sample transactions")
        
        for tx in sample_transactions:
            cache_key = self._generate_transaction_cache_key(tx)
            
            # Make prediction to warm up cache
            try:
                result = self.optimize_prediction_request(tx)
                self.memory_cache.put(cache_key, result)
            except Exception as e:
                logger.warning(f"Cache warm-up failed for transaction {tx.get('transaction_id')}: {e}")
        
        logger.info("Cache warm-up completed")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        
        # Calculate average response time
        if self.response_times:
            avg_response_time = np.mean(list(self.response_times))
            p95_response_time = np.percentile(list(self.response_times), 95)
            p99_response_time = np.percentile(list(self.response_times), 99)
        else:
            avg_response_time = 0
            p95_response_time = 0
            p99_response_time = 0
        
        # Calculate cache hit rate
        total_cache_requests = self.metrics.cache_hits + self.metrics.cache_misses
        cache_hit_rate = self.metrics.cache_hits / max(total_cache_requests, 1)
        
        return {
            "requests": {
                "total": self.metrics.total_requests,
                "cache_hits": self.metrics.cache_hits,
                "cache_misses": self.metrics.cache_misses,
                "cache_hit_rate": cache_hit_rate,
                "error_rate": self.metrics.error_rate / max(self.metrics.total_requests, 1)
            },
            "response_times": {
                "average_ms": avg_response_time,
                "p95_ms": p95_response_time,
                "p99_ms": p99_response_time,
                "min_ms": min(self.response_times) if self.response_times else 0,
                "max_ms": max(self.response_times) if self.response_times else 0
            },
            "memory_cache": self.memory_cache.get_stats(),
            "redis_cache": self.redis_cache.get_stats() if self.redis_cache else None,
            "feature_cache": self.feature_cache.get_stats(),
            "connection_pool": self.connection_pool.get_stats(),
            "optimization_settings": {
                "enabled": self.optimization_enabled,
                "batch_size": self.batch_size,
                "concurrency_limit": self.concurrency_limit
            }
        }
    
    def clear_all_caches(self):
        """Clear all caches"""
        self.memory_cache.clear()
        if self.redis_cache:
            self.redis_cache.clear()
        logger.info("All caches cleared")
    
    def benchmark_optimizations(self, test_transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Benchmark performance with and without optimizations"""
        
        logger.info("Running performance benchmark...")
        
        # Test without optimizations
        start_time = time.time()
        unoptimized_results = []
        
        for tx in test_transactions:
            try:
                response = requests.post(f"{self.api_base_url}/predict/single", json=tx, timeout=10)
                if response.status_code == 200:
                    unoptimized_results.append(response.json())
            except Exception as e:
                logger.error(f"Unoptimized request failed: {e}")
        
        unoptimized_time = time.time() - start_time
        
        # Test with optimizations
        start_time = time.time()
        optimized_results = self.optimize_concurrent_requests(test_transactions)
        optimized_time = time.time() - start_time
        
        # Calculate improvement
        improvement_factor = unoptimized_time / max(optimized_time, 0.001)
        
        benchmark_results = {
            "test_transactions": len(test_transactions),
            "unoptimized": {
                "total_time_seconds": unoptimized_time,
                "avg_time_per_request_ms": (unoptimized_time / len(test_transactions)) * 1000,
                "successful_requests": len(unoptimized_results)
            },
            "optimized": {
                "total_time_seconds": optimized_time,
                "avg_time_per_request_ms": (optimized_time / len(test_transactions)) * 1000,
                "successful_requests": len([r for r in optimized_results if "error" not in r])
            },
            "improvement": {
                "speedup_factor": improvement_factor,
                "time_saved_percent": ((unoptimized_time - optimized_time) / unoptimized_time) * 100
            }
        }
        
        logger.info(f"Benchmark completed: {improvement_factor:.2f}x speedup")
        
        return benchmark_results

def main():
    """Main function to demonstrate performance optimization"""
    
    print("FRAUD DETECTION - PERFORMANCE OPTIMIZER")
    print("=" * 50)
    
    # Initialize optimizer
    optimizer = PerformanceOptimizer()
    
    # Generate test data
    from demo_data_generator import FraudDemoDataGenerator
    generator = FraudDemoDataGenerator()
    
    test_transactions = generator.generate_batch(size=100, fraud_rate=0.1)
    
    print(f"Generated {len(test_transactions)} test transactions")
    
    # Precompute customer features
    customer_ids = list(set(tx['nameOrig'] for tx in test_transactions))
    optimizer.precompute_customer_features(customer_ids[:20])  # Limit for demo
    
    # Warm up cache
    optimizer.warm_up_cache(test_transactions[:10])
    
    # Run benchmark
    benchmark_results = optimizer.benchmark_optimizations(test_transactions[:50])
    
    print("\nBENCHMARK RESULTS:")
    print("-" * 30)
    print(f"Unoptimized: {benchmark_results['unoptimized']['avg_time_per_request_ms']:.2f}ms per request")
    print(f"Optimized: {benchmark_results['optimized']['avg_time_per_request_ms']:.2f}ms per request")
    print(f"Speedup: {benchmark_results['improvement']['speedup_factor']:.2f}x")
    print(f"Time saved: {benchmark_results['improvement']['time_saved_percent']:.1f}%")
    
    # Get performance stats
    stats = optimizer.get_performance_stats()
    
    print(f"\nPERFORMANCE STATISTICS:")
    print("-" * 30)
    print(f"Total Requests: {stats['requests']['total']}")
    print(f"Cache Hit Rate: {stats['requests']['cache_hit_rate']*100:.1f}%")
    print(f"Average Response Time: {stats['response_times']['average_ms']:.2f}ms")
    print(f"95th Percentile: {stats['response_times']['p95_ms']:.2f}ms")
    print(f"99th Percentile: {stats['response_times']['p99_ms']:.2f}ms")
    
    if stats['redis_cache']:
        print(f"Redis Memory Usage: {stats['redis_cache']['memory_usage']}")
    
    print("\nOptimization demo completed!")

if __name__ == "__main__":
    main()
