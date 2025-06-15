# Post Writer Backend

A Python-based backend service for processing and transforming data using Large Language Models (LLMs). This project provides a foundation for building data processing pipelines with AI-powered text generation and manipulation capabilities.

## Features

- Data processing and transformation using LLMs
- CSV data handling and conversion
- Integration with OpenRouter API for LLM access
- Comprehensive logging system
- Test suite for ensuring reliability

## Technologies

- **Python 3.13+**: Core programming language
- **OpenRouter**: LLM API integration for text generation
- **Colorama**: Terminal text coloring and formatting
- **Python-dotenv**: Environment variable management
- **Pytest**: Testing framework

## Project Structure

```
post-writer-backend/
├── src/                    # Source code
│   ├── csv_converter/     # CSV processing modules
│   ├── openrouter/        # OpenRouter API integration
│   ├── main.py           # Main application entry point
│   └── logger.py         # Logging configuration
├── input/                 # Input data directory
├── output/               # Output data directory
├── tests/                # Test suite
└── pyproject.toml        # Project configuration and dependencies
```

## Setup

1. Ensure you have Python 3.13 or higher installed
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -e .
   ```
4. Copy `.env.sample` to `.env` and configure your environment variables:
   ```bash
   cp .env.sample .env
   ```

## Environment Variables

Create a `.env` file with the following variables:
- `OPENROUTER_API_KEY`: Your OpenRouter API key

## Development

- Run tests:
  ```bash
  pytest
  ```
- Check logs in `src/main.log`

## Usage

1. Place your input data in the `input/` directory
2. Run the main script:
   ```bash
   python src/main.py
   ```
3. Processed results will be available in the `output/` directory
