"""
MCP-compliant error classes and error response formatting.
Implements JSON-RPC 2.0 error codes per MCP specification.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone


class MCPError(Exception):
    """
    Base class for all MCP errors.
    Follows JSON-RPC 2.0 error response format.
    """
    
    # JSON-RPC 2.0 standard error codes
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # Custom MCP error codes (start at -32000)
    UNAUTHORIZED = -32000
    FORBIDDEN = -32001
    PATH_NOT_ALLOWED = -32002
    FILE_NOT_FOUND = -32003
    PERMISSION_DENIED = -32004
    FILE_TOO_LARGE = -32005
    INVALID_EXTENSION = -32006
    DISK_FULL = -32007
    INVALID_CITY = -32008
    CITY_NOT_FOUND = -32009
    API_TIMEOUT = -32010
    API_RATE_LIMIT = -32011
    API_AUTHENTICATION_FAILED = -32012
    NETWORK_ERROR = -32013
    
    def __init__(
        self, 
        code: int, 
        message: str, 
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize MCP error.
        
        Args:
            code: JSON-RPC error code
            message: Human-readable error message
            data: Optional additional error details
        """
        self.code = code
        self.message = message
        self.data = data or {}
        self.data['timestamp'] = datetime.now(timezone.utc).isoformat()
        super().__init__(message)
    
    def to_dict(self, request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert error to JSON-RPC 2.0 error response format.
        
        Args:
            request_id: Request ID from original request
            
        Returns:
            Dictionary formatted per JSON-RPC 2.0 spec
        """
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": self.code,
                "message": self.message,
                "data": self.data
            },
            "id": request_id
        }


class ParseError(MCPError):
    """Invalid JSON received by the server."""
    
    def __init__(self, message: str = "Parse error", data: Optional[Dict] = None):
        super().__init__(MCPError.PARSE_ERROR, message, data)


class InvalidRequestError(MCPError):
    """The JSON sent is not a valid Request object."""
    
    def __init__(self, message: str = "Invalid request", data: Optional[Dict] = None):
        super().__init__(MCPError.INVALID_REQUEST, message, data)


class MethodNotFoundError(MCPError):
    """The method does not exist or is not available."""
    
    def __init__(self, method: str, data: Optional[Dict] = None):
        message = f"Method '{method}' not found"
        data = data or {}
        data['method'] = method
        super().__init__(MCPError.METHOD_NOT_FOUND, message, data)


class InvalidParamsError(MCPError):
    """Invalid method parameters."""
    
    def __init__(self, message: str = "Invalid parameters", data: Optional[Dict] = None):
        super().__init__(MCPError.INVALID_PARAMS, message, data)


class InternalError(MCPError):
    """Internal JSON-RPC error."""
    
    def __init__(self, message: str = "Internal error", data: Optional[Dict] = None):
        super().__init__(MCPError.INTERNAL_ERROR, message, data)


# File Operations Errors

class PathNotAllowedError(MCPError):
    """Path is not in the allowlist."""
    
    def __init__(self, path: str, allowed_dirs: list, data: Optional[Dict] = None):
        message = f"Path not in allowlist: {path}"
        data = data or {}
        data.update({
            'requested_path': path,
            'allowed_directories': allowed_dirs
        })
        super().__init__(MCPError.PATH_NOT_ALLOWED, message, data)


class FileNotFoundError(MCPError):
    """File does not exist at the specified path."""
    
    def __init__(self, filepath: str, data: Optional[Dict] = None):
        message = f"File not found: {filepath}"
        data = data or {}
        data['filepath'] = filepath
        super().__init__(MCPError.FILE_NOT_FOUND, message, data)


class PermissionDeniedError(MCPError):
    """Insufficient permissions to access the file."""
    
    def __init__(self, filepath: str, operation: str, data: Optional[Dict] = None):
        message = f"Permission denied: cannot {operation} {filepath}"
        data = data or {}
        data.update({
            'filepath': filepath,
            'operation': operation
        })
        super().__init__(MCPError.PERMISSION_DENIED, message, data)


class FileTooLargeError(MCPError):
    """File exceeds maximum allowed size."""
    
    def __init__(self, size_bytes: int, max_size_bytes: int, data: Optional[Dict] = None):
        message = f"File too large: {size_bytes} bytes (max: {max_size_bytes} bytes)"
        data = data or {}
        data.update({
            'size_bytes': size_bytes,
            'max_size_bytes': max_size_bytes,
            'size_mb': round(size_bytes / (1024 * 1024), 2),
            'max_size_mb': round(max_size_bytes / (1024 * 1024), 2)
        })
        super().__init__(MCPError.FILE_TOO_LARGE, message, data)


class InvalidExtensionError(MCPError):
    """File extension is not allowed."""
    
    def __init__(self, extension: str, allowed_extensions: list, data: Optional[Dict] = None):
        message = f"Invalid file extension: {extension}"
        data = data or {}
        data.update({
            'extension': extension,
            'allowed_extensions': allowed_extensions
        })
        super().__init__(MCPError.INVALID_EXTENSION, message, data)


class DiskFullError(MCPError):
    """Unable to write due to insufficient disk space."""
    
    def __init__(self, message: str = "Disk full", data: Optional[Dict] = None):
        super().__init__(MCPError.DISK_FULL, message, data)


# Weather Tool Errors

class InvalidCityError(MCPError):
    """Invalid city name provided."""
    
    def __init__(self, city: str, reason: str = "Invalid format", data: Optional[Dict] = None):
        message = f"Invalid city name: {city} ({reason})"
        data = data or {}
        data.update({
            'city': city,
            'reason': reason
        })
        super().__init__(MCPError.INVALID_CITY, message, data)


class CityNotFoundError(MCPError):
    """City not found in weather API."""
    
    def __init__(self, city: str, data: Optional[Dict] = None):
        message = f"City not found: {city}"
        data = data or {}
        data['city'] = city
        super().__init__(MCPError.CITY_NOT_FOUND, message, data)


class APITimeoutError(MCPError):
    """External API request timed out."""
    
    def __init__(self, api: str, timeout_seconds: int, data: Optional[Dict] = None):
        message = f"{api} API timeout after {timeout_seconds} seconds"
        data = data or {}
        data.update({
            'api': api,
            'timeout_seconds': timeout_seconds
        })
        super().__init__(MCPError.API_TIMEOUT, message, data)


class APIRateLimitError(MCPError):
    """API rate limit exceeded."""
    
    def __init__(self, api: str, retry_after: Optional[int] = None, data: Optional[Dict] = None):
        message = f"{api} API rate limit exceeded"
        data = data or {}
        data['api'] = api
        if retry_after:
            data['retry_after_seconds'] = retry_after
            message += f" (retry after {retry_after}s)"
        super().__init__(MCPError.API_RATE_LIMIT, message, data)


class APIAuthenticationError(MCPError):
    """API authentication failed."""
    
    def __init__(self, api: str, data: Optional[Dict] = None):
        message = f"{api} API authentication failed"
        data = data or {}
        data['api'] = api
        super().__init__(MCPError.API_AUTHENTICATION_FAILED, message, data)


class NetworkError(MCPError):
    """Network connection error."""
    
    def __init__(self, message: str = "Network error", data: Optional[Dict] = None):
        super().__init__(MCPError.NETWORK_ERROR, message, data)


# OAuth Errors (use HTTP status code style)

class UnauthorizedError(MCPError):
    """Authentication required or token invalid."""
    
    def __init__(self, message: str = "Unauthorized", data: Optional[Dict] = None):
        super().__init__(MCPError.UNAUTHORIZED, message, data)


class ForbiddenError(MCPError):
    """Valid authentication but insufficient permissions."""
    
    def __init__(self, message: str = "Forbidden", data: Optional[Dict] = None):
        super().__init__(MCPError.FORBIDDEN, message, data)


# JWT/Auth specific errors

class AuthenticationError(MCPError):
    """General authentication error."""
    
    def __init__(self, message: str = "Authentication failed", data: Optional[Dict] = None):
        super().__init__(MCPError.UNAUTHORIZED, message, data)


class TokenExpiredError(MCPError):
    """JWT token has expired."""
    
    def __init__(self, message: str = "Token has expired", data: Optional[Dict] = None):
        super().__init__(MCPError.UNAUTHORIZED, message, data)


class InvalidTokenError(MCPError):
    """JWT token is invalid or malformed."""
    
    def __init__(self, message: str = "Invalid token", data: Optional[Dict] = None):
        super().__init__(MCPError.UNAUTHORIZED, message, data)


class JWKSFetchError(MCPError):
    """Failed to fetch JWKS keys from Auth0."""
    
    def __init__(self, message: str = "Failed to fetch JWKS keys", data: Optional[Dict] = None):
        super().__init__(MCPError.API_AUTHENTICATION_FAILED, message, data)


def format_success_response(result: Any, request_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Format successful tool execution response per JSON-RPC 2.0 spec.
    
    Args:
        result: Tool execution result
        request_id: Request ID from original request
        
    Returns:
        Dictionary formatted per JSON-RPC 2.0 spec
    """
    return {
        "jsonrpc": "2.0",
        "result": result,
        "id": request_id
    }


# Database Errors

class DatabaseError(MCPError):
    """General database error."""
    
    def __init__(self, message: str = "Database error", data: Optional[Dict] = None):
        super().__init__(MCPError.INTERNAL_ERROR, message, data)


class ResourceNotFoundError(MCPError):
    """Requested resource not found in database."""
    
    def __init__(self, resource_type: str, resource_id: Any, data: Optional[Dict] = None):
        message = f"{resource_type} not found: {resource_id}"
        data = data or {}
        data.update({
            'resource_type': resource_type,
            'resource_id': str(resource_id)
        })
        super().__init__(MCPError.FILE_NOT_FOUND, message, data)


class DuplicateResourceError(MCPError):
    """Resource already exists."""
    
    def __init__(self, resource_type: str, message: str = None, data: Optional[Dict] = None):
        if not message:
            message = f"{resource_type} already exists"
        data = data or {}
        data['resource_type'] = resource_type
        super().__init__(MCPError.INVALID_PARAMS, message, data)


class ValidationError(MCPError):
    """Data validation failed."""
    
    def __init__(self, message: str, errors: Optional[list] = None, data: Optional[Dict] = None):
        data = data or {}
        if errors:
            data['validation_errors'] = errors
        super().__init__(MCPError.INVALID_PARAMS, message, data)

