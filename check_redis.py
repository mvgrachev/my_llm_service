#!/usr/bin/env python3
"""Check Redis cache status."""
import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

from cache.redis_client import cache
print('Redis available:', cache.redis_available)
print('Cache type:', type(cache._cache).__name__)
