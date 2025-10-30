"""
Weather tool for MCP server.
Fetches current weather data from OpenWeatherMap API.
"""

import time
from typing import Dict, Any
from datetime import datetime, timezone
import requests

from src.utils.errors import (
    InvalidCityError,
    CityNotFoundError,
    APITimeoutError,
    APIRateLimitError,
    APIAuthenticationError,
    NetworkError,
    InvalidParamsError
)
from src.utils.validators import validate_city_name
from src.utils.logging import get_logger, log_api_call

logger = get_logger(__name__)


class WeatherTool:
    """
    Weather data fetching tool using OpenWeatherMap API.
    Provides current weather information for cities worldwide.
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str,
        timeout: int = 10
    ):
        """
        Initialize weather tool.
        
        Args:
            api_key: OpenWeatherMap API key
            base_url: Base URL for OpenWeatherMap API
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
        logger.info(
            "WeatherTool initialized",
            extra={
                'base_url': base_url,
                'timeout': timeout
            }
        )
    
    def execute(self, city: str) -> Dict[str, Any]:
        """
        Get current weather for a city.
        
        Args:
            city: City name
            
        Returns:
            Dictionary with weather data
            
        Raises:
            InvalidCityError: If city name is invalid
            CityNotFoundError: If city is not found in API
            APITimeoutError: If request times out
            APIRateLimitError: If rate limit exceeded
            APIAuthenticationError: If API key is invalid
            NetworkError: If network error occurs
        """
        # Validate city name
        try:
            validated_city = validate_city_name(city)
        except InvalidCityError:
            raise
        
        # Build API request
        endpoint = f"{self.base_url}/weather"
        params = {
            'q': validated_city,
            'appid': self.api_key,
            'units': 'metric'  # Use Celsius
        }
        
        # Make API request with timing
        start_time = time.time()
        
        try:
            response = requests.get(
                endpoint,
                params=params,
                timeout=self.timeout
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Log API call
            log_api_call(
                logger,
                api_name="OpenWeatherMap",
                endpoint=endpoint,
                duration_ms=duration_ms,
                status_code=response.status_code,
                success=response.status_code == 200,
                error=None if response.status_code == 200 else response.text[:200]
            )
            
            # Handle response codes
            if response.status_code == 200:
                return self._parse_weather_data(response.json(), validated_city)
            
            elif response.status_code == 404:
                raise CityNotFoundError(
                    validated_city,
                    data={'api_response': response.text[:200]}
                )
            
            elif response.status_code == 401:
                raise APIAuthenticationError(
                    "OpenWeatherMap",
                    data={'message': 'Invalid API key'}
                )
            
            elif response.status_code == 429:
                # Extract retry-after header if available
                retry_after = response.headers.get('Retry-After')
                retry_seconds = int(retry_after) if retry_after else None
                raise APIRateLimitError(
                    "OpenWeatherMap",
                    retry_after=retry_seconds,
                    data={'api_response': response.text[:200]}
                )
            
            else:
                raise NetworkError(
                    f"OpenWeatherMap API error: {response.status_code}",
                    data={
                        'status_code': response.status_code,
                        'response': response.text[:200]
                    }
                )
        
        except requests.exceptions.Timeout:
            duration_ms = (time.time() - start_time) * 1000
            log_api_call(
                logger,
                api_name="OpenWeatherMap",
                endpoint=endpoint,
                duration_ms=duration_ms,
                status_code=0,
                success=False,
                error="Request timeout"
            )
            raise APITimeoutError(
                "OpenWeatherMap",
                self.timeout,
                data={'city': validated_city}
            )
        
        except requests.exceptions.ConnectionError as e:
            duration_ms = (time.time() - start_time) * 1000
            log_api_call(
                logger,
                api_name="OpenWeatherMap",
                endpoint=endpoint,
                duration_ms=duration_ms,
                status_code=0,
                success=False,
                error=str(e)[:200]
            )
            raise NetworkError(
                f"Connection error: {str(e)[:100]}",
                data={'city': validated_city}
            )
        
        except requests.exceptions.RequestException as e:
            duration_ms = (time.time() - start_time) * 1000
            log_api_call(
                logger,
                api_name="OpenWeatherMap",
                endpoint=endpoint,
                duration_ms=duration_ms,
                status_code=0,
                success=False,
                error=str(e)[:200]
            )
            raise NetworkError(
                f"Request error: {str(e)[:100]}",
                data={'city': validated_city}
            )
    
    def _parse_weather_data(self, data: dict, city: str) -> Dict[str, Any]:
        """
        Parse OpenWeatherMap API response.
        
        Args:
            data: API response JSON
            city: Original city name
            
        Returns:
            Formatted weather data
        """
        try:
            # Extract main weather data
            main = data.get('main', {})
            weather = data.get('weather', [{}])[0]
            wind = data.get('wind', {})
            sys_data = data.get('sys', {})
            
            result = {
                'city': data.get('name', city),
                'country': sys_data.get('country', 'Unknown'),
                'temperature_celsius': round(main.get('temp', 0), 1),
                'feels_like_celsius': round(main.get('feels_like', 0), 1),
                'humidity_percent': main.get('humidity', 0),
                'description': weather.get('description', 'Unknown'),
                'weather_main': weather.get('main', 'Unknown'),
                'wind_speed_ms': round(wind.get('speed', 0), 1),
                'pressure_hpa': main.get('pressure', 0),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'api_timestamp': data.get('dt', 0)
            }
            
            # Add optional fields if available
            if 'clouds' in data:
                result['cloudiness_percent'] = data['clouds'].get('all', 0)
            
            if 'visibility' in data:
                result['visibility_meters'] = data['visibility']
            
            logger.info(
                f"Weather data retrieved for {result['city']}, {result['country']}",
                extra={
                    'city': result['city'],
                    'country': result['country'],
                    'temperature': result['temperature_celsius'],
                    'description': result['description']
                }
            )
            
            return result
        
        except (KeyError, IndexError, TypeError) as e:
            raise InvalidParamsError(
                f"Failed to parse weather API response: {str(e)}",
                data={'raw_response': str(data)[:200]}
            )


def create_weather_tool(config) -> WeatherTool:
    """
    Factory function to create WeatherTool from config.
    
    Args:
        config: Configuration object with required settings
        
    Returns:
        Configured WeatherTool instance
    """
    return WeatherTool(
        api_key=config.OPENWEATHER_API_KEY,
        base_url=config.OPENWEATHER_BASE_URL,
        timeout=config.OPENWEATHER_TIMEOUT
    )
