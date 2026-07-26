"""Debug script for cache testing."""
import json
from cache.redis_client import CacheClient, InMemoryCache

# Test InMemoryCache
print("=== Testing InMemoryCache ===")
imc = InMemoryCache()
imc.set('test_key', {'model': 'Mitsubishi Pajero', 'price': 100000})
val = imc.get('test_key')
print(f"Value: {val}")
print(f"Type: {type(val)}")

# Test CacheClient
print("\n=== Testing CacheClient ===")
cc = CacheClient()
print(f"Redis available: {cc.redis_available}")
print(f"Cache type: {type(cc._cache)}")

# Set and get
cc.set('test_key', {'model': 'Mitsubishi Pajero', 'price': 100000})
val = cc.get('test_key')
print(f"Value: {val}")
print(f"Type: {type(val)}")

# Test with Redis directly
print("\n=== Testing Redis directly ===")
import redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
r.set('redis_test', json.dumps({'model': 'Mitsubishi Pajero', 'price': 100000}))
val = r.get('redis_test')
print(f"Value: {val}")
print(f"Type: {type(val)}")
parsed = json.loads(val)
print(f"Parsed: {parsed}")
print(f"Parsed type: {type(parsed)}")
