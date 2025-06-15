import os
import pytest
from dotenv import load_dotenv
from openrouter.client import OpenRouter
from openrouter.models import MODELS

# Load environment variables from .env file
load_dotenv()

@pytest.fixture
def openrouter_client():
    """Fixture to create OpenRouter client instance."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not found in environment variables")
    return OpenRouter(api_key=api_key)

def test_get_completion(openrouter_client):
    """Test that get_completion returns a string response."""
    prompt = "Say hello in one word"
    response = openrouter_client.get_completion(prompt)
    
    assert isinstance(response, str)
    assert len(response) > 0

def test_get_completion_with_custom_model(openrouter_client):
    """Test that get_completion works with a custom model."""
    prompt = "What is 2+2?"
    response = openrouter_client.get_completion(
        prompt=prompt,
        model_config=MODELS.GPT_3_5_TURBO
    )
    
    assert isinstance(response, str)
    assert len(response) > 0 