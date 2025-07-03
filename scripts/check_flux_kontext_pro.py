"""
Minimal module for testing Replicate Kontext Max image generation.
"""

import os
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from llms.replicate.replicate_client import ReplicateClient
from llms.replicate.models import MODELS

# Load environment variables
load_dotenv()

# Configuration constants
TEST_PROMPT = "Remove the piece of clothing with logo and caption above the shoulder"
TEST_MODEL = MODELS.FLUX_KONTEXT_MAX
CONTEXT_IMAGE_FILENAME = "NORS186.jpg"
OUTPUT_FILENAME = "flux_kontext_max.jpg"


def upload_image_to_temp_url(image_path: Path) -> str:
    """Upload image to a temporary URL service and return the URL."""
    # For now, we'll use a simple approach - create a data URL
    # This is a temporary solution until we implement proper file upload
    import base64
    import mimetypes
    
    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(str(image_path))
    if not mime_type:
        mime_type = "image/jpeg"  # Default to JPEG
    
    # Read and encode the image
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode('utf-8')
    
    # Create data URL
    data_url = f"data:{mime_type};base64,{image_data}"
    return data_url


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


def test_kontext_image_generation():
    """Test image generation with Replicate Kontext Max model."""
    
    # Get API token from environment
    api_token = os.getenv("REPLICATE_API_TOKEN")
    if not api_token:
        print("Please set REPLICATE_API_TOKEN environment variable")
        return
    
    # Initialize client
    client = ReplicateClient(api_token)
    
    # Check if context image exists
    context_image_path = Path("input") / CONTEXT_IMAGE_FILENAME
    if not context_image_path.exists():
        print(f"❌ Context image not found: {context_image_path}")
        return
    
    # Create output directory with current date
    current_date = datetime.now().strftime("%Y_%m_%d")
    output_dir = Path("output") / current_date
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=== Testing Replicate Kontext Max Image Generation ===")
    print(f"Prompt: {TEST_PROMPT}")
    print(f"Model: {TEST_MODEL.name}")
    print(f"Context image: {context_image_path}")
    print("Encoding context image...")
    
    try:
        # Upload context image to get URL
        context_image_url = upload_image_to_temp_url(context_image_path)
        print(f"Context image uploaded, URL length: {len(context_image_url)} characters")
        
        # Create model configuration with context image
        model_config = TEST_MODEL.model_copy(update={
            "input_image": context_image_url
        })
        
        print("Generating image with context...")
        
        # Generate image using specified model
        response = client.get_completion(TEST_PROMPT, model_config=model_config)
        
        print(f"Response received: {type(response)}")
        
        # Handle the response (should be an image URL)
        if response:
            image_url = response
            
            print(f"Image URL: {image_url}")
            
            # Download the image
            print("Downloading image...")
            img_response = requests.get(image_url, timeout=30)
            
            if img_response.status_code == 200:
                # Save to output directory with unique filename
                output_path = get_unique_filename(output_dir, OUTPUT_FILENAME)
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
    test_kontext_image_generation() 