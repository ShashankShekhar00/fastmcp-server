"""
Structured logging with security filtering.
Redacts sensitive data (tokens, API keys) from logs.
"""

import logging
import json
import re
from typing import Any, Dict, Optional
from datetime import datetime


# Patterns to redact from logs
SENSITIVE_PATTERNS = [
    (re.compile(r'Bearer\s+[\w\-\.]+', re.IGNORECASE), 'Bearer <REDACTED>'),
    (re.compile(r'"access_token"\s*:\s*"[^"]+"'), '"access_token": "<REDACTED>"'),
    (re.compile(r'"api_key"\s*:\s*"[^"]+"'), '"api_key": "<REDACTED>"'),
    (re.compile(r'"secret"\s*:\s*"[^"]+"'), '"secret": "<REDACTED>"'),
    (re.compile(r'"password"\s*:\s*"[^"]+"'), '"password": "<REDACTED>"'),
    (re.compile(r'appid=[a-zA-Z0-9]+'), 'appid=<REDACTED>'),
    (re.compile(r'client_secret=[^&\s]+'), 'client_secret=<REDACTED>'),
]


class SecurityFilter(logging.Filter):
    """Filter that redacts sensitive information from log messages."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Redact sensitive data from log record.
        
        Args:
            record: Log record to filter
            
        Returns:
            True (always allow the record, but modify it)
        """
        # Redact message
        if isinstance(record.msg, str):
            for pattern, replacement in SENSITIVE_PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        
        # Redact args
        if record.args:
            cleaned_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    for pattern, replacement in SENSITIVE_PATTERNS:
                        arg = pattern.sub(replacement, arg)
                cleaned_args.append(arg)
            record.args = tuple(cleaned_args)
        
        return True


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    Outputs logs in JSON format for easy parsing.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add custom fields from extra
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'message', 'pathname', 'process', 'processName',
                          'relativeCreated', 'thread', 'threadName', 'exc_info',
                          'exc_text', 'stack_info']:
                log_data[key] = value
        
        return json.dumps(log_data)


def setup_logger(
    name: str,
    level: str = "INFO",
    structured: bool = False
) -> logging.Logger:
    """
    Set up a logger with security filtering.
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        structured: Whether to use JSON structured logging
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler()
    handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Add security filter
    handler.addFilter(SecurityFilter())
    
    # Set formatter
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with security filtering.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_tool_execution(
    logger: logging.Logger,
    tool_name: str,
    duration_ms: float,
    success: bool,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    error: Optional[str] = None
):
    """
    Log tool execution with structured data.
    
    Args:
        logger: Logger instance
        tool_name: Name of the tool executed
        duration_ms: Execution duration in milliseconds
        success: Whether execution succeeded
        user_id: User/client ID from OAuth token
        request_id: Request ID for tracing
        error: Error message if execution failed
    """
    log_data = {
        'tool': tool_name,
        'duration_ms': round(duration_ms, 2),
        'success': success,
    }
    
    if user_id:
        log_data['user_id'] = user_id
    
    if request_id:
        log_data['request_id'] = request_id
    
    if error:
        log_data['error'] = error
    
    if success:
        logger.info(
            f"Tool '{tool_name}' executed successfully in {duration_ms:.2f}ms",
            extra=log_data
        )
    else:
        logger.error(
            f"Tool '{tool_name}' failed after {duration_ms:.2f}ms: {error}",
            extra=log_data
        )


def log_api_call(
    logger: logging.Logger,
    api_name: str,
    endpoint: str,
    duration_ms: float,
    status_code: int,
    success: bool,
    error: Optional[str] = None
):
    """
    Log external API call with structured data.
    
    Args:
        logger: Logger instance
        api_name: Name of the API (e.g., "OpenWeatherMap")
        endpoint: API endpoint called
        duration_ms: Request duration in milliseconds
        status_code: HTTP status code
        success: Whether call succeeded
        error: Error message if call failed
    """
    log_data = {
        'api': api_name,
        'endpoint': endpoint,
        'duration_ms': round(duration_ms, 2),
        'status_code': status_code,
        'success': success,
    }
    
    if error:
        log_data['error'] = error
    
    if success:
        logger.info(
            f"{api_name} API call succeeded: {endpoint} ({status_code}) in {duration_ms:.2f}ms",
            extra=log_data
        )
    else:
        logger.warning(
            f"{api_name} API call failed: {endpoint} ({status_code}): {error}",
            extra=log_data
        )


def log_auth_event(
    logger: logging.Logger,
    event_type: str,
    success: bool,
    user_id: Optional[str] = None,
    reason: Optional[str] = None
):
    """
    Log authentication event.
    
    Args:
        logger: Logger instance
        event_type: Type of auth event (e.g., "token_validation", "login")
        success: Whether authentication succeeded
        user_id: User/client ID if available
        reason: Failure reason if unsuccessful
    """
    log_data = {
        'event_type': event_type,
        'success': success,
    }
    
    if user_id:
        log_data['user_id'] = user_id
    
    if reason:
        log_data['reason'] = reason
    
    if success:
        logger.info(
            f"Auth event '{event_type}' succeeded for user {user_id}",
            extra=log_data
        )
    else:
        logger.warning(
            f"Auth event '{event_type}' failed: {reason}",
            extra=log_data
        )


def redact_sensitive_data(data: Any) -> Any:
    """
    Recursively redact sensitive data from dictionaries and strings.
    
    Args:
        data: Data to redact (string, dict, list, or other)
        
    Returns:
        Redacted data
    """
    if isinstance(data, str):
        for pattern, replacement in SENSITIVE_PATTERNS:
            data = pattern.sub(replacement, data)
        return data
    
    elif isinstance(data, dict):
        redacted = {}
        for key, value in data.items():
            # Redact keys that might contain sensitive data
            if any(sensitive in key.lower() for sensitive in 
                   ['token', 'password', 'secret', 'api_key', 'apikey', 'key', 'auth']):
                redacted[key] = '<REDACTED>'
            else:
                redacted[key] = redact_sensitive_data(value)
        return redacted
    
    elif isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]
    
    else:
        return data


# Initialize default logger for the application
app_logger = None

def init_app_logger(log_level: str = "INFO", structured: bool = False):
    """
    Initialize the application-wide logger.
    
    Args:
        log_level: Log level to use
        structured: Whether to use JSON structured logging
    """
    global app_logger
    app_logger = setup_logger("mcp_server", log_level, structured)
    return app_logger
