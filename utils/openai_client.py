import os
from openai import OpenAI
from dotenv import load_dotenv
import tiktoken
from typing import Optional
import httpx
import time

# Import centralized logging
from utils.logging_config import get_logger, log_openai_call

logger = get_logger(__name__)

# Load environment variables
load_dotenv()
logger.info("Loading environment variables for OpenAI client")


class OpenAIClient:
    """Wrapper for OpenAI API with retry logic and error handling"""
    
    def __init__(self):
        logger.info("=" * 80)
        logger.info("🤖 INITIALIZING OPENAI CLIENT")
        logger.info("=" * 80)
        
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # Log API key presence (not the actual key)
        logger.info(f"✓ API key loaded (length: {len(self.api_key)} chars)")
        
        # Create custom httpx client with proxies disabled
        # This prevents proxy-related errors
        try:
            logger.debug("Creating custom HTTP client with proxies disabled")
            custom_http_client = httpx.Client(
                timeout=60.0,
                trust_env=False  # Disable reading proxy from environment
            )
            
            self.client = OpenAI(
                api_key=self.api_key,
                http_client=custom_http_client,
                max_retries=2
            )
            logger.info("✓ OpenAI client initialized with custom HTTP client (proxies disabled)")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client with custom HTTP client: {e}", exc_info=True)
            # Last resort fallback - try without any custom settings
            try:
                logger.warning("Attempting fallback initialization with default settings")
                self.client = OpenAI(api_key=self.api_key)
                logger.info("✓ OpenAI client initialized with default settings")
            except Exception as e2:
                logger.error(f"Failed to initialize OpenAI client: {e2}", exc_info=True)
                raise
        
        # Load configuration
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "4000"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.0"))
        
        logger.info(f"✓ Model: {self.model}")
        logger.info(f"✓ Max tokens: {self.max_tokens}")
        logger.info(f"✓ Temperature: {self.temperature}")
        logger.info("=" * 80)
    
    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """Count tokens in text for the specified model"""
        try:
            encoding = tiktoken.encoding_for_model(model or self.model)
            return len(encoding.encode(text))
        except Exception as e:
            logger.warning(f"Token counting failed: {e}, using approximation")
            return len(text.split()) * 1.3  # Rough approximation
    
    def chat_completion(self, messages: list, temperature: Optional[float] = None, 
                       max_tokens: Optional[int] = None, response_format: Optional[dict] = None,
                       operation: str = "chat_completion") -> str:
        """
        Call OpenAI chat completion API
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            response_format: Optional response format (e.g., {"type": "json_object"})
            operation: Description of the operation for logging
        
        Returns:
            Response content as string
        """
        start_time = time.time()
        
        # Extract prompts for logging
        system_prompt = next((m['content'] for m in messages if m['role'] == 'system'), None)
        user_prompt = next((m['content'] for m in messages if m['role'] == 'user'), None)
        
        logger.info("=" * 80)
        logger.info(f"🤖 OPENAI API CALL - {operation}")
        logger.info("=" * 80)
        logger.info(f"Model: {self.model}")
        logger.info(f"Temperature: {temperature or self.temperature}")
        logger.info(f"Max tokens: {max_tokens or self.max_tokens}")
        logger.info(f"Response format: {response_format}")
        logger.info(f"Number of messages: {len(messages)}")
        
        # Log message details
        for i, msg in enumerate(messages, 1):
            role = msg.get('role', 'unknown')
            content_preview = msg.get('content', '')[:200]
            logger.debug(f"Message {i} [{role}]: {content_preview}...")
        
        # Log full prompts
        if system_prompt:
            logger.debug(f"System Prompt (length: {len(system_prompt)} chars):\n{system_prompt[:500]}...")
        if user_prompt:
            logger.debug(f"User Prompt (length: {len(user_prompt)} chars):\n{user_prompt[:500]}...")
        
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens,
            }
            
            if response_format:
                params["response_format"] = response_format
            
            logger.debug("Sending request to OpenAI...")
            response = self.client.chat.completions.create(**params)
            content = response.choices[0].message.content
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log token usage
            usage = response.usage
            logger.info(f"✓ API call completed successfully")
            logger.info(f"Tokens - Prompt: {usage.prompt_tokens}, "
                       f"Completion: {usage.completion_tokens}, Total: {usage.total_tokens}")
            logger.info(f"Duration: {duration_ms:.2f}ms")
            logger.debug(f"Response preview (first 500 chars):\n{content[:500]}...")
            logger.info("=" * 80)
            
            # Log to dedicated OpenAI log file
            log_openai_call(
                operation=operation,
                prompt=f"System: {system_prompt[:200] if system_prompt else 'None'}\nUser: {user_prompt[:200] if user_prompt else 'None'}",
                response=content[:500] if content else None,
                model=self.model,
                tokens_used=usage.total_tokens,
                duration_ms=round(duration_ms, 2)
            )
            
            return content
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error("=" * 80)
            logger.error(f"❌ OPENAI API CALL FAILED - {operation}")
            logger.error(f"Error: {str(e)}")
            logger.error(f"Duration before failure: {duration_ms:.2f}ms")
            logger.error("=" * 80)
            logger.error(f"Full error details:", exc_info=True)
            
            # Log error to dedicated OpenAI log file
            log_openai_call(
                operation=operation,
                prompt=f"System: {system_prompt[:200] if system_prompt else 'None'}\nUser: {user_prompt[:200] if user_prompt else 'None'}",
                model=self.model,
                duration_ms=round(duration_ms, 2),
                error=str(e)
            )
            
            raise
    
    def structured_completion(self, system_prompt: str, user_prompt: str, 
                             temperature: Optional[float] = None, operation: str = "structured_completion") -> str:
        """
        Helper for structured completions with system and user prompts
        
        Args:
            system_prompt: System message
            user_prompt: User message
            temperature: Optional temperature override
            operation: Description of the operation for logging
        
        Returns:
            Response content
        """
        logger.debug(f"Creating structured completion for operation: {operation}")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return self.chat_completion(messages, temperature=temperature, operation=operation)


# Global client instance
_client_instance = None


def get_openai_client() -> OpenAIClient:
    """Get or create the global OpenAI client instance"""
    global _client_instance
    if _client_instance is None:
        logger.info("Creating new OpenAI client instance (singleton)")
        _client_instance = OpenAIClient()
    else:
        logger.debug("Returning existing OpenAI client instance")
    return _client_instance

