"""
Logging System Module
Centralized logging for the game
"""
import logging
import os
from config.settings import LOG_LEVEL, LOG_FILE

def setup_logging():
    """Configure logging for the game"""
    # Create root logger
    root_logger = logging.getLogger('space_defender')
    
    # Only configure if not already configured
    if root_logger.handlers:
        return root_logger
    
    root_logger.setLevel(LOG_LEVEL)
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    try:
        file_handler = logging.FileHandler(LOG_FILE, mode='w')
        file_handler.setLevel(LOG_LEVEL)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create file handler: {e}")
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    root_logger.info("=" * 80)
    root_logger.info("GAME LOGGING INITIALIZED")
    root_logger.info("=" * 80)
    
    return root_logger

def get_logger(name='space_defender'):
    """Get the game logger"""
    logger = logging.getLogger(name)
    logger.propagate = True  # Ensure messages propagate to root logger
    return logger
