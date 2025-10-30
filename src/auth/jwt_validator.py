"""
JWT token validation using Auth0 JWKS.

This module handles:
- Fetching public keys from Auth0's JWKS endpoint
- Decoding and verifying JWT tokens
- Validating token expiration, audience, and issuer
- Extracting user information and scopes
"""

import requests
from jose import jwt, JWTError, jwk
from jose.exceptions import ExpiredSignatureError, JWTClaimsError
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging

from ..utils.errors import (
    AuthenticationError,
    TokenExpiredError,
    InvalidTokenError,
    JWKSFetchError
)

logger = logging.getLogger(__name__)


class JWTValidator:
    """
    Validates JWT tokens issued by Auth0.
    
    Uses JWKS (JSON Web Key Set) to fetch public keys for signature verification.
    Validates token claims including expiration, audience, and issuer.
    """
    
    def __init__(
        self,
        jwks_url: str,
        audience: str,
        issuer: str,
        algorithms: list[str] = None
    ):
        """
        Initialize JWT validator.
        
        Args:
            jwks_url: Auth0 JWKS endpoint URL
            audience: Expected audience (your API identifier)
            issuer: Expected issuer (Auth0 domain)
            algorithms: Allowed signing algorithms (default: ["RS256"])
        """
        self.jwks_url = jwks_url
        self.audience = audience
        self.issuer = issuer
        self.algorithms = algorithms or ["RS256"]
        self._jwks_cache: Optional[Dict[str, Any]] = None
        
        logger.info(
            f"JWT Validator initialized - Audience: {audience}, Issuer: {issuer}"
        )
    
    def _fetch_jwks(self) -> Dict[str, Any]:
        """
        Fetch JWKS (public keys) from Auth0.
        
        Returns:
            Dict containing JWKS keys
            
        Raises:
            JWKSFetchError: If fetching JWKS fails
        """
        try:
            logger.debug(f"Fetching JWKS from {self.jwks_url}")
            response = requests.get(self.jwks_url, timeout=10)
            response.raise_for_status()
            
            jwks = response.json()
            logger.info(f"JWKS fetched successfully - {len(jwks.get('keys', []))} keys found")
            return jwks
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            raise JWKSFetchError(f"Could not fetch JWKS from {self.jwks_url}: {str(e)}")
    
    def _get_signing_key(self, token: str) -> str:
        """
        Get the signing key for a JWT token.
        
        Extracts the 'kid' (key ID) from token header and finds matching
        public key in JWKS.
        
        Args:
            token: JWT token string
            
        Returns:
            PEM-formatted public key
            
        Raises:
            InvalidTokenError: If token header invalid or key not found
        """
        try:
            # Decode header without verification to get 'kid'
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            if not kid:
                raise InvalidTokenError("Token header missing 'kid' (key ID)")
            
            # Fetch JWKS (use cache if available)
            if not self._jwks_cache:
                self._jwks_cache = self._fetch_jwks()
            
            # Find matching key
            for key in self._jwks_cache.get("keys", []):
                if key.get("kid") == kid:
                    # Return the JWK key directly - python-jose handles conversion
                    return key
            
            # Key not found - try refreshing JWKS cache
            logger.warning(f"Key ID '{kid}' not found in cache, refreshing JWKS")
            self._jwks_cache = self._fetch_jwks()
            
            for key in self._jwks_cache.get("keys", []):
                if key.get("kid") == kid:
                    return key
            
            raise InvalidTokenError(f"Signing key with kid '{kid}' not found in JWKS")
            
        except JWTError as e:
            logger.error(f"Error decoding JWT header: {e}")
            raise InvalidTokenError(f"Invalid JWT token header: {str(e)}")
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token and return decoded payload.
        
        Performs complete validation:
        1. Fetches signing key from JWKS
        2. Verifies signature
        3. Checks expiration
        4. Validates audience and issuer
        
        Args:
            token: JWT token string
            
        Returns:
            Dict containing decoded token payload with user info and claims
            
        Raises:
            InvalidTokenError: If token format invalid or signature verification fails
            TokenExpiredError: If token has expired
            AuthenticationError: If audience/issuer validation fails
        """
        try:
            # Get signing key (JWK dict)
            signing_key = self._get_signing_key(token)
            
            # Decode and verify token using JWK directly
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=self.algorithms,
                audience=self.audience,
                issuer=self.issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True
                }
            )
            
            # Extract user info
            user_id = payload.get("sub")
            scopes = payload.get("scope", "").split() if payload.get("scope") else []
            exp = payload.get("exp", 0)
            
            logger.info(
                f"Token validated successfully - User: {user_id}, "
                f"Scopes: {scopes}, Expires: {datetime.fromtimestamp(exp, tz=timezone.utc) if exp else 'N/A'}"
            )
            
            return {
                "user_id": user_id,
                "scopes": scopes,
                "expires_at": exp,
                "payload": payload
            }
            
        except ExpiredSignatureError:
            logger.warning("Token validation failed - Token expired")
            raise TokenExpiredError("JWT token has expired")
            
        except JWTClaimsError as e:
            logger.warning(f"Token validation failed - Claims error: {e}")
            raise AuthenticationError(f"Invalid token claims: {str(e)}")
            
        except JWTError as e:
            logger.error(f"Token validation failed - JWT error: {e}")
            raise InvalidTokenError(f"Invalid JWT token: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error during token validation: {e}")
            raise AuthenticationError(f"Token validation error: {str(e)}")
    
    def validate_scopes(self, token_scopes: list[str], required_scopes: list[str]) -> bool:
        """
        Check if token has required scopes.
        
        Args:
            token_scopes: Scopes from decoded token
            required_scopes: Scopes required for the operation
            
        Returns:
            True if all required scopes are present, False otherwise
        """
        return all(scope in token_scopes for scope in required_scopes)
    
    def get_token_info(self, token: str) -> Dict[str, Any]:
        """
        Get token information without full validation (for debugging).
        
        Args:
            token: JWT token string
            
        Returns:
            Dict with token header and payload (unverified)
        """
        try:
            header = jwt.get_unverified_header(token)
            claims = jwt.get_unverified_claims(token)
            
            return {
                "header": header,
                "claims": claims,
                "expires_at": claims.get("exp"),
                "issued_at": claims.get("iat")
            }
        except JWTError as e:
            logger.error(f"Error getting token info: {e}")
            return {"error": str(e)}
