from openai import OpenAI
from typing import Optional
import time
import json
from .models import ModelConfig, MODELS, CompletionResponse, TokenUsage


class OpenRouter:
    def __init__(
        self,
        api_key: str,
        site_url: Optional[str] = None,
        site_name: Optional[str] = None,
    ):
        """
        Initialize OpenRouter client.

        Args:
            api_key (str): Your OpenRouter API key
            site_url (Optional[str]): Your site URL for rankings on openrouter.ai
            site_name (Optional[str]): Your site name for rankings on openrouter.ai
        """
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.extra_headers = {}
        if site_url:
            self.extra_headers["HTTP-Referer"] = site_url
        if site_name:
            self.extra_headers["X-Title"] = site_name

    def calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        input_token_cost_per_million: float = 1.25,
        output_token_cost_per_million: float = 10.0,
    ) -> float:
        """
        Calculate the cost of a request based on token usage.

        Args:
            prompt_tokens (int): Number of input tokens
            completion_tokens (int): Number of output tokens
            input_token_cost_per_million (float): Cost per million input tokens in USD (default: 1.25)
            output_token_cost_per_million (float): Cost per million output tokens in USD (default: 10.0)

        Returns:
            float: Total cost in USD
        """
        input_cost = (prompt_tokens / 1_000_000) * input_token_cost_per_million
        output_cost = (completion_tokens / 1_000_000) * output_token_cost_per_million
        return input_cost + output_cost

    def get_completion(
        self,
        prompt: str,
        model_config: ModelConfig = MODELS.GEMINI_FLASH,
        max_retries: int = 3,
        json_output: bool = False,
    ) -> CompletionResponse:
        """
        Get completion from OpenRouter API.

        Args:
            prompt (str): The prompt to send to the model
            model_config (ModelConfig): The model configuration to use (default: MODELS.GEMINI_FLASH)
            max_retries (int): Maximum number of retry attempts
            json_output (bool): Whether to request JSON output format and parse it (default: False)

        Returns:
            CompletionResponse: The model's response with content and token usage information
        """
        for attempt in range(max_retries):
            try:
                # Prepare request parameters
                request_params = {
                    "extra_headers": self.extra_headers,
                    "model": model_config.name,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": model_config.max_tokens,
                    "temperature": model_config.temperature,
                }

                # Add response_format if JSON output is requested
                if json_output:
                    request_params["response_format"] = {"type": "json_object"}

                completion = self.client.chat.completions.create(**request_params)

                # Get token usage if available, otherwise return zeros
                token_usage = TokenUsage()

                if hasattr(completion, "usage") and completion.usage is not None:
                    token_usage = TokenUsage(
                        prompt_tokens=getattr(completion.usage, "prompt_tokens", 0),
                        completion_tokens=getattr(
                            completion.usage, "completion_tokens", 0
                        ),
                        total_tokens=getattr(completion.usage, "total_tokens", 0),
                    )

                # Calculate cost using model_config parameters
                input_cost_usd = (
                    token_usage.prompt_tokens / 1_000_000
                ) * model_config.input_token_cost_per_million
                output_cost_usd = (
                    token_usage.completion_tokens / 1_000_000
                ) * model_config.output_token_cost_per_million
                total_cost = input_cost_usd + output_cost_usd

                token_usage.cost_usd = total_cost

                response_content = completion.choices[0].message.content

                # Parse JSON if requested
                if json_output:
                    try:
                        parsed_content = json.loads(response_content)
                        return CompletionResponse(
                            content=parsed_content,
                            token_usage=token_usage,
                        )
                    except json.JSONDecodeError as e:
                        raise Exception(
                            f"Failed to parse JSON response: {str(e)}. Response: {response_content}"
                        )
                else:
                    return CompletionResponse(
                        content=response_content, token_usage=token_usage
                    )

            except Exception as e:
                print(f"Attempt {attempt + 1} failed with error: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)  # Exponential backoff
                else:
                    raise Exception(
                        f"Failed after {max_retries} attempts. Last error: {str(e)}"
                    )
