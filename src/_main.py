from logger import setup_logger
from openrouter.openrouter_client import OpenRouter
import os
from dotenv import load_dotenv
from openrouter.models import ModelConfig
import logging


def main():
    # Set up logger with DEBUG level
    logger = setup_logger(level=logging.DEBUG)

    logger.info("Starting AI assistant application")
    load_dotenv()

    # Initialize OpenRouter client
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OPENROUTER_API_KEY environment variable is not set")
        return

    openrouter = OpenRouter(api_key=api_key)

    # Example usage
    try:
        prompt_new = """что находится в этих координатах 39.2 46.4"""

        response = openrouter.get_completion(
            prompt=prompt_new,
            model_config=ModelConfig(
                name="google/gemini-2.5-pro-preview",
                temperature=1,
                max_tokens=10000,
            ),
        )
        logger.info(f"OpenRouter response: {response}")
    except Exception as e:
        logger.error(f"Error using OpenRouter: {str(e)}")

    logger.info("Application started successfully")


if __name__ == "__main__":
    main()
