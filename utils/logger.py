"""
Centralized logging configuration for the application.
"""
import logging
import os
import sys
from datetime import datetime

# Define log levels mapping for easier configuration
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

def configure_logger(name, log_level="info", log_to_file=True):
    """
    Configure and return a logger with standardized settings.
    
    Parameters:
        name (str): The name of the logger, typically __name__
        log_level (str): Log level as string (debug, info, warning, error, critical)
        log_to_file (bool): Whether to log to file in addition to console
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Get the log level from mapping, default to INFO
    level = LOG_LEVELS.get(log_level.lower(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create stream handler for console output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Create formatter
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    console_handler.setFormatter(formatter)
    
    # Add console handler to logger
    logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_to_file:
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create file handler
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(logs_dir, f"{date_str}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        
        # Add file handler to logger
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name=None, log_level=None):
    """
    Get a configured logger. Uses environment variable LOG_LEVEL if set,
    otherwise defaults to 'info'.
    
    Parameters:
        name (str): The name of the logger, defaults to the calling module's name
        log_level (str): Override the default or environment-specified log level
        
    Returns:
        logging.Logger: Configured logger instance
    """
    if name is None:
        # Get the caller's module name as the logger name if not provided
        import inspect
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        name = module.__name__ if module else "root"
    
    # Use provided log_level, environment variable, or default to info
    level = log_level or os.environ.get("LOG_LEVEL", "info")
    
    return configure_logger(name, level) 