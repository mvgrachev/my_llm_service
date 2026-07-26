"""Pytest configuration for LLM Service tests."""

import os
import sys
from unittest.mock import MagicMock, patch

# Set up environment variables before any imports
os.environ['YANDEX_CLOUD_FOLDER'] = 'test-folder-id'
os.environ['YANDEX_CLOUD_API_KEY'] = 'test-api-key'
os.environ['YANDEX_CLOUD_MODEL'] = 'deepseek-v4-flash/latest'
os.environ['APP_ENV'] = 'test'
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'

# Mock DeepSeekClient BEFORE any imports to prevent real API calls
# This must happen before the services.chat module is imported
sys.modules['deepseek'] = MagicMock()
sys.modules['deepseek_client'] = MagicMock()

# Clear cached imports to reload with new env vars and mocks
for module_name in list(sys.modules.keys()):
    if 'llm' in module_name or 'services' in module_name or 'api' in module_name or 'deepseek' in module_name:
        del sys.modules[module_name]
