"""
Mock response fixtures for Weather App unit testing.

Contains realistic sample responses for OpenWeatherMap and Open-Meteo APIs,
enabling offline, reproducible test execution without live network requests.
"""

# Successful OpenWeatherMap JSON response for London
MOCK_OPENWEATHER_SUCCESS = {
    "coord": {"lon": -0.1257, "lat": 51.5085},
    "weather": [
        {
            "id": 802,
            "main": "Clouds",
            "description": "scattered clouds",
            "icon": "03d",
        }
    ],
    "base": "stations",
    "main": {
        "temp": 18.5,
        "feels_like": 18.1,
        "temp_min": 16.8,
        "temp_max": 20.2,
        "pressure": 1016,
        "humidity": 68,
    },
    "visibility": 10000,
    "wind": {"speed": 4.1, "deg": 230},
    "clouds": {"all": 40},
    "dt": 1696156800,
    "sys": {
        "type": 2,
        "id": 2075535,
        "country": "GB",
        "sunrise": 1696140000,
        "sunset": 1696182000,
    },
    "timezone": 3600,
    "id": 2643743,
    "name": "London",
    "cod": 200,
}

# 404 City Not Found payload
MOCK_OPENWEATHER_404 = {
    "cod": "404",
    "message": "city not found",
}

# 401 Unauthorized payload
MOCK_OPENWEATHER_401 = {
    "cod": 401,
    "message": "Invalid API key. Please see https://openweathermap.org/faq#error401 for more info.",
}

# 429 Rate Limit payload
MOCK_OPENWEATHER_429 = {
    "cod": 429,
    "message": "Your account is temporarily blocked due to exceeding of requests limitation of your subscription type.",
}

# Malformed response missing "main"
MOCK_OPENWEATHER_CORRUPTED = {
    "name": "CorruptedCity",
    "weather": [{"main": "Clear"}],
}

# Open-Meteo Geocoding successful response for Tokyo
MOCK_OPEN_METEO_GEO_SUCCESS = {
    "results": [
        {
            "id": 1850147,
            "name": "Tokyo",
            "latitude": 35.6895,
            "longitude": 139.69171,
            "country": "Japan",
            "country_code": "JP",
            "timezone": "Asia/Tokyo",
        }
    ],
    "generationtime_ms": 0.45,
}

# Open-Meteo Geocoding empty response
MOCK_OPEN_METEO_GEO_EMPTY = {
    "results": [],
    "generationtime_ms": 0.12,
}

# Open-Meteo Forecast successful response
MOCK_OPEN_METEO_FORECAST_SUCCESS = {
    "latitude": 35.6895,
    "longitude": 139.69171,
    "current": {
        "time": "2026-10-01T10:00",
        "temperature_2m": 22.4,
        "relative_humidity_2m": 58,
        "apparent_temperature": 21.9,
        "weather_code": 0,
        "surface_pressure": 1014.2,
        "wind_speed_10m": 3.4,
    },
}
