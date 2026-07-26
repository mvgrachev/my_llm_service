"""Test cache read."""
import sys
sys.path.insert(0, '/Users/mvgrachev/Downloads/my_llm_service')

from cache.redis_client import CacheClient
import json

cc = CacheClient()
print('Redis available:', cc.redis_available)
cc.set('test_key', {'model': 'Mitsubishi Pajero', 'price': 100000})
val = cc.get('test_key')
print('Value:', val)
print('Type:', type(val))
# Try to read again
val2 = cc.get('test_key')
print('Value2:', val2)
print('Type2:', type(val2))
