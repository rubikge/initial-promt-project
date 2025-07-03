import replicate
import time
from .models import MODELS, ModelConfig


class ReplicateClient:
    def __init__(self, api_token: str):
        """
        Initialize Replicate client.

        Args:
            api_token (str): Your Replicate API token
        """
        self.api_token = api_token
        # Set the API token for the replicate library
        replicate.api_token = api_token



    def get_completion(
        self,
        prompt: str,
        model_config: ModelConfig = MODELS.FLUX_1_1_PRO_ULTRA,
        max_retries: int = 3,
    ):
        """
        Get completion from Replicate API.

        Args:
            prompt (str): The prompt to send to the model
            model_config (ModelConfig): The model configuration to use (default: MODELS.FLUX_1_1_PRO_ULTRA)
            max_retries (int): Maximum number of retry attempts

        Returns:
            The model's response content
        """
        for attempt in range(max_retries):
            try:
                # Get input parameters from model config
                input_params = model_config.get_input_params(prompt)



                # Run the prediction
                output = replicate.run(
                    model_config.name,
                    input=input_params
                )

                return str(output)

            except Exception as e:
                print(f"Attempt {attempt + 1} failed with error: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)  # Exponential backoff
                else:
                    raise Exception(
                        f"Failed after {max_retries} attempts. Last error: {str(e)}"
                    )

    def stream_completion(
        self,
        prompt: str,
        model_config: ModelConfig = MODELS.FLUX_1_1_PRO_ULTRA,
    ):
        """
        Stream completion from Replicate API.

        Args:
            prompt (str): The prompt to send to the model
            model_config (ModelConfig): The model configuration to use
            json_output (bool): Whether to request JSON output format

        Yields:
            str: Streamed response chunks
        """
        try:
            # Get input parameters from model config
            input_params = model_config.get_input_params(prompt)



            # Stream the prediction
            for output in replicate.run(
                model_config.name,
                input=input_params,
                stream=True
            ):
                yield output

        except Exception as e:
            raise Exception(f"Streaming failed with error: {str(e)}")