from openai import OpenAI
from typing import Optional
from logger import logger
from .models import ModelConfig, MODELS

class OpenRouter:
    def __init__(self, api_key: str, site_url: Optional[str] = None, site_name: Optional[str] = None):
        """
        Initialize OpenRouter client.
        
        Args:
            api_key (str): Your OpenRouter API key
            site_url (Optional[str]): Your site URL for rankings on openrouter.ai
            site_name (Optional[str]): Your site name for rankings on openrouter.ai
        """
        logger.info("Initializing OpenRouter client")
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.extra_headers = {}
        if site_url:
            self.extra_headers["HTTP-Referer"] = site_url
        if site_name:
            self.extra_headers["X-Title"] = site_name
        logger.debug(f"Extra headers configured: {self.extra_headers}")

    def get_completion(self, prompt: str, model_config: ModelConfig = MODELS.GEMINI_FLASH) -> str:
        """
        Get completion from OpenRouter API.
        
        Args:
            prompt (str): The prompt to send to the model
            model_config (ModelConfig): Configuration for the model to use (default: GEMINI_FLASH)
            
        Returns:
            str: The model's response
        """        
        logger.info(f"Requesting completion from model: {model_config.name}")
        logger.debug(f"Prompt: {prompt}")
        
        try:
            completion = self.client.chat.completions.create(
                extra_headers=self.extra_headers,
                model=model_config.name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=model_config.max_tokens,
                temperature=model_config.temperature
            )
            response = completion.choices[0].message.content
            logger.debug(f"Received response: {response}")
            return response
        except Exception as e:
            logger.error(f"Error getting completion: {str(e)}", exc_info=True)
            raise 