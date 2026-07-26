"""Environment utilities for LLM Service."""

from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()


def get_env_variable(name: str, default: str = None) -> str:
    """
    Get environment variable with optional default value.
    
    Args:
        name: Variable name
        default: Default value if not found
        
    Returns:
        Environment variable value
    """
    return os.getenv(name, default)