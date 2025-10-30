"""
File operations tool for MCP server.
Provides secure read and write operations within allowed directories.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from src.utils.errors import (
    PathNotAllowedError,
    FileNotFoundError as MCPFileNotFoundError,
    PermissionDeniedError,
    FileTooLargeError,
    InvalidExtensionError,
    DiskFullError,
    InvalidParamsError
)
from src.utils.validators import (
    validate_file_path,
    validate_file_content,
    validate_file_extension,
    validate_operation_type
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class FileOperationsTool:
    """
    Secure file operations tool with allowlist validation.
    Supports read and write operations only within allowed directories.
    """
    
    def __init__(
        self,
        allowed_directories: list,
        max_file_size_bytes: int,
        allowed_extensions: list
    ):
        """
        Initialize file operations tool.
        
        Args:
            allowed_directories: List of Path objects for allowed directories
            max_file_size_bytes: Maximum file size in bytes
            allowed_extensions: List of allowed file extensions
        """
        self.allowed_directories = allowed_directories
        self.max_file_size_bytes = max_file_size_bytes
        self.allowed_extensions = allowed_extensions
        
        logger.info(
            f"FileOperationsTool initialized with {len(allowed_directories)} allowed directories",
            extra={
                'allowed_directories': [str(d) for d in allowed_directories],
                'max_file_size_mb': round(max_file_size_bytes / (1024 * 1024), 2),
                'allowed_extensions': allowed_extensions
            }
        )
    
    def execute(
        self,
        operation: str,
        filepath: str,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute file operation.
        
        Args:
            operation: Operation type ('read' or 'write')
            filepath: Path to file
            content: Content to write (required for write operation)
            
        Returns:
            Dictionary with operation results
            
        Raises:
            Various MCPError subclasses for different failure scenarios
        """
        # Validate operation type
        operation = validate_operation_type(operation, ['read', 'write'])
        
        # Validate file path
        try:
            validated_path = validate_file_path(
                filepath,
                self.allowed_directories
            )
        except InvalidParamsError as e:
            # Convert to PathNotAllowedError for MCP compliance
            raise PathNotAllowedError(
                filepath,
                [str(d) for d in self.allowed_directories],
                data={'reason': str(e)}
            )
        
        # Validate file extension
        try:
            validate_file_extension(filepath, self.allowed_extensions)
        except InvalidParamsError as e:
            raise InvalidExtensionError(
                Path(filepath).suffix.lower(),
                self.allowed_extensions,
                data={'filepath': filepath}
            )
        
        # Execute operation
        if operation == 'read':
            return self._read_file(validated_path)
        elif operation == 'write':
            if content is None:
                raise InvalidParamsError(
                    "Content is required for write operation",
                    data={'operation': 'write', 'filepath': filepath}
                )
            return self._write_file(validated_path, content)
        else:
            raise InvalidParamsError(f"Unknown operation: {operation}")
    
    def _read_file(self, filepath: Path) -> Dict[str, Any]:
        """
        Read file content.
        
        Args:
            filepath: Validated path to file
            
        Returns:
            Dictionary with file content and metadata
            
        Raises:
            MCPFileNotFoundError: If file doesn't exist
            PermissionDeniedError: If file can't be read
            FileTooLargeError: If file exceeds size limit
        """
        # Check if file exists
        if not filepath.exists():
            raise MCPFileNotFoundError(
                str(filepath),
                data={'operation': 'read'}
            )
        
        # Check if it's a file (not directory)
        if not filepath.is_file():
            raise InvalidParamsError(
                f"Path is not a file: {filepath}",
                data={'filepath': str(filepath), 'is_directory': filepath.is_dir()}
            )
        
        # Check file size before reading
        try:
            file_size = filepath.stat().st_size
        except OSError as e:
            raise PermissionDeniedError(
                str(filepath),
                'read',
                data={'error': str(e)}
            )
        
        if file_size > self.max_file_size_bytes:
            raise FileTooLargeError(file_size, self.max_file_size_bytes)
        
        # Read file content
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except PermissionError:
            raise PermissionDeniedError(
                str(filepath),
                'read',
                data={'reason': 'Permission denied by OS'}
            )
        except UnicodeDecodeError as e:
            raise InvalidParamsError(
                f"File is not valid UTF-8: {filepath}",
                data={'error': str(e), 'filepath': str(filepath)}
            )
        except OSError as e:
            raise PermissionDeniedError(
                str(filepath),
                'read',
                data={'error': str(e)}
            )
        
        # Get file metadata
        stat = filepath.stat()
        modified_time = datetime.fromtimestamp(stat.st_mtime).isoformat() + 'Z'
        
        logger.info(
            f"File read successfully: {filepath}",
            extra={
                'operation': 'read',
                'filepath': str(filepath),
                'size_bytes': file_size,
                'size_kb': round(file_size / 1024, 2)
            }
        )
        
        return {
            'content': content,
            'metadata': {
                'filepath': str(filepath),
                'size_bytes': file_size,
                'modified_at': modified_time,
                'encoding': 'utf-8'
            }
        }
    
    def _write_file(self, filepath: Path, content: str) -> Dict[str, Any]:
        """
        Write content to file.
        
        Args:
            filepath: Validated path to file
            content: Content to write
            
        Returns:
            Dictionary with write operation results
            
        Raises:
            PermissionDeniedError: If file can't be written
            FileTooLargeError: If content exceeds size limit
            DiskFullError: If disk is full
        """
        # Validate content size
        try:
            validate_file_content(content, self.max_file_size_bytes)
        except InvalidParamsError as e:
            content_bytes = len(content.encode('utf-8'))
            raise FileTooLargeError(content_bytes, self.max_file_size_bytes)
        
        # Ensure parent directory exists
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise PermissionDeniedError(
                str(filepath.parent),
                'create directory',
                data={'filepath': str(filepath)}
            )
        except OSError as e:
            raise PermissionDeniedError(
                str(filepath.parent),
                'create directory',
                data={'error': str(e)}
            )
        
        # Write file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        except PermissionError:
            raise PermissionDeniedError(
                str(filepath),
                'write',
                data={'reason': 'Permission denied by OS'}
            )
        except OSError as e:
            # Check for disk full errors
            if 'No space left on device' in str(e) or 'disk full' in str(e).lower():
                raise DiskFullError(
                    f"Unable to write file: {str(e)}",
                    data={'filepath': str(filepath)}
                )
            raise PermissionDeniedError(
                str(filepath),
                'write',
                data={'error': str(e)}
            )
        
        # Get file info after write
        try:
            stat = filepath.stat()
            bytes_written = stat.st_size
        except OSError:
            bytes_written = len(content.encode('utf-8'))
        
        logger.info(
            f"File written successfully: {filepath}",
            extra={
                'operation': 'write',
                'filepath': str(filepath),
                'bytes_written': bytes_written,
                'size_kb': round(bytes_written / 1024, 2)
            }
        )
        
        return {
            'success': True,
            'filepath': str(filepath),
            'bytes_written': bytes_written,
            'size_kb': round(bytes_written / 1024, 2)
        }


def create_file_operations_tool(config) -> FileOperationsTool:
    """
    Factory function to create FileOperationsTool from config.
    
    Args:
        config: Configuration object with required settings
        
    Returns:
        Configured FileOperationsTool instance
    """
    return FileOperationsTool(
        allowed_directories=config.ALLOWED_FILE_PATHS,
        max_file_size_bytes=config.MAX_FILE_SIZE_BYTES,
        allowed_extensions=config.ALLOWED_FILE_EXTENSIONS
    )
