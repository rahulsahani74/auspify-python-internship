"""
Data models and response parsers for the Weather Information Application.

Defines the WeatherData dataclass representing normalized weather metrics
along with robust deserializers for OpenWeatherMap and Open-Meteo payloads.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from src.exceptions import InvalidResponseError


# Weather condition to Unicode emoji mapping
WEATHER_EMOJIS = {
    "Clear": "☀️",
    "Clouds": "☁️",
    "Few Clouds": "🌤️",
    "Scattered Clouds": "⛅",
    "Broken Clouds": "🌥️",
    "Rain": "🌧️",
    "Light Rain": "🌦️",
    "Drizzle": "🌦️",
    "Thunderstorm": "⛈️",
    "Snow": "❄️",
    "Mist": "🌫️",
    "Smoke": "🌫️",
    "Haze": "🌫️",
    "Dust": "🌪️",
    "Fog": "🌫️",
    "Sand": "🌪️",
    "Ash": "🌋",
    "Squall": "💨",
    "Tornado": "🌪️",
}

# Open-Meteo WMO weather code mapping
WMO_WEATHER_CODES = {
    0: ("Clear sky", "Clear", "☀️"),
    1: ("Mainly clear", "Clear", "🌤️"),
    2: ("Partly cloudy", "Clouds", "⛅"),
    3: ("Overcast", "Clouds", "☁️"),
    45: ("Fog", "Fog", "🌫️"),
    48: ("Depositing rime fog", "Fog", "🌫️"),
    51: ("Light drizzle", "Drizzle", "🌦️"),
    53: ("Moderate drizzle", "Drizzle", "🌦️"),
    55: ("Dense drizzle", "Drizzle", "🌧️"),
    61: ("Slight rain", "Rain", "🌦️"),
    63: ("Moderate rain", "Rain", "🌧️"),
    65: ("Heavy rain", "Rain", "🌧️"),
    71: ("Slight snow", "Snow", "❄️"),
    73: ("Moderate snow", "Snow", "❄️"),
    75: ("Heavy snow", "Snow", "❄️"),
    80: ("Slight rain showers", "Rain", "🌦️"),
    81: ("Moderate rain showers", "Rain", "🌧️"),
    82: ("Violent rain showers", "Rain", "⛈️"),
    95: ("Thunderstorm", "Thunderstorm", "⛈️"),
    96: ("Thunderstorm with hail", "Thunderstorm", "⛈️"),
}


def _get_emoji_for_condition(condition: str) -> str:
    """Return matching emoji or default weather symbol."""
    return WEATHER_EMOJIS.get(condition.title(), "🌤️")


@dataclass
class WeatherData:
    """Normalized real-time weather information."""

    city: str
    country: str
    temperature: float
    feels_like: float
    temp_min: float
    temp_max: float
    humidity: int
    pressure: int
    wind_speed: float
    condition: str
    description: str
    icon_code: str = ""
    icon_emoji: str = "🌤️"
    sunrise: str = "N/A"
    sunset: str = "N/A"
    units: str = "metric"
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    provider: str = "OpenWeatherMap"

    @property
    def unit_symbol(self) -> str:
        """Return temperature unit symbol (°C or °F)."""
        return "°F" if self.units == "imperial" else "°C"

    @property
    def wind_unit(self) -> str:
        """Return wind speed unit (mph or m/s)."""
        return "mph" if self.units == "imperial" else "m/s"

    @property
    def temp_str(self) -> str:
        """Formatted temperature string."""
        return f"{self.temperature:.1f} {self.unit_symbol}"

    @property
    def feels_like_str(self) -> str:
        """Formatted feels-like string."""
        return f"Feels like {self.feels_like:.1f} {self.unit_symbol}"

    @property
    def min_max_str(self) -> str:
        """Formatted min/max temperature string."""
        return f"Min: {self.temp_min:.1f} {self.unit_symbol} / Max: {self.temp_max:.1f} {self.unit_symbol}"

    @property
    def wind_str(self) -> str:
        """Formatted wind speed string."""
        return f"{self.wind_speed:.1f} {self.wind_unit}"

    @property
    def humidity_str(self) -> str:
        """Formatted humidity percentage string."""
        return f"{self.humidity}%"

    @property
    def pressure_str(self) -> str:
        """Formatted atmospheric pressure string."""
        return f"{self.pressure} hPa"

    def to_dict(self) -> Dict[str, Any]:
        """Convert weather data to dictionary."""
        return {
            "city": self.city,
            "country": self.country,
            "temperature": self.temperature,
            "feels_like": self.feels_like,
            "temp_min": self.temp_min,
            "temp_max": self.temp_max,
            "humidity": self.humidity,
            "pressure": self.pressure,
            "wind_speed": self.wind_speed,
            "condition": self.condition,
            "description": self.description,
            "icon_emoji": self.icon_emoji,
            "sunrise": self.sunrise,
            "sunset": self.sunset,
            "units": self.units,
            "provider": self.provider,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_openweathermap(cls, data: Dict[str, Any], units: str = "metric") -> "WeatherData":
        """Parse OpenWeatherMap Current Weather API response into WeatherData.

        Raises:
            InvalidResponseError: If essential dictionary keys are missing.
        """
        try:
            city = str(data.get("name") or "Unknown City").strip()
            sys_info = data.get("sys") or {}
            country = str(sys_info.get("country") or "").strip()

            main_info = data.get("main")
            if not isinstance(main_info, dict):
                raise InvalidResponseError("Missing 'main' block in OpenWeatherMap payload.")

            temp = float(main_info.get("temp", 0.0))
            feels_like = float(main_info.get("feels_like", temp))
            temp_min = float(main_info.get("temp_min", temp))
            temp_max = float(main_info.get("temp_max", temp))
            humidity = int(main_info.get("humidity", 0))
            pressure = int(main_info.get("pressure", 1013))

            wind_info = data.get("wind") or {}
            wind_speed = float(wind_info.get("speed", 0.0))

            weather_list = data.get("weather") or []
            if weather_list and isinstance(weather_list[0], dict):
                first_weather = weather_list[0]
                condition = str(first_weather.get("main") or "Clear").strip()
                description = str(first_weather.get("description") or condition).capitalize()
                icon_code = str(first_weather.get("icon") or "")
            else:
                condition = "Clear"
                description = "Clear sky"
                icon_code = ""

            emoji = _get_emoji_for_condition(condition)

            # Format sunrise and sunset timestamps if present
            sunrise_ts = sys_info.get("sunrise")
            sunset_ts = sys_info.get("sunset")
            sunrise_str = datetime.fromtimestamp(sunrise_ts).strftime("%H:%M") if sunrise_ts else "N/A"
            sunset_str = datetime.fromtimestamp(sunset_ts).strftime("%H:%M") if sunset_ts else "N/A"

            return cls(
                city=city,
                country=country,
                temperature=temp,
                feels_like=feels_like,
                temp_min=temp_min,
                temp_max=temp_max,
                humidity=humidity,
                pressure=pressure,
                wind_speed=wind_speed,
                condition=condition,
                description=description,
                icon_code=icon_code,
                icon_emoji=emoji,
                sunrise=sunrise_str,
                sunset=sunset_str,
                units=units,
                provider="OpenWeatherMap",
            )
        except (TypeError, ValueError) as exc:
            raise InvalidResponseError(f"Error parsing OpenWeatherMap response: {exc}")

    @classmethod
    def from_open_meteo(
        cls,
        city_name: str,
        country: str,
        current_data: Dict[str, Any],
        units: str = "metric",
    ) -> "WeatherData":
        """Parse Open-Meteo API response into WeatherData."""
        try:
            temp = float(current_data.get("temperature_2m", 0.0))
            feels_like = float(current_data.get("apparent_temperature", temp))
            humidity = int(current_data.get("relative_humidity_2m", 0))
            pressure = int(round(float(current_data.get("surface_pressure", 1013))))
            wind_speed = float(current_data.get("wind_speed_10m", 0.0))
            wmo_code = int(current_data.get("weather_code", 0))

            desc, condition, emoji = WMO_WEATHER_CODES.get(
                wmo_code, ("Fair", "Clear", "🌤️")
            )

            return cls(
                city=city_name,
                country=country,
                temperature=temp,
                feels_like=feels_like,
                temp_min=temp,
                temp_max=temp,
                humidity=humidity,
                pressure=pressure,
                wind_speed=wind_speed,
                condition=condition,
                description=desc,
                icon_emoji=emoji,
                units=units,
                provider="Open-Meteo",
            )
        except (TypeError, ValueError) as exc:
            raise InvalidResponseError(f"Error parsing Open-Meteo response: {exc}")
