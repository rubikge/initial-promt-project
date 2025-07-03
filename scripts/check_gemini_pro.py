"""
Minimal module for testing OpenRouter Gemini Pro text generation.
"""

import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from llms.openrouter.openrouter_client import OpenRouter
from llms.openrouter.models import MODELS

# Load environment variables
load_dotenv()

# Configuration constants
TEST_PROMPT = """Write a short story about a robot learning to paint. Make it creative and engaging, around 200-300 words."""
TEST_MODEL = MODELS.GEMINI_PRO
OUTPUT_FILENAME = "openrouter_gemini_pro_response.md"


def get_unique_filename(output_dir: Path, filename: str) -> Path:
    """Generate a unique filename by adding underscore prefix if file exists."""
    output_path = output_dir / filename
    
    # If file doesn't exist, return original path
    if not output_path.exists():
        return output_path
    
    # If file exists, keep adding underscores until we find a unique name
    name, ext = os.path.splitext(filename)
    counter = 1
    
    while True:
        new_filename = f"{'_' * counter}{name}{ext}"
        new_path = output_dir / new_filename
        
        if not new_path.exists():
            return new_path
        
        counter += 1


def test_gemini_pro_text_generation():
    """Test text generation with OpenRouter Gemini Pro model."""
    
    # Get API token from environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Please set OPENROUTER_API_KEY environment variable")
        return
    
    # Initialize client
    client = OpenRouter(api_key)
    
    # Create output directory with current date
    current_date = datetime.now().strftime("%Y_%m_%d")
    output_dir = Path("output") / current_date
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=== Testing OpenRouter Gemini Pro Text Generation ===")
    print(f"Prompt: {TEST_PROMPT}")
    print(f"Model: {TEST_MODEL.name}")
    print(f"Max tokens: {TEST_MODEL.max_tokens}")
    print(f"Temperature: {TEST_MODEL.temperature}")
    
    try:
        print("Generating text response...")
        
        # Generate text using specified model
        response = client.get_completion(TEST_PROMPT, model_config=TEST_MODEL)
        
        print(f"Response received: {type(response)}")
        
        # Handle the response
        if response and hasattr(response, 'content'):
            content = response.content
            token_usage = response.token_usage
            
            print(f"Response content length: {len(content)} characters")
            print(f"Token usage - Prompt: {token_usage.prompt_tokens}, Completion: {token_usage.completion_tokens}, Total: {token_usage.total_tokens}")
            print(f"Cost: ${token_usage.cost_usd:.6f}")
            
            # Save to output directory with unique filename
            output_path = get_unique_filename(output_dir, OUTPUT_FILENAME)
            
            # Create markdown content
            markdown_content = f"""# OpenRouter Gemini Pro Test

## Test Configuration
- **Model**: {TEST_MODEL.name}
- **Max Tokens**: {TEST_MODEL.max_tokens}
- **Temperature**: {TEST_MODEL.temperature}
- **Test Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Input Prompt
```
{TEST_PROMPT}
```

## Model Response
```
{content}
```

## Token Usage
- **Prompt Tokens**: {token_usage.prompt_tokens}
- **Completion Tokens**: {token_usage.completion_tokens}
- **Total Tokens**: {token_usage.total_tokens}
- **Cost**: ${token_usage.cost_usd:.6f}
"""
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            
            print(f"✅ Response successfully saved to: {output_path}")
            print(f"File size: {len(markdown_content)} characters")
        else:
            print("❌ No valid response received")
            
    except Exception as e:
        print(f"❌ Error during text generation: {str(e)}")


if __name__ == "__main__":
    test_gemini_pro_text_generation() 