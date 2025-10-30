"""
Input validation functions for MCP server.
Validates user inputs before processing to prevent security issues.
"""

import re
from pathlib import Path
from typing import Optional
from src.utils.errors import InvalidParamsError, InvalidCityError


def validate_city_name(city: str) -> str:
    """
    Validate city name for weather API calls.
    Prevents SQL injection and other malicious inputs.
    
    Args:
        city: City name to validate
        
    Returns:
        Validated and cleaned city name
        
    Raises:
        InvalidCityError: If city name is invalid
    """
    if not city:
        raise InvalidCityError("", "City name cannot be empty")
    
    # Remove leading/trailing whitespace
    city = city.strip()
    
    # Check length
    if len(city) < 2:
        raise InvalidCityError(city, "City name too short (minimum 2 characters)")
    
    if len(city) > 100:
        raise InvalidCityError(city, "City name too long (maximum 100 characters)")
    
    # Allow letters, spaces, hyphens, apostrophes, and common unicode characters
    # This covers cities like "São Paulo", "M'Sila", "Saint-Étienne"
    allowed_pattern = re.compile(r'^[\w\s\-\'\u00C0-\u017F]+$', re.UNICODE)
    
    if not allowed_pattern.match(city):
        raise InvalidCityError(
            city,
            "City name contains invalid characters (only letters, spaces, hyphens, apostrophes allowed)"
        )
    
    # Check for common SQL injection patterns
    sql_patterns = ['--', ';', '/*', '*/', 'xp_', 'sp_', 'exec', 'execute', 'drop', 'delete']
    city_lower = city.lower()
    
    for pattern in sql_patterns:
        if pattern in city_lower:
            raise InvalidCityError(city, "City name contains forbidden pattern")
    
    return city


def validate_file_path(
    filepath: str,
    allowed_directories: list,
    max_length: int = 4096
) -> Path:
    """
    Validate file path for security.
    Checks for path traversal, validates against allowlist.
    
    Args:
        filepath: Path to validate
        allowed_directories: List of allowed directory paths
        max_length: Maximum path length
        
    Returns:
        Validated Path object
        
    Raises:
        InvalidParamsError: If path is invalid or not allowed
    """
    if not filepath:
        raise InvalidParamsError("File path cannot be empty")
    
    # Check length
    if len(filepath) > max_length:
        raise InvalidParamsError(
            f"File path too long ({len(filepath)} chars, max {max_length})"
        )
    
    # Check for null bytes
    if '\x00' in filepath:
        raise InvalidParamsError("File path contains null bytes")
    
    # Check for path traversal sequences
    if '..' in filepath:
        raise InvalidParamsError("Path traversal detected: '..' not allowed in path")
    
    # Additional suspicious patterns
    suspicious_patterns = ['~/', '..\\', '%2e%2e', '..%2f', '..%5c']
    filepath_lower = filepath.lower()
    
    for pattern in suspicious_patterns:
        if pattern in filepath_lower:
            raise InvalidParamsError(f"Suspicious pattern detected in path: {pattern}")
    
    # Try to resolve path
    try:
        resolved_path = Path(filepath).resolve()
    except Exception as e:
        raise InvalidParamsError(f"Invalid file path: {str(e)}")
    
    # Check if path is within allowed directories
    is_allowed = False
    for allowed_dir in allowed_directories:
        try:
            resolved_path.relative_to(allowed_dir)
            is_allowed = True
            break
        except ValueError:
            continue
    
    if not is_allowed:
        allowed_dirs_str = ", ".join(str(d) for d in allowed_directories)
        raise InvalidParamsError(
            f"Path '{filepath}' is not within allowed directories: [{allowed_dirs_str}]"
        )
    
    return resolved_path


def validate_file_content(
    content: str,
    max_size_bytes: int
) -> str:
    """
    Validate file content before writing.
    
    Args:
        content: Content to validate
        max_size_bytes: Maximum allowed content size in bytes
        
    Returns:
        Validated content
        
    Raises:
        InvalidParamsError: If content is invalid or too large
    """
    if content is None:
        raise InvalidParamsError("File content cannot be None")
    
    # Check size
    content_bytes = len(content.encode('utf-8'))
    
    if content_bytes > max_size_bytes:
        max_mb = round(max_size_bytes / (1024 * 1024), 2)
        actual_mb = round(content_bytes / (1024 * 1024), 2)
        raise InvalidParamsError(
            f"Content too large ({actual_mb}MB, max {max_mb}MB)",
            data={'size_bytes': content_bytes, 'max_size_bytes': max_size_bytes}
        )
    
    return content


