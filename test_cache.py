#!/usr/bin/env python3
"""Test cache behavior."""
import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

from cache import cache
from api.models import ChatRequest
from services.chat import ChatService

# Check cache keys
print('Cache keys:', list(cache.client.keys('chat:*')))

# Test with same request twice
request = ChatRequest(message='Рассчитай КАСКО для Toyota Camry 2.5 л., 181 л.с.')
service = ChatService()

# First call
response1 = service.process_request(request)
print(f'First response: {response1.model_dump()}')

# Check cache after first call
print('Cache keys after first call:', list(cache.client.keys('chat:*')))

# Second call
response2 = service.process_request(request)
print(f'Second response: {response2.model_dump()}')

# Check if responses are identical
print(f'Responses identical: {response1.model_dump() == response2.model_dump()}')
