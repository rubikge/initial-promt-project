from pydantic import BaseModel, Field
from typing import Union, Dict, Any, Optional, List


class CompletionResponse(BaseModel):
    """Response from the Replicate completion API"""

    content: Union[str, Dict[str, Any], List[str]] = Field(
        description="The model's response content"
    )


class ModelConfig(BaseModel):
    """Universal configuration for any Replicate model"""
    
    name: str = Field(description="Model name/identifier (e.g., 'black-forest-labs/flux-1.1-pro-ultra')")
    
    def get_input_params(self, prompt: str = None) -> Dict[str, Any]:
        """
        Get input parameters for the model, filtering out None values.
        
        Args:
            prompt (str): Override prompt if provided
            
        Returns:
            Dict[str, Any]: Filtered input parameters
        """
        params = {}
        
        # Use provided prompt or fall back to config prompt
        if prompt is not None:
            params["prompt"] = prompt
            
        # Add all non-None parameters from the model config
        for field_name, field_value in self.dict().items():
            if field_name not in ["name"] and field_value is not None:
                params[field_name] = field_value
                
        return params


class FluxProUltraConfig(ModelConfig):
    """Configuration for Flux Pro Ultra model with default parameters"""
    
    name: str = Field(default="black-forest-labs/flux-1.1-pro-ultra", description="Model name/identifier")
    raw: Optional[bool] = Field(default=None, description="Generate less processed, more natural-looking images")
    seed: Optional[int] = Field(default=None, description="Random seed. Set for reproducible generation")
    prompt: Optional[str] = Field(default=None, description="Text prompt for image generation")
    aspect_ratio: Optional[str] = Field(default="1:1", description="Aspect ratio for the generated image")
    image_prompt: Optional[str] = Field(default=None, description="Image to use with Flux Redux. This is used together with the text prompt to guide the generation towards the composition of the image_prompt. Must be jpeg, png, gif, or webp.")
    output_format: Optional[str] = Field(default="jpg", description="Format of the output images.")
    safety_tolerance: Optional[int] = Field(default=2, description="Safety tolerance, 1 is most strict and 6 is most permissive")
    image_prompt_strength: Optional[float] = Field(default=None, description="Blend between the prompt and the image prompt.")


class FluxKontextMaxConfig(ModelConfig):
    """Configuration for Flux Kontext Max model with default parameters"""
    
    name: str = Field(default="black-forest-labs/flux-kontext-max", description="Model name/identifier")
    seed: Optional[int] = Field(default=None, description="Random seed. Set for reproducible generation")
    prompt: Optional[str] = Field(default=None, description="Text description of what you want to generate, or the instruction on how to edit the given image.")
    input_image: Optional[str] = Field(default=None, description="Image to use as reference. Must be jpeg, png, gif, or webp.")
    aspect_ratio: Optional[str] = Field(default="match_input_image", description="Aspect ratio of the generated image. Use 'match_input_image' to match the aspect ratio of the input image.")
    output_format: Optional[str] = Field(default="jpg", description="Output format for the generated image")
    safety_tolerance: Optional[int] = Field(default=2, description="Safety tolerance, 0 is most strict and 6 is most permissive. 2 is currently the maximum allowed when input images are used.")
    prompt_upsampling: Optional[bool] = Field(default=None, description="Automatic prompt improvement")

class FluxKontextProConfig(ModelConfig):
    """Configuration for Flux Kontext Pro model with default parameters"""
    
    name: str = Field(default="black-forest-labs/flux-kontext-pro", description="Model name/identifier")
    seed: Optional[int] = Field(default=None, description="Random seed. Set for reproducible generation")
    prompt: Optional[str] = Field(default=None, description="Text description of what you want to generate, or the instruction on how to edit the given image.")
    input_image: Optional[str] = Field(default=None, description="Image to use as reference. Must be jpeg, png, gif, or webp.")
    aspect_ratio: Optional[str] = Field(default="match_input_image", description="Aspect ratio of the generated image. Use 'match_input_image' to match the aspect ratio of the input image.")
    output_format: Optional[str] = Field(default="jpg", description="Output format for the generated image")
    safety_tolerance: Optional[int] = Field(default=2, description="Safety tolerance, 0 is most strict and 6 is most permissive. 2 is currently the maximum allowed when input images are used.")
    prompt_upsampling: Optional[bool] = Field(default=None, description="Automatic prompt improvement")



class Models:
    """Class for accessing Replicate model configurations"""

    # Image generation models with specific configurations
    FLUX_1_1_PRO_ULTRA = FluxProUltraConfig()
    FLUX_KONTEXT_MAX = FluxKontextMaxConfig()
    FLUX_KONTEXT_PRO = FluxKontextProConfig()
    
    @staticmethod
    def create_custom_config(
        model_name: str,
        **kwargs
    ) -> ModelConfig:
        """
        Create a custom model configuration for any Replicate model.
        
        Args:
            model_name (str): The model name/identifier
            **kwargs: Additional parameters for the model
            
        Returns:
            ModelConfig: Custom model configuration
        """
        return ModelConfig(name=model_name, **kwargs)


# Create a single instance of Models
MODELS = Models() 