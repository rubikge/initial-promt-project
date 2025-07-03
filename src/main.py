#!/usr/bin/env python3

import os
import csv
import json
import random
import logging
import argparse
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional
import replicate
import requests
from dataclasses import dataclass
import time
from openai import OpenAI
import concurrent.futures
from threading import Lock
from google import genai
from google.genai import types
from dotenv import load_dotenv


# Configure logging with thread safety
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(threadName)s - %(levelname)s - %(message)s",
)

# Add a lock for thread-safe logging
logging_lock = Lock()


def thread_safe_logging(level, message):
    """Thread-safe logging function."""
    with logging_lock:
        logging.log(level, message)


@dataclass
class NordicSample:
    """Represents a Nordic DNA sample with all necessary information for portrait generation."""

    sample_id: str  # Sample ID
    tier_1: str  # Tier 1 Era Label (e.g., Mesolithic)
    tier_2: str  # Tier 2 Region/Route (e.g., Steppe-Frontier & LNBA Ancestors)
    gender: str  # Sex
    years_range: str  # Full Date (radiocarbon age or archaeological context)
    location: str  # Locality
    region: str  # Political Entity
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    publication: Optional[str] = None
    marketing_name: Optional[str] = None
    description: Optional[str] = None


class PortraitGenerator:
    def __init__(
        self, output_dir: str = "out", num_threads: int = 10, use_gemini: bool = False
    ):
        """Initialize the portrait generator with output directory."""
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.num_threads = num_threads
        self.use_gemini = use_gemini

        if use_gemini:
            # Initialize Gemini client
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            if not gemini_api_key:
                raise ValueError(
                    "GEMINI_API_KEY environment variable is required for Gemini generation"
                )
            self.gemini_client = genai.Client(api_key=gemini_api_key)
        else:
            # Initialize OpenAI client for OpenRouter
            openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
            if not openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY environment variable is required")

            self.openai_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_api_key,
                default_headers={
                    "HTTP-Referer": "https://github.com/yourusername/your-repo",
                    "X-Title": "Ancient DNA Portrait Generator",
                },
            )

            # Ensure Replicate API key is available
            if not os.getenv("REPLICATE_API_TOKEN"):
                raise ValueError("REPLICATE_API_TOKEN environment variable is required")

        # Add rate limiting
        self.request_lock = Lock()
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum time between requests in seconds

    def rate_limit(self):
        """Implement rate limiting for API requests."""
        with self.request_lock:
            current_time = time.time()
            time_since_last_request = current_time - self.last_request_time
            if time_since_last_request < self.min_request_interval:
                time.sleep(self.min_request_interval - time_since_last_request)
            self.last_request_time = time.time()

    def load_samples(
        self, csv_path: str, sample_size: Optional[int] = None
    ) -> List[NordicSample]:
        """Load and optionally sample random entries from the CSV file."""
        samples = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)  # Get header row

            # Find latitude and longitude column indices if they exist
            try:
                lat_idx = header.index("latitude")
                lon_idx = header.index("longitude")
                has_coordinates = True
            except ValueError:
                has_coordinates = False

            for row in reader:
                sample = NordicSample(
                    sample_id=row[0],
                    tier_1=row[1],
                    tier_2=row[2],
                    gender=row[3],
                    years_range=row[4],
                    location=row[5],
                    region=row[6],
                    latitude=float(row[lat_idx]) if has_coordinates else None,
                    longitude=float(row[lon_idx]) if has_coordinates else None,
                    publication=row[7],
                    marketing_name=row[8],
                    description=row[9],
                )
                samples.append(sample)

        if sample_size and sample_size < len(samples):
            return random.sample(samples, sample_size)
        return samples

    def get_geographical_context(self, sample: NordicSample) -> dict:
        """Get geographical context using deepseek-chat via OpenRouter API"""
        try:
            # If we have coordinates, use them
            if sample.latitude and sample.longitude:
                coordinates_text = (
                    f"latitude: {sample.latitude}, longitude: {sample.longitude}"
                )
            else:
                coordinates_text = (
                    f"location: {sample.location}, {sample.region}, {sample.region}"
                )

            prompt = f"""You are a historical geography expert. I need you to describe the geographical and environmental context of an ancient location.

Location: {coordinates_text}
Time Period: {sample.years_range}
Culture: {sample.tier_2}

Please provide a detailed description in JSON format with the following structure:
{{
    "description": "A detailed description of the overall landscape and its historical significance",
    "features": "List of specific visual elements that would appear in a portrait background",
    "atmosphere": "Details about lighting, weather, and atmospheric conditions",
    "architecture": "Description of period-specific buildings and structures"
}}

Consider:
1. The natural landscape and terrain features that existed during {sample.years_range}
2. The climate and weather patterns typical for that historical period
3. The vegetation and natural resources available
4. How {sample.tier_2} people would have interacted with and modified this landscape
5. What architectural or settlement features would be visible
6. The quality of light and atmospheric conditions specific to this region

Focus on creating historically accurate, painterly descriptions suitable for a Renaissance-style portrait background.
Emphasize elements that would create depth and atmosphere in the image.

Respond ONLY with the JSON object, no additional text."""

            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/yourusername/your-repo",
                    "X-Title": "Ancient DNA Portrait Generator",
                },
                json={
                    "model": "google/gemini-2.0-flash-001",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 300,
                    "temperature": 0.7,
                },
            )

            if response.status_code != 200:
                raise Exception(
                    f"API request failed with status {response.status_code}: {response.text}"
                )

            # Parse the JSON response
            response_data = response.json()
            if not response_data.get("choices") or not response_data["choices"][0].get(
                "message"
            ):
                raise Exception("Invalid response format from API")

            content = response_data["choices"][0]["message"]["content"]

            # Try to extract JSON from the response content
            try:
                # First, try direct JSON parsing
                context_data = json.loads(content)
            except json.JSONDecodeError:
                # If that fails, try to find JSON-like structure in the text
                import re

                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    try:
                        context_data = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        raise Exception("Could not parse JSON from response")
                else:
                    raise Exception("No JSON structure found in response")

            # Return standardized format with enhanced defaults
            return {
                "region": f"{sample.tier_2}_{sample.location}_{sample.years_range}",
                "description": context_data.get(
                    "description",
                    f"Authentic {sample.tier_2} landscape from {sample.years_range}, showing the raw, untamed environment of ancient {sample.region}",
                ),
                "features": context_data.get(
                    "features",
                    f"Traditional {sample.tier_2} settlements, ancient pathways, and natural formations typical of {sample.region}",
                ),
                "atmosphere": context_data.get(
                    "atmosphere",
                    "Natural lighting with atmospheric perspective, creating depth and historical ambiance",
                ),
                "architecture": context_data.get(
                    "architecture",
                    f"Period-accurate {sample.tier_2} structures and settlements from {sample.years_range}",
                ),
            }

        except Exception as e:
            logging.error(
                f"Error getting geographical context for {sample.sample_id}: {str(e)}"
            )
            # Enhanced fallback context with more detail
            return {
                "region": f"{sample.tier_2}_{sample.location}",
                "description": f"Rugged {sample.tier_2} landscape showing the untamed wilderness of ancient {sample.region}, with natural formations and traditional settlements visible in the distance",
                "features": f"Ancient {sample.tier_2} pathways winding through the terrain, traditional settlements nestled in the landscape, and period-appropriate agricultural or cultural sites",
                "atmosphere": "Dramatic natural lighting filtering through the atmosphere, creating depth and historical authenticity",
                "architecture": f"Historically accurate {sample.years_range} {sample.tier_2} structures, showing traditional building methods and materials",
            }

    def get_gender_terms(self, gender: Optional[str]) -> Dict[str, str]:
        """Get gender-specific terms for portrait generation."""
        gender_terms = {
            "male": {
                "title": "man",
                "features": "masculine features, strong jawline, male bone structure",
                "clothing": "male garments, masculine attire",
                "posture": "commanding presence, masculine bearing",
                "descriptors": "strong facial features, defined bone structure",
            },
            "female": {
                "title": "woman",
                "features": "feminine features, graceful bone structure, female characteristics",
                "clothing": "female garments, feminine attire",
                "posture": "graceful presence, feminine bearing",
                "descriptors": "refined facial features, elegant bone structure",
            },
        }

        gender_lower = gender.lower() if gender else None
        return gender_terms.get(
            gender_lower,
            {
                "title": "person",
                "features": "balanced features, neutral bone structure",
                "clothing": "neutral garments",
                "posture": "balanced presence",
                "descriptors": "harmonious facial features, balanced bone structure",
            },
        )

    def wait_for_prediction(self, prediction, timeout=300, poll_interval=2):
        """Wait for a prediction to complete."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Get the current status of the prediction
            prediction = replicate.predictions.get(prediction.id)

            if prediction.status == "succeeded":
                return prediction
            elif prediction.status == "failed":
                raise Exception(f"Prediction failed: {prediction.error}")
            elif prediction.status == "canceled":
                raise Exception("Prediction was canceled")

            logging.info(f"Waiting for prediction... Status: {prediction.status}")
            time.sleep(poll_interval)

        raise Exception(f"Prediction timed out after {timeout} seconds")

    def generate_with_gemini(
        self, portrait_prompt: str, sample: NordicSample
    ) -> Optional[str]:
        """Generate portrait using Google Gemini."""
        try:
            # Create content for image generation
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=portrait_prompt),
                        types.Part.from_text(
                            text="Generate this portrait exactly as described."
                        ),
                    ],
                ),
            ]

            # Configure generation parameters exactly as in documentation
            generate_content_config = types.GenerateContentConfig(
                temperature=1,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
                response_modalities=[
                    "image",
                    "text",
                ],
                response_mime_type="text/plain",
            )

            # Generate image
            thread_safe_logging(
                logging.INFO, "Starting image generation with Gemini..."
            )

            # Use the experimental image generation model
            model = "gemini-2.0-flash-exp-image-generation"

            # Process the response stream
            for chunk in self.gemini_client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                if (
                    not chunk.candidates
                    or not chunk.candidates[0].content
                    or not chunk.candidates[0].content.parts
                ):
                    continue

                if chunk.candidates[0].content.parts[0].inline_data:
                    # Save the image
                    filename = f"{sample.sample_id}.jpg"
                    filepath = self.images_dir / filename

                    inline_data = chunk.candidates[0].content.parts[0].inline_data
                    file_extension = mimetypes.guess_extension(inline_data.mime_type)
                    if file_extension:
                        filepath = (
                            self.images_dir / f"{sample.sample_id}{file_extension}"
                        )

                    with open(filepath, "wb") as f:
                        f.write(inline_data.data)

                    thread_safe_logging(
                        logging.INFO,
                        f"Successfully saved Gemini portrait with mime type {inline_data.mime_type} to: {filepath}",
                    )
                    return str(filepath)
                else:
                    if hasattr(chunk, "text") and chunk.text:
                        thread_safe_logging(
                            logging.INFO, f"Gemini response text: {chunk.text}"
                        )

            thread_safe_logging(logging.ERROR, "No valid image data in Gemini response")
            return None

        except Exception as e:
            thread_safe_logging(
                logging.ERROR,
                f"Error generating Gemini portrait for {sample.sample_id}: {str(e)}",
            )
            return None

    def generate_portrait(self, sample: NordicSample) -> Optional[str]:
        """Generate a portrait for a single sample."""
        try:
            # Check if file already exists
            filename = f"{sample.sample_id}.jpg"
            filepath = self.images_dir / filename

            if filepath.exists():
                thread_safe_logging(
                    logging.INFO,
                    f"Skipping existing portrait for {sample.sample_id}: {filepath}",
                )
                return str(filepath)

            # Apply rate limiting
            self.rate_limit()

            # Get gender-specific terms and geographical context
            gender_info = self.get_gender_terms(sample.gender)
            geo_context = self.get_geographical_context(sample)

            # Log sample details
            thread_safe_logging(
                logging.INFO, f"\nGenerating portrait for {sample.sample_id}"
            )
            thread_safe_logging(
                logging.INFO, f"Culture: {sample.tier_1} -> {sample.tier_2}"
            )
            thread_safe_logging(
                logging.INFO, f"Location: {sample.location}, {sample.region}"
            )

            # Create optimized prompt
            portrait_prompt = f"""Create a photorealistic portrait with these exact specifications:

