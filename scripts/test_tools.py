"""Test script for file operations and weather tools."""

import sys
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.tools.file_operations import FileOperationsTool
from src.tools.weather import WeatherTool
from src.utils.errors import (
    PathNotAllowedError,
    FileTooLargeError,
    InvalidCityError,
    MCPError
)

print("=" * 60)
print("Testing File Operations Tool")
print("=" * 60)

# Create temporary directory for testing
with tempfile.TemporaryDirectory() as temp_dir:
    temp_path = Path(temp_dir)
    
    # Initialize file operations tool
    file_tool = FileOperationsTool(
        allowed_directories=[temp_path],
        max_file_size_bytes=10 * 1024 * 1024,  # 10MB
        allowed_extensions=['.txt', '.json', '.csv', '.md']
    )
    
    # Test 1: Write a file
    print("\n1. Testing file write...")
    test_file = temp_path / "test.txt"
    try:
        result = file_tool.execute(
            operation='write',
            filepath=str(test_file),
            content="Hello, MCP Server!"
        )
        print(f"   ✓ Write successful: {result['bytes_written']} bytes written")
    except MCPError as e:
        print(f"   ✗ Write failed: {e.message}")
    
    # Test 2: Read the file back
    print("\n2. Testing file read...")
    try:
        result = file_tool.execute(
            operation='read',
            filepath=str(test_file)
        )
        print(f"   ✓ Read successful: '{result['content']}'")
        print(f"   ✓ File size: {result['metadata']['size_bytes']} bytes")
    except MCPError as e:
        print(f"   ✗ Read failed: {e.message}")
    
    # Test 3: Path traversal attempt (should fail)
    print("\n3. Testing path traversal protection...")
    try:
        result = file_tool.execute(
            operation='read',
            filepath='../../../etc/passwd'
        )
        print(f"   ✗ Path traversal NOT blocked! Security issue!")
    except PathNotAllowedError as e:
        print(f"   ✓ Path traversal blocked: {e.message}")
    
    # Test 4: Invalid extension (should fail)
    print("\n4. Testing extension validation...")
    try:
        result = file_tool.execute(
            operation='write',
            filepath=str(temp_path / "test.exe"),
            content="malicious content"
        )
        print(f"   ✗ Invalid extension NOT blocked!")
    except MCPError as e:
        print(f"   ✓ Invalid extension blocked: {e.message}")
    
    # Test 5: File size limit
    print("\n5. Testing file size limit...")
    try:
        large_content = "X" * (11 * 1024 * 1024)  # 11MB (exceeds 10MB limit)
        result = file_tool.execute(
            operation='write',
            filepath=str(temp_path / "large.txt"),
            content=large_content
        )
        print(f"   ✗ Size limit NOT enforced!")
    except FileTooLargeError as e:
        print(f"   ✓ Size limit enforced: {e.message}")

print("\n" + "=" * 60)
print("Testing Weather Tool")
print("=" * 60)

# Initialize weather tool with dummy credentials
weather_tool = WeatherTool(
    api_key="dummy_key_for_testing",
    base_url="https://api.openweathermap.org/data/2.5",
    timeout=5
)

# Test 1: Validate city name
print("\n1. Testing city name validation...")
try:
    result = weather_tool.execute(city="London")
    print(f"   ✓ Valid city name accepted (API call will fail with dummy key)")
except InvalidCityError as e:
    print(f"   ✗ Valid city rejected: {e.message}")
except MCPError as e:
    # Expected to fail with dummy API key
    print(f"   ✓ City validation passed (API error expected: {e.message})")

# Test 2: SQL injection attempt (should fail)
print("\n2. Testing SQL injection protection...")
try:
    result = weather_tool.execute(city="London; DROP TABLE users--")
    print(f"   ✗ SQL injection NOT blocked!")
except InvalidCityError as e:
    print(f"   ✓ SQL injection blocked: {e.message}")
except MCPError as e:
    print(f"   ✗ Unexpected error: {e.message}")

# Test 3: Empty city name (should fail)
print("\n3. Testing empty city name...")
try:
    result = weather_tool.execute(city="")
    print(f"   ✗ Empty city NOT blocked!")
except InvalidCityError as e:
    print(f"   ✓ Empty city blocked: {e.message}")

# Test 4: City name with special characters
print("\n4. Testing international city names...")
try:
    result = weather_tool.execute(city="São Paulo")
    print(f"   ✓ International city accepted (API call will fail with dummy key)")
except InvalidCityError as e:
    print(f"   ✗ Valid international city rejected: {e.message}")
except MCPError as e:
    print(f"   ✓ City validation passed (API error expected)")

print("\n" + "=" * 60)
print("✅ All tool tests completed!")
print("=" * 60)
print("\nNote: Weather API calls fail because we're using dummy credentials.")
print("Once you add real API keys to .env, the weather tool will work fully.")
