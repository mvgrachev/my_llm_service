"""Chat models and schemas."""

from pydantic import BaseModel, Field, field_validator
from typing import Any, Dict, Optional


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    
    message: str = Field(..., min_length=1, max_length=1000)
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate message is not empty and within length limit."""
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        if len(v) > 1000:
            raise ValueError('Message must be at most 1000 characters')
        return v.strip()


class ChatResponse(BaseModel):
    """Response model for chat endpoint.
    
    Corresponds to DeepSeek LLM response for KASCO calculation.
    Returns both raw text response and structured data.
    
    Expected JSON structure from DeepSeek:
    {
        "model": "Toyota",
        "price": 50000
    }
    """
    
    model: str
    price: float
