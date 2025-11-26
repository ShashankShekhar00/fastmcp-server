"""
Configuration loader with validation for MCP server.
Loads all environment variables and validates required settings.
"""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""
    pass


class Config:
    """Application configuration loaded from environment variables."""
    
    def __init__(self):
        """Initialize configuration by loading and validating environment variables."""
        load_dotenv()
        self._validate_and_load()
    
    def _validate_and_load(self):
        """Load and validate all required environment variables."""
        
        # OAuth 2.0 Configuration (Auth0)
        self.OAUTH_DOMAIN = self._get_required("OAUTH_DOMAIN")
        self.OAUTH_AUDIENCE = self._get_required("OAUTH_AUDIENCE")
        self.OAUTH_CLIENT_ID = self._get_required("OAUTH_CLIENT_ID")
        self.OAUTH_CLIENT_SECRET = self._get_required("OAUTH_CLIENT_SECRET")
        self.OAUTH_TOKEN_URL = self._get_required("OAUTH_TOKEN_URL")
        self.OAUTH_JWKS_URL = self._get_required("OAUTH_JWKS_URL")
        self.OAUTH_ALGORITHMS = os.getenv("OAUTH_ALGORITHMS", "RS256")
        self.OAUTH_ISSUER = self._get_required("OAUTH_ISSUER")
        
        # OAuth 2.1 Security Settings
        self.OAUTH_ACCESS_TOKEN_EXPIRY = int(os.getenv("OAUTH_ACCESS_TOKEN_EXPIRY", "900"))
        self.OAUTH_REFRESH_TOKEN_EXPIRY = int(os.getenv("OAUTH_REFRESH_TOKEN_EXPIRY", "604800"))
        self.OAUTH_REQUIRE_PKCE = os.getenv("OAUTH_REQUIRE_PKCE", "true").lower() == "true"
        self.OAUTH_ALLOW_IMPLICIT = os.getenv("OAUTH_ALLOW_IMPLICIT", "false").lower() == "true"
        
        # OpenWeatherMap API
        self.OPENWEATHER_API_KEY = self._get_required("OPENWEATHER_API_KEY")
        self.OPENWEATHER_BASE_URL = os.getenv(
            "OPENWEATHER_BASE_URL", 
            "https://api.openweathermap.org/data/2.5"
        )
        self.OPENWEATHER_TIMEOUT = int(os.getenv("OPENWEATHER_TIMEOUT", "10"))
        
        # File Operations Security
        allowed_paths_str = self._get_required("ALLOWED_FILE_PATHS")
        self.ALLOWED_FILE_PATHS = self._parse_paths(allowed_paths_str)
        self.MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
        self.MAX_FILE_SIZE_BYTES = self.MAX_FILE_SIZE_MB * 1024 * 1024
        
        extensions_str = os.getenv("ALLOWED_FILE_EXTENSIONS", ".txt,.json,.csv,.md")
        self.ALLOWED_FILE_EXTENSIONS = [ext.strip() for ext in extensions_str.split(",")]
        
        # Server Configuration
        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.PORT = int(os.getenv("PORT", "8000"))
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
        
        cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000")
        self.CORS_ORIGINS = [origin.strip() for origin in cors_origins_str.split(",")]
        
        # FastMCP Transport
        self.TRANSPORT_MODE = os.getenv("TRANSPORT_MODE", "sse")
        
        # Rate Limiting
        self.RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "3600"))
        
        # Security
        self.SECRET_KEY = self._get_required("SECRET_KEY")
        self.HTTPS_ONLY = os.getenv("HTTPS_ONLY", "false").lower() == "true"
        
        # Database Configuration
        self.DATABASE_URL = os.getenv(
            "DATABASE_URL",
            "sqlite:///./mcp_server.db"  # Default to SQLite
        )
        self.DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"
        
        # User Data Storage
        self.USER_DATA_DIR = os.getenv("USER_DATA_DIR", "user_data")
    
    def _get_required(self, key: str) -> str:
        """
        Get required environment variable or raise ConfigurationError.
        
        Args:
            key: Environment variable name
            
        Returns:
            Value of the environment variable
            
        Raises:
            ConfigurationError: If the variable is not set or is empty
        """
        value = os.getenv(key)
        if not value or value.startswith("your_") or value == "generate-random-64-char-string-here":
            raise ConfigurationError(
                f"Required environment variable '{key}' is not properly set. "
                f"Please check your .env file and update with real values."
            )
        return value
    
    def _parse_paths(self, paths_string: str) -> List[Path]:
        """
        Parse comma-separated directory paths and validate them.
        
        Args:
            paths_string: Comma-separated list of directory paths
            
        Returns:
            List of resolved Path objects
            
        Raises:
            ConfigurationError: If no valid paths found
        """
        paths = []
        for path_str in paths_string.split(','):
            path_str = path_str.strip()
            if not path_str:
                continue
            
            path = Path(path_str).resolve()
            paths.append(path)
        
        if not paths:
            raise ConfigurationError(
                "ALLOWED_FILE_PATHS must contain at least one valid directory path"
            )
        
        return paths
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"
    
    def validate_file_path(self, requested_path: str) -> Path:
        """
        Validate that requested path is within allowed directories.
        Prevents path traversal attacks.
        
        Args:
            requested_path: Path requested by user/tool
            
        Returns:
            Resolved Path object if valid
            
        Raises:
            ValueError: If path is not within allowed directories or contains traversal sequences
        """
        # Check for path traversal sequences
        if ".." in requested_path:
            raise ValueError(
                f"Path traversal detected: '{requested_path}' contains '..' sequence"
            )
        
        # Resolve to absolute path
        try:
            requested = Path(requested_path).resolve()
        except Exception as e:
            raise ValueError(f"Invalid path '{requested_path}': {str(e)}")
        
        # Check if path is within any allowed directory
        for allowed_dir in self.ALLOWED_FILE_PATHS:
            try:
                # Check if requested path is relative to allowed directory
                requested.relative_to(allowed_dir)
                return requested
            except ValueError:
                # Not relative to this allowed directory, try next
                continue
        
        # Path not in any allowed directory
        allowed_dirs_str = ", ".join(str(d) for d in self.ALLOWED_FILE_PATHS)
        raise ValueError(
            f"Path '{requested_path}' is not within allowed directories. "
            f"Allowed: [{allowed_dirs_str}]"
        )
    
    def validate_file_extension(self, filepath: str) -> bool:
        """
        Check if file extension is allowed.
        
        Args:
            filepath: Path to file
            
        Returns:
            True if extension is allowed
            
        Raises:
            ValueError: If extension is not allowed
        """
        path = Path(filepath)
        extension = path.suffix.lower()
        
        if extension not in self.ALLOWED_FILE_EXTENSIONS:
            allowed_exts_str = ", ".join(self.ALLOWED_FILE_EXTENSIONS)
            raise ValueError(
                f"File extension '{extension}' is not allowed. "
                f"Allowed extensions: [{allowed_exts_str}]"
            )
        
        return True


# Global configuration instance
# Import this in other modules: from src.config import config
try:
    config = Config()
except ConfigurationError as e:
    # In development, we might not have all credentials yet
    # Print error but allow import
    print(f"⚠️  Configuration Warning: {e}")
    print("💡 Update your .env file with real credentials before running the server")
    config = None
