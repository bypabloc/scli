"""
Logging configuration for SCLI
Provides structured logging with different levels and file output
"""

import os
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green  
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


def setup_logger(name: str = None, level: str = "INFO", log_to_file: bool = True) -> logging.Logger:
    """Setup logger with console and file handlers"""
    
    # Get or create logger
    if name is None:
        name = "scli"
    
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Set level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Create formatters
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if enabled)
    if log_to_file:
        try:
            # Find project root
            current_dir = Path(__file__).parent
            while current_dir.parent != current_dir:
                if (current_dir / "pyproject.toml").exists():
                    project_root = current_dir
                    break
                current_dir = current_dir.parent
            else:
                project_root = Path.cwd()
            
            # Create logs directory
            logs_dir = project_root / "logs"
            logs_dir.mkdir(exist_ok=True)
            
            # Create log file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d")
            log_file = logs_dir / f"scli_{timestamp}.log"
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)  # Always DEBUG for file
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            logger.debug(f"Logging to file: {log_file}")
            
        except Exception as e:
            logger.warning(f"Could not setup file logging: {e}")
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance"""
    if name is None:
        name = "scli"
    
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Setup logger if not already configured
        setup_logger(name)
    
    return logger


def set_debug_mode():
    """Enable debug mode for all loggers"""
    logging.getLogger("scli").setLevel(logging.DEBUG)
    for handler in logging.getLogger("scli").handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setLevel(logging.DEBUG)


def log_request(logger: logging.Logger, method: str, url: str, headers: dict = None, 
               data: any = None, response_status: int = None, response_text: str = None):
    """Log HTTP request details for debugging"""
    logger.debug(f"HTTP {method} Request:")
    logger.debug(f"  URL: {url}")
    
    if headers:
        # Mask sensitive headers
        safe_headers = {}
        for key, value in headers.items():
            if key.lower() in ['authorization', 'x-santander-client-id']:
                safe_headers[key] = f"{value[:8]}***" if len(value) > 8 else "***"
            else:
                safe_headers[key] = value
        logger.debug(f"  Headers: {safe_headers}")
    
    if data:
        logger.debug(f"  Data: {data}")
    
    if response_status is not None:
        logger.debug(f"HTTP Response:")
        logger.debug(f"  Status: {response_status}")
        if response_text:
            # Truncate long responses
            if len(response_text) > 500:
                logger.debug(f"  Body: {response_text[:500]}... (truncated)")
            else:
                logger.debug(f"  Body: {response_text}")


def log_config_info(logger: logging.Logger, config: dict, script_name: str):
    """Log configuration information (masking sensitive data)"""
    logger.info(f"Loading configuration for {script_name}")
    
    if not config:
        logger.warning(f"No configuration found for {script_name}")
        return
    
    # Create safe config for logging (mask sensitive values)
    safe_config = {}
    sensitive_keys = ['client_secret', 'password', 'token', 'secret', 'key']
    
    for key, value in config.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            if isinstance(value, str) and len(value) > 4:
                safe_config[key] = f"{value[:4]}***"
            else:
                safe_config[key] = "***"
        else:
            safe_config[key] = value
    
    logger.debug(f"Configuration loaded: {safe_config}")


# Initialize default logger
default_logger = setup_logger()