"""
Example: Using MCP tools directly in Python
"""
import sys
sys.path.insert(0, 'c:/Users/KIIT/Desktop/fastmcp-server')

from src.config import config
from src.tools.file_operations import create_file_operations_tool
from src.tools.weather import create_weather_tool

# Initialize tools
file_tool = create_file_operations_tool(config)
weather_tool = create_weather_tool(config)

# Example 1: Get weather data
print("=" * 50)
print("Getting weather for London...")
print("=" * 50)
weather_result = weather_tool.execute(city="London")
print(f"Temperature: {weather_result['temperature_celsius']}°C")
print(f"Description: {weather_result['description']}")
print(f"Humidity: {weather_result['humidity_percent']}%")

# Example 2: Write a file
print("\n" + "=" * 50)
print("Writing a file...")
print("=" * 50)
write_result = file_tool.execute(
    operation="write",
    filepath="test_output/my_data.txt",
    content="Hello from local Python script!"
)
print(f"Status: {write_result['status']}")
print(f"Path: {write_result['path']}")

# Example 3: Read the file back
print("\n" + "=" * 50)
print("Reading the file...")
print("=" * 50)
read_result = file_tool.execute(
    operation="read",
    filepath="test_output/my_data.txt"
)
print(f"Content: {read_result['content']}")
print(f"Size: {read_result['size_bytes']} bytes")

print("\n✅ All operations completed successfully!")