Subject: {sample.marketing_name}
Time Period: {sample.years_range} BCE
Culture: {sample.tier_2}
Location: {sample.location}, {sample.region}

Portrait Style:
- Square image format (1:1 aspect ratio)
- Ultra-detailed colour photograph
- Kodak Gold 200 film style, no modern digital effects, no monochrome
- Natural color, no filters or effects
- Professional portrait composition
- 2/3 turn pose, head at top third intersection
- Shoulders angled 45° to camera
- Face turned 3/4 toward viewer
- Shallow depth of field (f/2.8) focused on eyes
- Professional Rembrandt lighting with 45° key light
- Subtle rim light for separation

Physical Characteristics:
- {gender_info['features']}
- Natural skin texture with historical weathering
- Authentic period-appropriate facial features
- No modern beauty standards or enhancements

Historical Attire:
- Authentic {sample.years_range} BCE {sample.tier_2} {gender_info['clothing']}
- Natural woven fabrics with visible texture
- Traditional metal clasps and ornaments with patina
- Leather details with period-accurate wear
- Handwoven edges with natural wear patterns

Environmental Context:
- {geo_context['description']} (defocused)
- {geo_context['features']} creating depth
- {geo_context['atmosphere']}
- Subtle {geo_context['architecture']} in distance

Key Requirements:
- Historical accuracy in all details
- No modern elements or styling
- Natural imperfections and weathering
- Torso view, no extreme close-ups
- No artificial enhancements or modern beauty standards"""

            # Enhanced negative prompt for better historical accuracy
            negative_prompt = """dark, flat background, make-up, close-up, model, beautiful, symmetry, beauty, makeup, (deformed iris, deformed pupils, semi-realistic, cgi, 3d, render, sketch, cartoon, drawing, anime, modern elements, contemporary style, buttons, zippers, synthetic materials, wrong historical period, modern clothing, anachronistic details, deformed features, bad anatomy, extra limbs, plain background, studio backdrop, modern buildings, text, watermark, blurry, low quality, incorrect period architecture, modern landscape features, incorrect framing, cropped head, extreme close-up, full body shot, harsh lighting, flat lighting, overexposed, underexposed"""

            # Log prompts
            thread_safe_logging(logging.INFO, "\nPortrait Prompt:")
            thread_safe_logging(logging.INFO, portrait_prompt)

            if self.use_gemini:
                return self.generate_with_gemini(portrait_prompt, sample)
            else:
                # Generate image with flux-1.1-pro parameters
                thread_safe_logging(
                    logging.INFO, "Starting image generation with Replicate..."
                )

                try:
                    # Use replicate.run() instead of predictions.create()
                    output = replicate.run(
                        "black-forest-labs/flux-1.1-pro-ultra",
                        input={
                            "raw": True,
                            "prompt": portrait_prompt.strip(),
                            "negative_prompt": negative_prompt.strip(),
                            "aspect_ratio": "1:1",  # Square format for consistency
                            "output_format": "jpg",
                            "output_quality": 95,  # High quality output
                            "safety_tolerance": 2,  # Standard safety level
                            "prompt_upsampling": True,  # Enable advanced prompt processing
                            "scheduler": "K_EULER",  # Better for portrait details
                            "num_inference_steps": 50,  # Higher quality generation
                            "image_prompt_strength": 0.1,  # Added as per example
                        },
                    )

                    # Handle the output
                    if output:
                        # Get the image URL (output is either a string or a list with one item)
                        image_url = output[0] if isinstance(output, list) else output

                        # Download and save the image
                        filename = f"{sample.sample_id}.jpg"
                        filepath = self.images_dir / filename

                        response = requests.get(image_url, timeout=30)
                        if response.status_code == 200:
                            with open(filepath, "wb") as f:
                                f.write(response.content)
                            thread_safe_logging(
                                logging.INFO, f"Successfully saved portrait: {filename}"
                            )
                            return str(filepath)
                        else:
                            thread_safe_logging(
                                logging.ERROR,
                                f"Failed to download image: HTTP {response.status_code}",
                            )
                            return None
                    else:
                        thread_safe_logging(
                            logging.ERROR, "No output received from Replicate"
                        )
                        return None

                except Exception as e:
                    thread_safe_logging(
                        logging.ERROR, f"Error in Replicate generation: {str(e)}"
                    )
                    return None

        except Exception as e:
            thread_safe_logging(
                logging.ERROR,
                f"Error generating portrait for {sample.sample_id}: {str(e)}",
            )
            return None

    def process_samples(self, samples: List[NordicSample]):
        """Process all samples and generate portraits using thread pool."""
        total = len(samples)

        # Count existing files
        existing_files = sum(
            1
            for sample in samples
            if (self.images_dir / f"{sample.sample_id}.jpg").exists()
        )
        thread_safe_logging(
            logging.INFO,
            f"Found {existing_files} existing portraits, {total - existing_files} to generate",
        )
        thread_safe_logging(
            logging.INFO, f"Processing {total} samples using {self.num_threads} threads"
        )

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.num_threads
        ) as executor:
            # Submit all samples to the thread pool
            future_to_sample = {
                executor.submit(self.generate_portrait, sample): sample
                for sample in samples
            }

            # Process completed futures as they finish
            completed = 0
            for future in concurrent.futures.as_completed(future_to_sample):
                sample = future_to_sample[future]
                completed += 1
                try:
                    portrait_path = future.result()
                    if portrait_path:
                        status = (
                            "skipped"
                            if (self.images_dir / f"{sample.sample_id}.jpg").exists()
                            else "generated"
                        )
                        thread_safe_logging(
                            logging.INFO,
                            f"[{completed}/{total}] Successfully {status} portrait for {sample.sample_id}: {portrait_path}",
                        )
                    else:
                        thread_safe_logging(
                            logging.ERROR,
                            f"[{completed}/{total}] Failed to generate portrait for {sample.sample_id}",
                        )
                except Exception as e:
                    thread_safe_logging(
                        logging.ERROR,
                        f"[{completed}/{total}] Error processing {sample.sample_id}: {str(e)}",
                    )


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Generate portraits from Nordic DNA samples"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="input/input.csv",
        help="Input CSV file path (default: input.csv)",
    )
    parser.add_argument(
        "--output", type=str, default="out", help="Output directory (default: out)"
    )
    parser.add_argument(
        "--samples", type=int, help="Number of random samples to process (optional)"
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=10,
        help="Number of parallel threads (default: 10)",
    )
    parser.add_argument(
        "--use-gemini",
        action="store_true",
        help="Use Google Gemini for image generation instead of Replicate",
    )
    parser.add_argument(
        "--force", action="store_true", help="Force regeneration of existing portraits"
    )

    args = parser.parse_args()

    try:
        generator = PortraitGenerator(args.output, args.threads, args.use_gemini)
        samples = generator.load_samples(args.input, args.samples)

        if not args.force:
            # Filter out samples that already have portraits
            original_count = len(samples)
            samples = [
                s
                for s in samples
                if not (generator.images_dir / f"{s.sample_id}.jpg").exists()
            ]
            if len(samples) < original_count:
                thread_safe_logging(
                    logging.INFO,
                    f"Skipping {original_count - len(samples)} existing portraits. Use --force to regenerate.",
                )

        generator.process_samples(samples)

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
