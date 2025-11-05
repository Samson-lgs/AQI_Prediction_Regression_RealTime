"""
Redis Caching Utility for AQI Prediction System
Provides caching layer for frequently accessed data
"""
import redis
import json
import logging
from functools import wraps
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class RedisCache:
    """Redis cache manager for API responses"""
    
    def __init__(self):
        """Initialize Redis connection"""
        self.redis_client = None
        self.enabled = False
        
        try:
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            redis_db = int(os.getenv('REDIS_DB', 0))
            redis_password = os.getenv('REDIS_PASSWORD', None)
            
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            logger.info(f"Redis cache connected: {redis_host}:{redis_port}")
            
        except redis.ConnectionError:
            logger.warning("Redis not available - caching disabled")
            self.enabled = False
        except Exception as e:
            logger.error(f"Redis initialization error: {str(e)}")
            self.enabled = False
    
    def get(self, key):
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            else:
                logger.debug(f"Cache MISS: {key}")
                return None
        except Exception as e:
            logger.error(f"Redis GET error: {str(e)}")
            return None
    
    def set(self, key, value, expire=300):
        """Set value in cache with expiration (seconds)"""
        if not self.enabled:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            self.redis_client.setex(key, expire, serialized)
            logger.debug(f"Cache SET: {key} (expires in {expire}s)")
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {str(e)}")
            return False
    
    def delete(self, key):
        """Delete key from cache"""
        if not self.enabled:
            return False
        
        try:
            self.redis_client.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {str(e)}")
            return False
    
    def delete_pattern(self, pattern):
        """Delete all keys matching pattern"""
        if not self.enabled:
            return False
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Cache DELETE PATTERN: {pattern} ({len(keys)} keys)")
            return True
        except Exception as e:
            logger.error(f"Redis DELETE PATTERN error: {str(e)}")
            return False
    
    def clear_all(self):
        """Clear all cache"""
        if not self.enabled:
            return False
        
        try:
            self.redis_client.flushdb()
            logger.warning("Cache CLEARED - all keys deleted")
            return True
        except Exception as e:
            logger.error(f"Redis FLUSH error: {str(e)}")
            return False
    
    def get_stats(self):
        """Get cache statistics"""
        if not self.enabled:
            return {'enabled': False}
        
        try:
            info = self.redis_client.info('stats')
            return {
                'enabled': True,
                'total_keys': self.redis_client.dbsize(),
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(info)
            }
        except Exception as e:
            logger.error(f"Redis STATS error: {str(e)}")
            return {'enabled': False, 'error': str(e)}
    
    def _calculate_hit_rate(self, info):
        """Calculate cache hit rate"""
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)

# Global cache instance
cache = RedisCache()

# ============================================================================
# Cache Decorators
# ============================================================================

def cached(expire=300, key_prefix=''):
    """
    Decorator to cache function results
    
    Args:
        expire: Cache expiration time in seconds (default 300 = 5 minutes)
        key_prefix: Optional prefix for cache key
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}{f.__name__}"
            
            # Add args to key (skip 'self' for methods)
            for arg in args:
                if arg.__class__.__name__ != 'Resource':  # Skip Flask-RESTX Resource
                    cache_key += f":{arg}"
            
            # Add relevant kwargs to key
            for k, v in sorted(kwargs.items()):
                cache_key += f":{k}={v}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Returning cached result for {f.__name__}")
                return cached_result
            
            # Execute function
            result = f(*args, **kwargs)
            
            # Cache the result
            cache.set(cache_key, result, expire)
            
            return result
        
        return decorated_function
    return decorator

def invalidate_cache(pattern='*'):
    """
    Invalidate cache entries matching pattern
    
    Args:
        pattern: Redis key pattern (default '*' for all)
    """
    cache.delete_pattern(pattern)
    logger.info(f"Cache invalidated: {pattern}")

# ============================================================================
# Specific Cache Functions
# ============================================================================

def cache_city_aqi(city, aqi_data, expire=300):
    """Cache current AQI data for a city"""
    key = f"aqi:current:{city}"
    return cache.set(key, aqi_data, expire)

def get_cached_city_aqi(city):
    """Get cached AQI data for a city"""
    key = f"aqi:current:{city}"
    return cache.get(key)

def cache_city_forecast(city, hours, forecast_data, expire=600):
    """Cache forecast data for a city"""
    key = f"forecast:{city}:{hours}h"
    return cache.set(key, forecast_data, expire)

def get_cached_city_forecast(city, hours):
    """Get cached forecast data for a city"""
    key = f"forecast:{city}:{hours}h"
    return cache.get(key)

def cache_model_metrics(city, model, metrics, expire=3600):
    """Cache model performance metrics"""
    key = f"metrics:{city}:{model}"
    return cache.set(key, metrics, expire)

def get_cached_model_metrics(city, model):
    """Get cached model metrics"""
    key = f"metrics:{city}:{model}"
    return cache.get(key)

def cache_cities_list(cities, expire=3600):
    """Cache list of cities"""
    key = "cities:list"
    return cache.set(key, cities, expire)

def get_cached_cities_list():
    """Get cached cities list"""
    key = "cities:list"
    return cache.get(key)

def cache_city_rankings(rankings, days, metric, expire=1800):
    """Cache city rankings"""
    key = f"rankings:{days}d:{metric}"
    return cache.set(key, rankings, expire)

def get_cached_city_rankings(days, metric):
    """Get cached city rankings"""
    key = f"rankings:{days}d:{metric}"
    return cache.get(key)

def invalidate_city_cache(city):
    """Invalidate all cache entries for a city"""
    patterns = [
        f"aqi:current:{city}",
        f"forecast:{city}:*",
        f"metrics:{city}:*"
    ]
    for pattern in patterns:
        cache.delete_pattern(pattern)
    logger.info(f"Invalidated cache for city: {city}")

def invalidate_all_forecasts():
    """Invalidate all forecast caches"""
    cache.delete_pattern("forecast:*")
    logger.info("Invalidated all forecast caches")

# ============================================================================
# Cache Warming (preload frequently accessed data)
# ============================================================================

def warm_cache():
    """Pre-populate cache with frequently accessed data"""
    if not cache.enabled:
        logger.warning("Cache warming skipped - Redis not available")
        return
    
    try:
        from config.settings import CITIES, PRIORITY_CITIES
        from database.db_operations import DatabaseOperations
        from datetime import datetime, timedelta
        
        db = DatabaseOperations()
        logger.info("Starting cache warming...")
        
        # Cache cities list
        cache_cities_list(CITIES)
        
        # Cache current AQI for priority cities
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=1)
        
        for city in PRIORITY_CITIES:
            try:
                data = db.get_pollution_data(city, start_date, end_date)
                if data:
                    latest = data[0]
                    cache_city_aqi(city, latest, expire=300)
            except Exception as city_error:
                logger.error(f"Error warming cache for {city}: {str(city_error)}")
        
        logger.info("Cache warming completed")
        
    except Exception as e:
        logger.error(f"Cache warming error: {str(e)}")

# ============================================================================
# Cache Monitoring
# ============================================================================

def get_cache_info():
    """Get comprehensive cache information"""
    if not cache.enabled:
        return {
            'status': 'disabled',
            'message': 'Redis cache is not available'
        }
    
    try:
        stats = cache.get_stats()
        
        return {
            'status': 'enabled',
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }
