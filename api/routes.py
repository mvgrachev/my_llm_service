"""Chat routing and endpoints."""

from fastapi import APIRouter, HTTPException
from api.models import ChatRequest, ChatResponse
from services import chat_service
import logging

logger = logging.getLogger('llm_service.routes')

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Process chat message and return response from LLM.
    
    Args:
        request: ChatRequest with message field
        
    Returns:
        ChatResponse with message and LLM response
        
    Raises:
        HTTPException: If LLM call fails
    """
    try:
        response = chat_service.process_request(request)
        return response
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
