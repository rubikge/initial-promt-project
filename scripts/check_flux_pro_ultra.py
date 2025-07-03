"""
Minimal module for testing Replicate image generation.
"""

import os
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from llms.replicate import ReplicateClient, MODELS

# Load environment variables
load_dotenv()

# Configuration constants
TEST_PROMPT = "A beautiful portrait of a wise ancient philosopher in a library, detailed, high quality"
TEST_MODEL = MODELS.FLUX_1_1_PRO_ULTRA
OUTPUT_FILENAME = "flux_pro_ultra.jpg"


def test_image_generation():
    """Test image generation with Replicate Flux model."""
    
    # Get API token from environment
    api_token = os.getenv("REPLICATE_API_TOKEN")
    if not api_token:
        print("Please set REPLICATE_API_TOKEN environment variable")
        return
    
    # Initialize client
    client = ReplicateClient(api_token)
    
    # Create output directory with current date
    current_date = datetime.now().strftime("%Y_%m_%d")
    output_dir = Path("output") / current_date
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=== Testing Replicate Image Generation ===")
    print(f"Prompt: {TEST_PROMPT}")
    print(f"Model: {TEST_MODEL.name}")
    print("Generating image...")
    
    try:
        # Generate image using specified model
        response = client.get_completion(TEST_PROMPT, model_config=TEST_MODEL)
        
        print(f"Response received: {type(response.content)}")
        print(f"Token usage: {response.token_usage}")
        print(f"Cost: ${response.token_usage.cost_usd:.6f}")
        
        # Handle the response (should be an image URL)
        if response.content:
            image_url = response.content[0] if isinstance(response.content, list) else response.content
            
            print(f"Image URL: {image_url}")
            
            # Download the image
            print("Downloading image...")
            img_response = requests.get(image_url, timeout=30)
            
            if img_response.status_code == 200:
                # Save to output directory
                output_path = output_dir / OUTPUT_FILENAME
                with open(output_path, "wb") as f:
                    f.write(img_response.content)
                
                print(f"✅ Image successfully saved to: {output_path}")
                print(f"File size: {len(img_response.content)} bytes")
            else:
                print(f"❌ Failed to download image: HTTP {img_response.status_code}")
        else:
            print("❌ No image URL received in response")
            
    except Exception as e:
        print(f"❌ Error during image generation: {str(e)}")


if __name__ == "__main__":
    test_image_generation() 