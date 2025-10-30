"""
Authentication middleware for FastAPI/Starlette.

Validates JWT tokens in Authorization header and blocks unauthorized requests.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from typing import Callable
import logging

from ..auth.jwt_validator import JWTValidator
from ..utils.errors import (
    AuthenticationError,
    TokenExpiredError,
    InvalidTokenError,
    JWKSFetchError
)

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate JWT tokens on incoming requests.
    
    Extracts and validates Authorization header, blocks unauthorized requests,
    and adds user info to request state for downstream handlers.
    """
    
    def __init__(self, app, jwt_validator: JWTValidator, exempt_paths: list[str] = None):
        """
        Initialize authentication middleware.
        
        Args:
            app: ASGI application
            jwt_validator: JWTValidator instance
            exempt_paths: List of paths that don't require authentication
        """
        super().__init__(app)
        self.jwt_validator = jwt_validator
        self.exempt_paths = exempt_paths or ["/health", "/docs", "/openapi.json"]
        
        logger.info(f"Auth middleware initialized - Exempt paths: {self.exempt_paths}")
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process incoming request and validate authentication.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response from next handler or 401/403 error
        """
        path = request.url.path
        
        # Skip authentication for exempt paths
        if path in self.exempt_paths:
            logger.debug(f"Skipping auth for exempt path: {path}")
            return await call_next(request)
        
        # Extract token from Authorization header or query parameter (for SSE)
        auth_header = request.headers.get("Authorization")
        token = None
        
        if auth_header:
            # Validate token format
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
        elif path.startswith("/stream/"):
            # For SSE endpoints, also check query parameter
            token = request.query_params.get("token")
        
        if not token:
            logger.warning(f"Missing or invalid Authorization - Path: {path}, IP: {request.client.host}")
            return JSONResponse(
                status_code=401,
                content={
                    "error": "unauthorized",
                    "message": "Missing or invalid authorization",
                    "details": "Please provide a valid JWT token in the Authorization header or token query parameter"
                }
            )
        
        # Validate JWT token
        try:
            token_data = self.jwt_validator.validate_token(token)
            
            # Add user info to request state (accessible in route handlers)
            request.state.user_id = token_data["user_id"]
            request.state.scopes = token_data["scopes"]
            request.state.token_payload = token_data["payload"]
            
            logger.info(
                f"Request authenticated - User: {token_data['user_id']}, "
                f"Path: {path}, Method: {request.method}"
            )
            
            # Continue to next handler
            response = await call_next(request)
            return response
        
        except TokenExpiredError as e:
            logger.warning(f"Token expired - Path: {path}")
            return JSONResponse(
                status_code=401,
                content={
                    "error": "token_expired",
                    "message": str(e),
                    "details": "Please obtain a new access token"
                }
            )
        
        except InvalidTokenError as e:
            logger.warning(f"Invalid token - Path: {path}, Error: {e}")
            return JSONResponse(
                status_code=401,
                content={
                    "error": "invalid_token",
                    "message": str(e),
                    "details": "Token validation failed"
                }
            )
        
        except JWKSFetchError as e:
            logger.error(f"JWKS fetch error - Path: {path}, Error: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "error": "service_unavailable",
                    "message": "Unable to validate token",
                    "details": "Authentication service temporarily unavailable"
                }
            )
        
        except AuthenticationError as e:
            logger.warning(f"Authentication error - Path: {path}, Error: {e}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": "forbidden",
                    "message": str(e),
                    "details": "Token validation failed"
                }
            )
        
        except Exception as e:
            logger.error(f"Unexpected auth error - Path: {path}, Error: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_error",
                    "message": "An unexpected error occurred during authentication",
                    "details": str(e)
                }
            )


def require_scopes(*required_scopes: str):
    """
    Decorator to require specific scopes for a route handler.
    
    Usage:
        @app.get("/admin")
        @require_scopes("admin:read", "admin:write")
        async def admin_endpoint(request: Request):
            ...
    
    Args:
        required_scopes: Scopes required to access the endpoint
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            user_scopes = getattr(request.state, "scopes", [])
            
            missing_scopes = [scope for scope in required_scopes if scope not in user_scopes]
            
            if missing_scopes:
                logger.warning(
                    f"Insufficient scopes - User: {request.state.user_id}, "
                    f"Required: {required_scopes}, Has: {user_scopes}"
                )
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "insufficient_scope",
                        "message": "Insufficient permissions to access this resource",
                        "details": f"Required scopes: {', '.join(required_scopes)}"
                    }
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator
