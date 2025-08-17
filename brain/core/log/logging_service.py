import logging
from logging.handlers import RotatingFileHandler
import os

# Define default log file path
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "logs/beanbrain.log")

# Ensure the logs directory exists
os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

def get_logger(name: str) -> logging.Logger:
    """
    Creates and configures a logger with a rotating file handler.

    Args:
        name (str): Name of the logger (usually the module name).

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)

        # Rotating file handler
        file_handler = RotatingFileHandler(
            LOG_FILE_PATH, maxBytes=5 * 1024 * 1024, backupCount=3
        )
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Enhanced formatter with file and line number
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
