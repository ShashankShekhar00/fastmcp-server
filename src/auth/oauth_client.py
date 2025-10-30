"""
OAuth 2.0 client for obtaining access tokens from Auth0.

This module is used for testing and client applications that need to
authenticate with the MCP server.
"""

import requests
from typing import Dict, Optional
import logging
from datetime import datetime, timezone

from ..utils.errors import AuthenticationError, APITimeoutError

logger = logging.getLogger(__name__)


class OAuthClient:
    """
    OAuth 2.0 client for Auth0 authentication.
    
    Handles client credentials flow to obtain access tokens.
    """
    
    def __init__(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        audience: str,
        timeout: int = 10
    ):
        """
        Initialize OAuth client.
        
        Args:
            token_url: Auth0 token endpoint
            client_id: Application client ID
            client_secret: Application client secret
            audience: API identifier (audience)
            timeout: Request timeout in seconds
        """
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.audience = audience
        self.timeout = timeout
        
        # Cache for access token
        self._cached_token: Optional[str] = None
        self._token_expires_at: Optional[int] = None
        
        logger.info(f"OAuth client initialized - Audience: {audience}")
    
    def get_access_token(self, force_refresh: bool = False) -> str:
        """
        Get access token using client credentials flow.
        
        Uses cached token if available and not expired.
        
        Args:
            force_refresh: Force fetching new token even if cached token valid
            
        Returns:
            Access token string
            
        Raises:
            AuthenticationError: If authentication fails
            APITimeoutError: If request times out
        """
        # Check if cached token is still valid
        if not force_refresh and self._cached_token and self._token_expires_at:
            current_time = int(datetime.now(timezone.utc).timestamp())
            # Add 60 second buffer before expiration
            if current_time < (self._token_expires_at - 60):
                logger.debug("Using cached access token")
                return self._cached_token
        
        # Fetch new token
        logger.info("Fetching new access token from Auth0")
        
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "audience": self.audience
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                self.token_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)  # Default 1 hour
                
                # Cache token
                self._cached_token = access_token
                self._token_expires_at = int(datetime.now(timezone.utc).timestamp()) + expires_in
                
                logger.info(f"Access token obtained - Expires in {expires_in} seconds")
                return access_token
            
            elif response.status_code == 401:
                logger.error("Authentication failed - Invalid credentials")
                raise AuthenticationError(
                    "Invalid client credentials. Check OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET"
                )
            
            elif response.status_code == 403:
                logger.error("Authorization failed - Insufficient permissions")
                raise AuthenticationError(
                    "Client not authorized to access this API. Check Auth0 application permissions"
                )
            
            else:
                logger.error(f"Token request failed - HTTP {response.status_code}: {response.text}")
                raise AuthenticationError(
                    f"Failed to obtain access token: {response.status_code} - {response.text}"
                )
        
        except requests.Timeout:
            logger.error("Token request timed out")
            raise APITimeoutError(f"Auth0 token request timed out after {self.timeout} seconds")
        
        except requests.RequestException as e:
            logger.error(f"Token request failed: {e}")
            raise AuthenticationError(f"Failed to connect to Auth0: {str(e)}")
    
    def clear_cache(self):
        """Clear cached access token."""
        self._cached_token = None
        self._token_expires_at = None
        logger.debug("Token cache cleared")
    
    def get_token_info(self) -> Dict[str, any]:
        """
        Get information about cached token.
        
        Returns:
            Dict with token status and expiration info
        """
        if not self._cached_token:
            return {"cached": False}
        
        current_time = int(datetime.now(timezone.utc).timestamp())
        is_valid = current_time < (self._token_expires_at - 60)
        seconds_until_expiry = self._token_expires_at - current_time if self._token_expires_at else 0
        
        return {
            "cached": True,
            "valid": is_valid,
            "expires_at": self._token_expires_at,
            "seconds_until_expiry": seconds_until_expiry
        }
