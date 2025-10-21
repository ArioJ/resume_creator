import os
import logging
from openai import OpenAI
from dotenv import load_dotenv
import tiktoken
from typing import Optional

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class OpenAIClient:
    """Wrapper for OpenAI API with retry logic and error handling"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # Initialize OpenAI client with explicit parameters only
        # This avoids issues with proxy settings or unexpected kwargs
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                timeout=60.0,
                max_retries=2
            )
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            # Fallback to minimal initialization
            self.client = OpenAI(api_key=self.api_key)
        
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "4000"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.3"))
        
        logger.info(f"OpenAI client initialized with model: {self.model}")
    
    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """Count tokens in text for the specified model"""
        try:
            encoding = tiktoken.encoding_for_model(model or self.model)
            return len(encoding.encode(text))
        except Exception as e:
            logger.warning(f"Token counting failed: {e}, using approximation")
            return len(text.split()) * 1.3  # Rough approximation
    
    def chat_completion(self, messages: list, temperature: Optional[float] = None, 
                       max_tokens: Optional[int] = None, response_format: Optional[dict] = None) -> str:
        """
        Call OpenAI chat completion API
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            response_format: Optional response format (e.g., {"type": "json_object"})
        
        Returns:
            Response content as string
        """
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens,
            }
            
            if response_format:
                params["response_format"] = response_format
            
            response = self.client.chat.completions.create(**params)
            content = response.choices[0].message.content
            
            # Log token usage
            usage = response.usage
            logger.info(f"API call completed. Tokens used - Prompt: {usage.prompt_tokens}, "
                       f"Completion: {usage.completion_tokens}, Total: {usage.total_tokens}")
            
            return content
        
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    def structured_completion(self, system_prompt: str, user_prompt: str, 
                             temperature: Optional[float] = None) -> str:
        """
        Helper for structured completions with system and user prompts
        
        Args:
            system_prompt: System message
            user_prompt: User message
            temperature: Optional temperature override
        
        Returns:
            Response content
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return self.chat_completion(messages, temperature=temperature)


# Global client instance
_client_instance = None


def get_openai_client() -> OpenAIClient:
    """Get or create the global OpenAI client instance"""
    global _client_instance
    if _client_instance is None:
        _client_instance = OpenAIClient()
    return _client_instance

