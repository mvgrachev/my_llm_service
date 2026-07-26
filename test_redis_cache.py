#!/usr/bin/env python3
"""Test Redis cache."""
import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

from cache import cache
from api.models import ChatRequest
from services.chat import ChatService

# Check existing cache keys
if hasattr(cache, '_cache'):
    try:
        if hasattr(cache._cache, 'keys'):
            keys = list(cache._cache.keys('chat:*'))
            print('Cache keys before:', keys)
        else:
            print('Cache _cache has no keys() method')
    except Exception as e:
        print(f'Error getting keys: {e}')
else:
    print('Cache has no _cache attribute')

# Test with same request twice
request = ChatRequest(message='Test BMW X5 3.0 л., 265 л.с.')
service = ChatService()

# First call
response1 = service.process_request(request)
print(f'First response: {response1.model_dump()}')

# Check cache after first call
if hasattr(cache, '_cache'):
    try:
        if hasattr(cache._cache, 'keys'):
            keys = list(cache._cache.keys('chat:*'))
            print('Cache keys after first:', keys)
        else:
            print('Cache _cache has no keys() method')
    except Exception as e:
        print(f'Error getting keys: {e}')

# Second call
response2 = service.process_request(request)
print(f'Second response: {response2.model_dump()}')

# Check if responses are identical
print(f'Responses identical: {response1.model_dump() == response2.model_dump()}')

# Check if cache is being used
print(f'Cache redis_available: {cache.redis_available}')
