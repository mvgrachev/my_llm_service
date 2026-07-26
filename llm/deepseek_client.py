"""DeepSeek client for Yandex Cloud."""
import os
import openai
import threading
import queue
import logging
from typing import Optional

logger = logging.getLogger('llm_service.deepseek')


# Default prompt for KASCO calculation
DEFAULT_PROMPT = (
    "Рассчитай стоимость КАСКО в зависимости от марки автомобиля и количества лошидиных сил. "
    "Укажи базовую стоимость и учет коэффициентов. "
    "\n\nФормат ответа: JSON. "
    "Обязательные поля: model (марка автомобиля), price (стоимость в рублях). "
    "Без вступления, без лишних полей. "
    "Пример: {\"model\": \"Toyota\", \"price\": 50000}"
)


def with_timeout(timeout: int = 30):
    """
    Decorator for adding timeout to LLM calls.
    
    Args:
        timeout: Timeout in seconds
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            result_queue = queue.Queue()
            exception_queue = queue.Queue()
            
            def target():
                try:
                    result = func(*args, **kwargs)
                    result_queue.put(result)
                except Exception as e:
                    exception_queue.put(e)
            
            thread = threading.Thread(target=target, daemon=True)
            thread.start()
            thread.join(timeout=timeout)
            
            if thread.is_alive():
                raise TimeoutError(f"LLM call timed out after {timeout} seconds")
            
            if not exception_queue.empty():
                raise exception_queue.get()
            
            return result_queue.get()
        
        return wrapper
    return decorator


class DeepSeekClient:
    """Client for DeepSeek model on Yandex Cloud."""
    
    def __init__(
        self,
        folder_id: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        prompt: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize DeepSeek client.
        
        Args:
            folder_id: Yandex Cloud folder ID (from env YANDEX_CLOUD_FOLDER)
            api_key: Yandex Cloud API key (from env YANDEX_CLOUD_API_KEY)
            model: Model name (from env YANDEX_CLOUD_MODEL)
            prompt: System prompt for KASCO calculation (from env PROMPT or DEFAULT_PROMPT)
            timeout: Request timeout in seconds
        """
        self.folder_id = folder_id or os.getenv("YANDEX_CLOUD_FOLDER")
        self.api_key = api_key or os.getenv("YANDEX_CLOUD_API_KEY")
        self.model = model or os.getenv("YANDEX_CLOUD_MODEL", "deepseek-v4-flash/latest")
        self.prompt = prompt or os.getenv("PROMPT", DEFAULT_PROMPT)
        self.timeout = timeout
        
        if not self.folder_id:
            raise ValueError("YANDEX_CLOUD_FOLDER environment variable is required")
        if not self.api_key:
            raise ValueError("YANDEX_CLOUD_API_KEY environment variable is required")
        
        openai.api_key = self.api_key
        openai.api_base = "https://ai.api.cloud.yandex.net/v1"
    
    @with_timeout(timeout=30)
    def generate(
        self,
        input_text: str,
        temperature: float = 0.3,
        instructions: Optional[str] = None,
        max_output_tokens: int = 1500
    ) -> str:
        """
        Generate response from DeepSeek model with timeout.
        
        Args:
            input_text: Input text for the model
            temperature: Temperature for generation
            instructions: System instructions (uses self.prompt if None)
            max_output_tokens: Maximum output tokens
            
        Returns:
            Generated text response
            
        Raises:
            TimeoutError: If request takes longer than timeout
            Exception: If LLM call fails
        """
        prompt_text = instructions if instructions is not None else self.prompt
        
        logger.info(f"[DEEPSEEK] Generating response for input: {input_text[:100]}...")
        logger.info(f"[DEEPSEEK] Prompt: {prompt_text[:200]}...")
        
        try:
            response = openai.ChatCompletion.create(
                model=f"gpt://{self.folder_id}/{self.model}",
                temperature=temperature,
                messages=[
                    {"role": "system", "content": prompt_text},
                    {"role": "user", "content": input_text}
                ],
                max_tokens=max_output_tokens
            )
            result = response.choices[0].message.content
            logger.info(f"[DEEPSEEK] Response received: {result[:200]}...")
            return result
        except Exception as e:
            logger.error(f"[DEEPSEEK] Error during generation: {str(e)}")
            raise Exception(f"LLM generation error: {str(e)}")


# Default instance for convenience
deepseek_client = DeepSeekClient()
