from api.models import ChatRequest, ChatResponse
from llm import deepseek_client
from config import settings
from cache import cache
from typing import Optional
import json
import hashlib
import time
import logging
import socket
import re

logger = logging.getLogger('llm_service.chat')


class ChatService:
    """Service for handling chat interactions with LLM."""
    
    def __init__(self, client=None, settings=None, cache_client=None):
        """
        Initialize ChatService.
        
        Args:
            client: LLM client instance (defaults to deepseek_client)
            settings: Application settings (defaults to config.settings)
            cache_client: Cache client instance (defaults to cache.cache)
        """
        self.client = client or deepseek_client
        self.settings = settings or settings
        self.cache = cache_client or cache
        self.cache_ttl = 600  # 10 minutes in seconds
    
    def _generate_cache_key(self, request: ChatRequest, temperature: float, max_output_tokens: int) -> str:
        """
        Generate cache key from request parameters.
        
        Args:
            request: ChatRequest object
            temperature: Temperature for generation
            max_output_tokens: Maximum output tokens
            
        Returns:
            MD5 hash of request parameters
        """
        key_data = {
            "message": request.message,
            "temperature": temperature,
            "max_output_tokens": max_output_tokens
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return f"chat:{hashlib.md5(key_str.encode()).hexdigest()}"
    
    def _check_network(self, timeout: int = 5) -> bool:
        """Check if network is available."""
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            return True
        except socket.error:
            return False
    
    def _parse_llm_response(self, response: str) -> dict:
        """
        Parse LLM response and extract model and price fields.
        Handles both English and Russian field names.
        
        Args:
            response: Raw LLM response string
            
        Returns:
            Dict with model and price keys
        """
        # Try to parse as JSON first
        try:
            data = json.loads(response)
            
            # Map Russian field names to English
            result = {}
            
            # Get model/brand
            for key in ['model', 'марка_автомобиля', 'brand', 'автомобиль']:
                if key in data:
                    result['model'] = str(data[key])
                    break
            
            # Get price
            for key in ['price', 'стоимость_каско', 'стоимость', 'цена']:
                if key in data:
                    result['price'] = float(data[key])
                    break
            
            return result
        except json.JSONDecodeError:
            # Try to extract values using regex
            model_match = re.search(r'"(?:марка_автомобиля|model|brand)"\s*:\s*"([^"]+)"', response)
            price_match = re.search(r'"(?:стоимость_каско|price|стоимость)"\s*:\s*(\d+)', response)
            
            result = {}
            if model_match:
                result['model'] = model_match.group(1)
            if price_match:
                result['price'] = float(price_match.group(1))
            
            return result
    
    def _create_fallback_response(self, error_message: str) -> ChatResponse:
        """
        Create fallback response for network errors.
        
        Args:
            error_message: Description of the error
            
        Returns:
            ChatResponse with fallback error data
        """
        return ChatResponse(
            message="",
            model="Ошибка",
            price=0.0
        )
    
    def process_request(
        self,
        request: ChatRequest,
        temperature: float = 0.3,
        max_output_tokens: int = 1500,
        system_prompt: Optional[str] = None
    ) -> ChatResponse:
        """
        Process chat request and generate LLM response.
        Implements retry logic with timeout and fallback for network errors.
        Uses Redis cache to store/retrieve responses for duplicate requests.
        
        Retry strategy:
        - First retry: 1 second
        - Second retry: 3 seconds  
        - Third retry: 5 seconds
        - Timeout: 30 seconds per request
        - Cache TTL: 10 minutes
        
        Args:
            request: Validated ChatRequest from API layer
            temperature: Temperature for generation (0.0-1.0)
            max_output_tokens: Maximum output tokens
            system_prompt: Custom system prompt (uses default if None)
            
        Returns:
            ChatResponse with original message and LLM response
            
        Raises:
            Exception: If LLM call fails after all retries
        """
        # Log request start
        logger.info(f"[REQUEST] Time: {time.strftime('%Y-%m-%d %H:%M:%S')}, Message: {request.message[:100]}...")
        
        # Generate cache key
        cache_key = self._generate_cache_key(request, temperature, max_output_tokens)
        
        # Try to get from cache first
        cached_response = self.cache.get(cache_key)
        if cached_response:
            logger.info(f"[CACHE HIT] Key: {cache_key}, Response: {json.dumps(cached_response)}")
            return ChatResponse(**cached_response)
        
        logger.info(f"[CACHE MISS] Key: {cache_key}")
        
        max_retries = 3
        wait_times = [1, 3, 5]  # Wait times between retries
        
        for attempt in range(max_retries):
            try:
                # Log prompt being sent
                logger.info(f"[PROMPT] Temperature: {temperature}, Max tokens: {max_output_tokens}")
                
                # Generate response from LLM
                llm_response = self.client.generate(
                    input_text=request.message,
                    temperature=temperature,
                    instructions=system_prompt,
                    max_output_tokens=max_output_tokens
                )
                
                logger.info(f"[LLM RESPONSE] Raw response: {llm_response[:200]}...")
                
                # Parse response to extract model and price
                parsed = self._parse_llm_response(llm_response)
                
                response = ChatResponse(
                    message=request.message,
                    model=parsed.get('model', ''),
                    price=parsed.get('price', 0.0)
                )
                
                # Cache the response
                self.cache.set(
                    cache_key,
                    response.model_dump(),
                    ttl=self.cache_ttl
                )
                
                logger.info(f"[RESPONSE] Model: {response.model}, Price: {response.price}, Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                return response
                
            except Exception as e:
                error_str = str(e).lower()
                logger.error(f"[ERROR] Attempt {attempt + 1}/{max_retries}: {error_str}")
                
                # Check if this is a network error
                is_network_error = (
                    'network' in error_str or 
                    'connection' in error_str or 
                    'timeout' in error_str or
                    'refused' in error_str
                )
                
                # If network error, check connectivity and return fallback
                if is_network_error and not self._check_network():
                    fallback_response = self._create_fallback_response(f"Network error: {str(e)}")
                    logger.warning(f"[NETWORK ERROR] Returning fallback response: {fallback_response.model_dump()}")
                    # Cache the fallback response with shorter TTL
                    self.cache.set(
                        cache_key,
                        fallback_response.model_dump(),
                        ttl=60  # 1 minute for fallback
                    )
                    return fallback_response
                
                # If not last attempt, wait before retry
                if attempt < max_retries - 1:
                    wait_time = wait_times[attempt] if attempt < len(wait_times) else 5
                    logger.warning(f"[RETRY] Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    # Last attempt failed, raise exception
                    logger.error(f"[FAILED] LLM processing error after {max_retries} attempts: {str(e)}")
                    raise Exception(f"LLM processing error after {max_retries} attempts: {str(e)}")


# Default instance for convenience
chat_service = ChatService()
