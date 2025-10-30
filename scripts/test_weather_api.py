"""
Quick test script to verify OpenWeatherMap API key is working.
Run this after your API key is activated (wait ~2 hours after signup).
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

def test_openweather_api():
    """Test if OpenWeatherMap API key is working."""
    
    api_key = os.getenv("OPENWEATHER_API_KEY")
    base_url = os.getenv("OPENWEATHER_BASE_URL", "https://api.openweathermap.org/data/2.5")
    
    if not api_key or api_key == "your_api_key_here":
        print("❌ Error: OPENWEATHER_API_KEY not set in .env file")
        print("💡 Please add your API key to the .env file")
        return False
    
    print(f"🔑 API Key: {api_key[:8]}...{api_key[-4:]} (masked for security)")
    print(f"🌐 Base URL: {base_url}")
    print(f"🧪 Testing with city: London\n")
    
    # Test API call
    url = f"{base_url}/weather"
    params = {
        "q": "London",
        "appid": api_key,
        "units": "metric"
    }
    
    try:
        print("📡 Sending request to OpenWeatherMap...")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS! API key is working!\n")
            print(f"📍 City: {data['name']}, {data['sys']['country']}")
            print(f"🌡️  Temperature: {data['main']['temp']}°C")
            print(f"💧 Humidity: {data['main']['humidity']}%")
            print(f"☁️  Description: {data['weather'][0]['description']}")
            print(f"💨 Wind Speed: {data['wind']['speed']} m/s")
            return True
        
        elif response.status_code == 401:
            print("❌ FAILED: Invalid API key (401 Unauthorized)")
            print("💡 Your API key may not be activated yet (wait ~2 hours)")
            print("💡 Or check if you copied it correctly to .env")
            return False
        
        elif response.status_code == 429:
            print("❌ FAILED: Rate limit exceeded (429)")
            print("💡 You've made too many requests. Wait a bit and try again.")
            return False
        
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    except requests.Timeout:
        print("❌ FAILED: Request timed out")
        print("💡 Check your internet connection")
        return False
    
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("OpenWeatherMap API Key Test")
    print("=" * 60 + "\n")
    
    success = test_openweather_api()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Your OpenWeatherMap integration is ready!")
        print("✅ The weather tool in your MCP server will work!")
    else:
        print("❌ Setup incomplete - follow the suggestions above")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
