from pydantic import BaseModel, Field

class ModelConfig(BaseModel):
    """Configuration for a model"""
    name: str = Field(default="google/gemini-2.0-flash-001")
    max_tokens: int = Field(default=4096)
    temperature: float = Field(default=0.7)

class Models:
    """Class for accessing model configurations"""
    GPT_3_5_TURBO = ModelConfig(
        name="openai/gpt-3.5-turbo"
    )
    GPT_4 = ModelConfig(
        name="openai/gpt-4",
        max_tokens=8192
    )
    CLAUDE_3_OPUS = ModelConfig(
        name="anthropic/claude-3-opus-20240229",
        max_tokens=200000
    )
    GEMINI_PRO = ModelConfig(
        name="google/gemini-pro",
        max_tokens=32768
    )
    GEMINI_FLASH = ModelConfig()

# Create a single instance of Models
MODELS = Models()