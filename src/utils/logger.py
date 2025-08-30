"""
SCLI Logging Utility

Centralized logging system using Loguru with enhanced console and file output.
Provides colored console logs with file path, datetime, and structured formatting.

Best practices:
- NEVER use print() directly, always use this logger
- Use appropriate log levels: trace, debug, info, success, warning, error, critical
- Include context with extra information when needed
- Configure rotation and retention for production use
"""

import sys
import os
from pathlib import Path
from typing import Any
from traceback import format_exc as traceback_format_exc
from loguru import logger as loguru_instance


def _get_relative_path(record):
    """Get relative path from src/ directory."""
    file_path = Path(record["file"].path)
    try:
        # Find project root and get path relative to src/
        current_dir = Path.cwd()
        if (current_dir / "pyproject.toml").exists():
            full_relative = file_path.relative_to(current_dir)
            # Remove 'src/' prefix if it exists
            if full_relative.parts[0] == "src":
                return "/".join(full_relative.parts[1:])
            else:
                return str(full_relative)
        else:
            # Fallback to just filename if can't find project root
            return file_path.name
    except (ValueError, IndexError):
        # If file is outside project, use filename
        return file_path.name


class Logger:
    """
    SCLI centralized logging system with enhanced formatting and file management.
    
    Features:
    - Colored console output based on log levels
    - File path and line number tracking
    - Timestamp with human-readable format
    - Automatic file rotation and retention
    - Structured logging with JSON support
    - Thread-safe operations
    """
    
    def __init__(self):
        """Initialize SCLI logger with optimized configuration."""
        # Remove default handler to customize completely
        loguru_instance.remove(0)
        
        # Configure console handler with colors and enhanced format
        self._setup_console_handler()
        
        # Setup file handlers for different environments
        self._setup_file_handlers()
    
    def _setup_console_handler(self):
        """Configure colored console output with enhanced formatting."""
        def format_with_relative_path(record):
            relative_path = _get_relative_path(record)
            record["extra"]["relative_path"] = relative_path
            return (
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                f"<cyan>{relative_path}:{record['line']}</cyan> | "
                "<level>{message}</level>\n"
            )
        
        loguru_instance.add(
            sys.stderr,
            format=format_with_relative_path,
            level="DEBUG",
            colorize=True,
            backtrace=True,
            diagnose=True,
            enqueue=True  # Thread-safe
        )
    
    def _setup_file_handlers(self):
        """Setup file logging with rotation and retention."""
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # General application logs
        loguru_instance.add(
            logs_dir / "scli_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {file.path}:{line} | {message}",
            level="INFO",
            rotation="00:00",  # New file daily at midnight
            retention="7 days",  # Keep logs for 7 days
            compression="zip",  # Compress old logs
            enqueue=True
        )
        
        # Error-specific logs
        loguru_instance.add(
            logs_dir / "scli_errors_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {file.path}:{line} | {message} | {extra}",
            level="ERROR",
            rotation="10 MB",  # New file every 10MB
            retention="30 days",  # Keep error logs for 30 days
            compression="zip",
            enqueue=True,
            backtrace=True,
            diagnose=True
        )
        
        # JSON structured logs for production analysis
        loguru_instance.add(
            logs_dir / "scli_structured_{time:YYYY-MM-DD}.json",
            format="{message}",
            level="INFO",
            rotation="100 MB",
            retention="14 days",
            compression="zip",
            serialize=True,  # JSON format
            enqueue=True
        )
    
    def get_logger(self):
        """Get configured loguru logger instance."""
        return loguru_instance
    
    def add_context(self, **context: Any):
        """Add contextual information to logger."""
        return loguru_instance.bind(**context)
    
    def catch_exceptions(self):
        """Decorator for automatic exception logging."""
        return loguru_instance.catch
    
    # Direct logging methods for class usage
    def trace(self, message: str, detail=None):
        """Log trace level message with optional detail dict."""
        self._validate_and_log('trace', message, detail)
    
    def debug(self, message: str, detail=None):
        """Log debug level message with optional detail dict."""
        self._validate_and_log('debug', message, detail)
    
    def info(self, message: str, detail=None):
        """Log info level message with optional detail dict."""
        self._validate_and_log('info', message, detail)
    
    def success(self, message: str, detail=None):
        """Log success level message with optional detail dict."""
        self._validate_and_log('success', message, detail)
    
    def warning(self, message: str, detail=None):
        """Log warning level message with optional detail dict."""
        self._validate_and_log('warning', message, detail)
    
    def error(self, message: str, detail=None):
        """Log error level message with optional detail dict."""
        self._validate_and_log('error', message, detail)
    
    def critical(self, message: str = "Critical error occurred", detail=None):
        """Log critical level message with automatic traceback."""
        traceback_info = traceback_format_exc()
        final_message = f"{message}\n{traceback_info}"
        self._validate_and_log('critical', final_message, detail)
    
    def _validate_and_log(self, level: str, message: str, detail):
        """
        Validate logging parameters and perform actual logging.
        
        Args:
            level: Log level (trace, debug, info, success, warning, error, critical)
            message: Must be a plain string, no f-strings or b-strings allowed
            detail: Optional dict with additional data, or None/False to ignore
        """
        # Validate message is a plain string
        if not isinstance(message, str):
            raise TypeError(f"Log message must be a plain string, got {type(message).__name__}")
        
        # Check for f-string or b-string patterns (basic validation)
        if message.startswith(('f"', "f'", 'b"', "b'")):
            raise ValueError("f-strings and b-strings not allowed in log messages. Use plain string with detail parameter.")
        
        # Validate detail parameter
        if detail is not None and detail is not False:
            if not isinstance(detail, dict):
                raise TypeError(f"detail parameter must be dict or None/False, got {type(detail).__name__}")
        
        # Get the logging method
        log_method = getattr(loguru_instance, level)
        
        # Log with or without detail context
        if detail and isinstance(detail, dict):
            # Build message with detail information
            import json
            detail_str = json.dumps(detail, separators=(',', ':'))
            full_message = f"{message} | {detail_str}"
            log_method(full_message)
        else:
            # Log plain message
            log_method(message)
    
    def configure_for_testing(self):
        """Configure logger for testing environment (less verbose)."""
        loguru_instance.remove()  # Remove all handlers
        loguru_instance.add(
            sys.stderr,
            format="<level>{level: <8}</level> | <cyan>{file.path}:{line}</cyan> | {message}",
            level="WARNING",  # Only warnings and above in tests
            colorize=True
        )
    
    def configure_for_production(self):
        """Configure logger for production environment."""
        loguru_instance.remove()  # Remove all handlers
        
        # Console: Only critical errors
        loguru_instance.add(
            sys.stderr,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {file.path}:{line} | {message}",
            level="ERROR",
            colorize=False  # No colors in production console
        )
        
        # Enhanced file logging for production
        logs_dir = Path("/var/log/scli") if os.path.exists("/var/log") else Path("logs")
        logs_dir.mkdir(exist_ok=True, parents=True)
        
        loguru_instance.add(
            logs_dir / "scli_production.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {file.path}:{line} | {message}",
            level="INFO",
            rotation="50 MB",
            retention="90 days",
            compression="zip",
            enqueue=True
        )


# Pre-initialized global logger instance
logger = Logger()



# Export the logger for direct import
__all__ = [
    'Logger',
    'logger'
]