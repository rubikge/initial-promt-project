import logging
import sys
from pathlib import Path
from datetime import datetime
from colorama import init, Fore, Style
import inspect

# Initialize colorama for Windows compatibility
init()

class CustomFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels and emojis for file output"""
    
    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }
    EMOJIS = {
        'DEBUG': '🔵',
        'INFO': '🟢',
        'WARNING': '🟡',
        'ERROR': '🔴',
        'CRITICAL': '❗'
    }

    def __init__(self, fmt=None, datefmt=None, style='%', use_colors=True):
        super().__init__(fmt, datefmt, style)
        self.use_colors = use_colors

    def format(self, record):
        record.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        levelname = record.levelname
        msg = record.getMessage()
        if self.use_colors and levelname in self.COLORS:
            color = self.COLORS[levelname]
            levelname = f"{color}{levelname}{Style.RESET_ALL}"
            msg = f"{color}{msg}{Style.RESET_ALL}"
        elif not self.use_colors and levelname in self.EMOJIS:
            levelname = f"{self.EMOJIS[levelname]} {levelname}"
        formatted = self._fmt.replace('%(levelname)s', levelname).replace('%(message)s', msg)
        return formatted % record.__dict__

def setup_logger(log_file: str = 'main.log', level: int = logging.INFO) -> logging.Logger:
    """
    Set up and configure the logger
    
    Args:
        log_file (str, optional): Path to the log file. If None, logs will only be printed to console.
                                 If 'log.txt', will create log.txt in the caller's directory.
        level (int, optional): Logging level. Defaults to logging.INFO
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger('app_logger')
    logger.setLevel(level)
    
    # Clear any existing handlers
    logger.handlers = []
    
    # Create console handler with custom formatter (with colors)
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = CustomFormatter(
        '%(timestamp)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        use_colors=True
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log_file is specified
    if log_file:
        # Get the caller's file path
        caller_frame = inspect.stack()[1]
        caller_file = caller_frame.filename
        caller_dir = Path(caller_file).parent
        log_file = str(caller_dir / log_file)
        
        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Add empty line to the log file
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write('\n-----------------------------------\n')
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_formatter = CustomFormatter(
            '%(timestamp)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            use_colors=False
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

# Create a default logger instance
logger = setup_logger()

# Example usage
if __name__ == '__main__':
    # Example with file logging
    test_logger = setup_logger('logs/test.log')
    test_logger.debug('This is a debug message')
    test_logger.info('This is an info message')
    test_logger.warning('This is a warning message')
    test_logger.error('This is an error message')
    test_logger.critical('This is a critical message') 