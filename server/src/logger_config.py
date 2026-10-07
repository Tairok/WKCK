"""Centralized logging configuration for BMC Server

This module provides a proper logging setup that respects config levels
and doesn't override them with hardcoded DEBUG levels.
"""

import logging
import os
from pathlib import Path
from config import Config


class LoggerConfigurator:
    """Handles proper logging configuration across the application"""
    
    # Cache to avoid reconfiguring
    _configured = False
    
    @classmethod
    def configure(cls) -> logging.Logger:
        """Configure root logger with proper level inheritance
        
        Returns:
            logging.Logger: Configured root logger
        """
        if cls._configured:
            return logging.getLogger()
        
        root_logger = logging.getLogger()
        
        # Set root logger to the minimum level needed by ANY handler
        # This allows handlers to do their own filtering
        root_logger.setLevel(logging.DEBUG)
        
        # Remove any existing handlers to avoid duplicates
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Create formatters
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s %(module)s.%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        
        # File handler - respects LOG_FILE_LEVEL from config
        os.makedirs(Config.LOG_PATH.parent, exist_ok=True)
        file_handler = logging.FileHandler(Config.LOG_PATH, encoding="utf-8", mode="a")
        file_handler.setFormatter(formatter)
        file_level = cls._parse_level(Config.LOG_FILE_LEVEL, logging.DEBUG)
        file_handler.setLevel(file_level)
        root_logger.addHandler(file_handler)
        
        # Console handler - respects LOG_CONSOLE_LEVEL from config
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_level = cls._parse_level(Config.LOG_CONSOLE_LEVEL, logging.WARNING)
        console_handler.setLevel(console_level)
        root_logger.addHandler(console_handler)
        
        # Suppress overly verbose external loggers
        logging.getLogger("django").setLevel(logging.WARNING)
        logging.getLogger("channels").setLevel(logging.WARNING)
        logging.getLogger("daphne").setLevel(logging.ERROR)
        logging.getLogger("daphne.ws_protocol").setLevel(logging.ERROR)
        logging.getLogger("urllib3").setLevel(logging.ERROR)
        logging.getLogger("asyncio").setLevel(logging.ERROR)
        
        cls._configured = True
        root_logger.info(f"[LOGGER] Logging configured: console={Config.LOG_CONSOLE_LEVEL}, file={Config.LOG_FILE_LEVEL}")
        
        return root_logger
    
    @staticmethod
    def _parse_level(level_name: str, fallback: int) -> int:
        """Parse logging level name to logging constant
        
        Args:
            level_name: String like 'DEBUG', 'INFO', 'WARN', 'ERROR'
            fallback: Fallback level if parsing fails
            
        Returns:
            int: logging level constant
        """
        try:
            return logging._nameToLevel.get(level_name.upper(), fallback)
        except (AttributeError, TypeError):
            return fallback


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name
    
    Usage:
        logger = get_logger(__name__)
        logger.info("Message")
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        logging.Logger: Configured logger
    """
    LoggerConfigurator.configure()
    return logging.getLogger(name)
