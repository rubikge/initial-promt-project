from pydantic import BaseModel, Field
from typing import Union, Dict, Any


class TokenUsage(BaseModel):
    """Token usage information"""

    prompt_tokens: int = Field(default=0, description="Number of input tokens")
    completion_tokens: int = Field(default=0, description="Number of output tokens")
    total_tokens: int = Field(default=0, description="Total number of tokens")
    cost_usd: float = Field(default=0.0, description="Cost in USD")


class CompletionResponse(BaseModel):
    """Response from the completion API"""

    content: Union[str, Dict[str, Any]] = Field(
        description="The model's response content"
    )
    token_usage: TokenUsage = Field(description="Token usage information")


class ModelConfig(BaseModel):
    """Configuration for a model"""

    name: str = Field(default="google/gemini-2.5-flash")
    max_tokens: int = Field(default=4096)
    temperature: float = Field(default=1.0)
    input_token_cost_per_million: float = Field(default=0.3)
    output_token_cost_per_million: float = Field(default=2.5)


class Models:
    """Class for accessing model configurations"""

    # GPT_3_5_TURBO = ModelConfig(name="openai/gpt-3.5-turbo")
    # GPT_4 = ModelConfig(name="openai/gpt-4", max_tokens=8192)
    # CLAUDE_3_OPUS = ModelConfig(
    #     name="anthropic/claude-3-opus-20240229", max_tokens=200000
    # )
    GEMINI_PRO = ModelConfig(name="google/gemini-2.5-pro", max_tokens=32768)
    GEMINI_FLASH = ModelConfig(name="google/gemini-2.5-flash", max_tokens=32768)


# Create a single instance of Models
MODELS = Models()
