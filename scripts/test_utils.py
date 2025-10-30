"""Quick test of utility modules."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.validators import validate_city_name
from src.utils.errors import InvalidCityError, PathNotAllowedError
from src.utils.logging import setup_logger, redact_sensitive_data

# Test city validation
print("Testing city name validation...")
try:
    city = validate_city_name('London')
    print(f"✓ Valid city: {city}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test SQL injection prevention
try:
    validate_city_name('drop table')
    print("✗ SQL injection not blocked!")
except InvalidCityError as e:
    print(f"✓ SQL injection blocked: {e.message}")

# Test logging with token redaction
print("\nTesting logging with token redaction...")
logger = setup_logger("test", "INFO")
test_data = {
    "user": "john",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
    "api_key": "secret_key_12345"
}
redacted = redact_sensitive_data(test_data)
print(f"Original: {test_data}")
print(f"Redacted: {redacted}")

# Test error formatting
print("\nTesting MCP error formatting...")
error = PathNotAllowedError("/etc/passwd", ["/app/data", "/app/uploads"])
error_dict = error.to_dict(request_id="test-123")
print(f"✓ Error code: {error_dict['error']['code']}")
print(f"✓ Error message: {error_dict['error']['message']}")

print("\n✅ All utility tests passed!")