def validate_file_extension(
    filepath: str,
    allowed_extensions: list
) -> bool:
    """
    Validate file extension against allowlist.
    
    Args:
        filepath: Path to file
        allowed_extensions: List of allowed extensions (e.g., ['.txt', '.json'])
        
    Returns:
        True if extension is allowed
        
    Raises:
        InvalidParamsError: If extension is not allowed
    """
    path = Path(filepath)
    extension = path.suffix.lower()
    
    if not extension:
        raise InvalidParamsError(
            "File must have an extension",
            data={'filepath': filepath}
        )
    
    if extension not in [ext.lower() for ext in allowed_extensions]:
        allowed_exts_str = ", ".join(allowed_extensions)
        raise InvalidParamsError(
            f"File extension '{extension}' not allowed. Allowed: [{allowed_exts_str}]",
            data={'extension': extension, 'allowed_extensions': allowed_extensions}
        )
    
    return True


def validate_operation_type(
    operation: str,
    allowed_operations: list
) -> str:
    """
    Validate operation type.
    
    Args:
        operation: Operation to validate
        allowed_operations: List of allowed operations
        
    Returns:
        Validated operation (lowercase)
        
    Raises:
        InvalidParamsError: If operation is not allowed
    """
    if not operation:
        raise InvalidParamsError("Operation cannot be empty")
    
    operation = operation.lower().strip()
    
    if operation not in [op.lower() for op in allowed_operations]:
        allowed_ops_str = ", ".join(allowed_operations)
        raise InvalidParamsError(
            f"Invalid operation '{operation}'. Allowed: [{allowed_ops_str}]",
            data={'operation': operation, 'allowed_operations': allowed_operations}
        )
    
    return operation


def validate_request_id(request_id: Optional[str]) -> Optional[str]:
    """
    Validate JSON-RPC request ID.
    
    Args:
        request_id: Request ID to validate
        
    Returns:
        Validated request ID
        
    Raises:
        InvalidParamsError: If request ID format is invalid
    """
    if request_id is None:
        return None
    
    # Request ID should be string or number
    if not isinstance(request_id, (str, int, float)):
        raise InvalidParamsError(
            "Request ID must be a string, number, or null",
            data={'request_id_type': type(request_id).__name__}
        )
    
    # If string, check length
    if isinstance(request_id, str):
        if len(request_id) > 256:
            raise InvalidParamsError("Request ID too long (max 256 characters)")
        
        # Check for control characters
        if any(ord(c) < 32 for c in request_id if c != '\t'):
            raise InvalidParamsError("Request ID contains invalid control characters")
    
    return str(request_id)


def sanitize_log_message(message: str) -> str:
    """
    Sanitize message before logging to prevent log injection.
    
    Args:
        message: Message to sanitize
        
    Returns:
        Sanitized message
    """
    if not message:
        return ""
    
    # Remove control characters except tab and newline
    sanitized = ''.join(c for c in message if ord(c) >= 32 or c in '\t\n')
    
    # Limit length
    max_length = 10000
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "... (truncated)"
    
    return sanitized


def validate_json_rpc_request(request: dict) -> bool:
    """
    Validate JSON-RPC 2.0 request format.
    
    Args:
        request: Request dictionary to validate
        
    Returns:
        True if valid
        
    Raises:
        InvalidParamsError: If request format is invalid
    """
    # Check required fields
    if not isinstance(request, dict):
        raise InvalidParamsError("Request must be a JSON object")
    
    if request.get('jsonrpc') != '2.0':
        raise InvalidParamsError("Request must have 'jsonrpc': '2.0'")
    
    if 'method' not in request:
        raise InvalidParamsError("Request must have 'method' field")
    
    if not isinstance(request['method'], str):
        raise InvalidParamsError("Method must be a string")
    
    # Validate params if present
    if 'params' in request:
        if not isinstance(request['params'], (dict, list)):
            raise InvalidParamsError("Params must be an object or array")
    
    # Validate id if present (can be string, number, or null)
    if 'id' in request:
        validate_request_id(request['id'])
    
    return True
