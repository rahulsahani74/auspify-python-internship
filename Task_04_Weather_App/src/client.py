"""
REST API Client for the Weather Information Application.

Integrates with OpenWeatherMap as the primary provider and seamlessly supports
Open-Meteo as a keyless fallback, ensuring the application remains operational
under any environment configuration.
"""

from typing import Any, Dict, Optional
import requests

from src.config import Config
from src.exceptions import (
    ApiConnectionError,
    ApiKeyError,
    CityNotFoundError,
    InvalidResponseError,
    NetworkTimeoutError,
    RateLimitError,
    WeatherAppError,
)
from src.models import WeatherData


OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
OPEN_METEO_GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


class WeatherApiClient:
    """HTTP Client for retrieving real-time weather information."""

    def __init__(
        self,
        config: Optional[Config] = None,
        session: Optional[requests.Session] = None,
    ):
        """Initialize the weather API client.

        Args:
            config: Config instance. If None, default settings are loaded.
            session: Optional requests.Session instance (useful for unit test injection).
        """
        self.config = config or Config.load()
        self.session = session or requests.Session()

    def get_weather(self, city: str, units: Optional[str] = None) -> WeatherData:
        """Fetch current weather for the specified city.

        Uses OpenWeatherMap if an API key is present; otherwise falls back
        gracefully to Open-Meteo (keyless).

        Args:
            city: City name (e.g. 'London', 'Tokyo', 'Mumbai').
            units: 'metric' (°C) or 'imperial' (°F). Defaults to config.units.

        Returns:
            A normalized WeatherData object.

        Raises:
            CityNotFoundError: If city is not recognized.
            ApiKeyError: If API key is unauthorized.
            NetworkTimeoutError: If request times out.
            ApiConnectionError: If network fails.
            InvalidResponseError: If response cannot be parsed.
        """
        cleaned_city = city.strip()
        if not cleaned_city:
            raise CityNotFoundError("")

        target_units = units.lower().strip() if units else self.config.units
        if target_units not in ("metric", "imperial"):
            target_units = "metric"

        if self.config.has_api_key:
            return self._fetch_openweathermap(cleaned_city, target_units)
        else:
            return self._fetch_open_meteo(cleaned_city, target_units)

    def _fetch_openweathermap(self, city: str, units: str) -> WeatherData:
        """Fetch weather data from OpenWeatherMap API."""
        params = {
            "q": city,
            "appid": self.config.api_key,
            "units": units,
        }

        try:
            resp = self.session.get(
                OPENWEATHER_BASE_URL,
                params=params,
                timeout=self.config.timeout,
            )
        except requests.exceptions.Timeout as exc:
            raise NetworkTimeoutError() from exc
        except requests.exceptions.ConnectionError as exc:
            raise ApiConnectionError() from exc
        except requests.exceptions.RequestException as exc:
            raise WeatherAppError(f"HTTP request error: {exc}") from exc

        if resp.status_code == 200:
            try:
                payload = resp.json()
            except ValueError as exc:
                raise InvalidResponseError("OpenWeatherMap returned non-JSON payload.") from exc
            return WeatherData.from_openweathermap(payload, units=units)

        if resp.status_code == 404:
            raise CityNotFoundError(city)

        if resp.status_code == 401:
            raise ApiKeyError(
                "Invalid or unauthorized OpenWeatherMap API key. "
                "Please configure a valid OPENWEATHER_API_KEY in your .env file."
            )

        if resp.status_code == 429:
            raise RateLimitError("OpenWeatherMap rate limit exceeded. Please wait before retrying.")

        raise WeatherAppError(
            f"OpenWeatherMap request failed with status code {resp.status_code}: {resp.text}",
            status_code=resp.status_code,
        )

    def _fetch_open_meteo(self, city: str, units: str) -> WeatherData:
        """Fetch weather data from Open-Meteo API (Keyless fallback mode)."""
        # Step 1: Geocode city name to lat/lon
        geo_params = {
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json",
        }

        try:
            geo_resp = self.session.get(
                OPEN_METEO_GEO_URL,
                params=geo_params,
                timeout=self.config.timeout,
            )
        except requests.exceptions.Timeout as exc:
            raise NetworkTimeoutError() from exc
        except requests.exceptions.ConnectionError as exc:
            raise ApiConnectionError() from exc
        except requests.exceptions.RequestException as exc:
            raise WeatherAppError(f"Geocoding request error: {exc}") from exc

        if geo_resp.status_code != 200:
            raise WeatherAppError(f"Geocoding service returned status {geo_resp.status_code}.")

        try:
            geo_data = geo_resp.json()
        except ValueError as exc:
            raise InvalidResponseError("Geocoding service returned non-JSON payload.") from exc

        results = geo_data.get("results") or []
        if not results or not isinstance(results, list):
            raise CityNotFoundError(city)

        top_match = results[0]
        lat = top_match.get("latitude")
        lon = top_match.get("longitude")
        matched_city = top_match.get("name", city)
        matched_country = top_match.get("country", "")

        # Step 2: Fetch current weather for latitude/longitude
        forecast_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,surface_pressure,wind_speed_10m",
            "temperature_unit": "fahrenheit" if units == "imperial" else "celsius",
            "wind_speed_unit": "mph" if units == "imperial" else "ms",
        }

        try:
            forecast_resp = self.session.get(
                OPEN_METEO_FORECAST_URL,
                params=forecast_params,
                timeout=self.config.timeout,
            )
        except requests.exceptions.Timeout as exc:
            raise NetworkTimeoutError() from exc
        except requests.exceptions.ConnectionError as exc:
            raise ApiConnectionError() from exc
        except requests.exceptions.RequestException as exc:
            raise WeatherAppError(f"Weather forecast request error: {exc}") from exc

        if forecast_resp.status_code != 200:
            raise WeatherAppError(f"Weather forecast service returned status {forecast_resp.status_code}.")

        try:
            forecast_data = forecast_resp.json()
        except ValueError as exc:
            raise InvalidResponseError("Forecast service returned non-JSON payload.") from exc

        current_data = forecast_data.get("current")
        if not isinstance(current_data, dict):
            raise InvalidResponseError("Forecast payload missing 'current' weather block.")

        return WeatherData.from_open_meteo(
            city_name=matched_city,
            country=matched_country,
            current_data=current_data,
            units=units,
        )
