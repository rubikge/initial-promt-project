from logger import logger
from openrouter.client import OpenRouter
import os
from dotenv import load_dotenv

def main():

    logger.info("Starting post-writer-backend application")
    load_dotenv()
    
    # Initialize OpenRouter client
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OPENROUTER_API_KEY environment variable is not set")
        return
        
    openrouter = OpenRouter(api_key=api_key)
    
    # Example usage
    try:
        response = openrouter.get_completion("Write a short greeting message")
        logger.info(f"OpenRouter response: {response}")
    except Exception as e:
        logger.error(f"Error using OpenRouter: {str(e)}")
    
    logger.info("Application started successfully")

if __name__ == "__main__":
    main()
