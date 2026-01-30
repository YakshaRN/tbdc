"""
Logging configuration using loguru.
"""
import sys
from loguru import logger

from app.core.config import settings


def setup_logging():
    """
    Configure application logging.
    """
    # Remove default handler
    logger.remove()
    
    # Add console handler with appropriate level
    log_level = "DEBUG" if settings.DEBUG else "INFO"
    
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
    )
    
    # Add file handler for production
    if not settings.DEBUG:
        logger.add(
            "logs/app.log",
            rotation="10 MB",
            retention="10 days",
            compression="gz",
            level="INFO",
        )
    
    return logger


# Initialize logger
app_logger = setup_logging()
