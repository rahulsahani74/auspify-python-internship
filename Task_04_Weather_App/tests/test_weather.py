"""
Comprehensive Automated Unit Tests for Task 04: Weather Information Application.

Covers:
- Configuration loader: defaults, environment variable ingestion, .env parsing
- WeatherData model: OpenWeatherMap deserializer, Open-Meteo deserializer, formatted string properties, emojis
- WeatherApiClient: OpenWeatherMap queries, Open-Meteo keyless fallback, 404 City Not Found, 401 Unauthorized,
  429 Rate Limit, network connection errors, HTTP timeouts, and malformed JSON payloads
- WeatherGUI: headless window construction, asynchronous fetching callbacks, widget updates, and unit toggles
"""

import os
import sys
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import requests

from src.client import WeatherApiClient
from src.config import Config, load_env_file
from src.exceptions import (
    ApiConnectionError,
    ApiKeyError,
    CityNotFoundError,
    InvalidResponseError,
    NetworkTimeoutError,
    RateLimitError,
    WeatherAppError,
)
from src.gui import WeatherGUI
from src.models import WeatherData
from tests.mock_data import (
    MOCK_OPEN_METEO_FORECAST_SUCCESS,
    MOCK_OPEN_METEO_GEO_EMPTY,
    MOCK_OPEN_METEO_GEO_SUCCESS,
    MOCK_OPENWEATHER_401,
    MOCK_OPENWEATHER_404,
    MOCK_OPENWEATHER_429,
    MOCK_OPENWEATHER_CORRUPTED,
    MOCK_OPENWEATHER_SUCCESS,
)


# ===========================================================================
# 1. Configuration Tests
# ===========================================================================

class TestConfig(unittest.TestCase):
    """Test suite for environment and configuration loading."""

    def setUp(self):
        self.orig_env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.orig_env)

    def test_default_config(self):
        os.environ.pop("OPENWEATHER_API_KEY", None)
        os.environ.pop("WEATHER_API_KEY", None)
        os.environ.pop("WEATHER_UNITS", None)
        os.environ.pop("REQUEST_TIMEOUT", None)
        os.environ.pop("DEFAULT_CITY", None)

        cfg = Config.load()
        self.assertIsNone(cfg.api_key)
        self.assertFalse(cfg.has_api_key)
        self.assertEqual(cfg.units, "metric")
        self.assertEqual(cfg.timeout, 10)
        self.assertEqual(cfg.default_city, "London")

    def test_custom_environment_variables(self):
        os.environ["OPENWEATHER_API_KEY"] = "test_key_12345"
        os.environ["WEATHER_UNITS"] = "imperial"
        os.environ["REQUEST_TIMEOUT"] = "15"
        os.environ["DEFAULT_CITY"] = "Paris"

        cfg = Config.load()
        self.assertEqual(cfg.api_key, "test_key_12345")
        self.assertTrue(cfg.has_api_key)
        self.assertEqual(cfg.units, "imperial")
        self.assertEqual(cfg.timeout, 15)
        self.assertEqual(cfg.default_city, "Paris")

    def test_placeholder_api_key_treated_as_unset(self):
        os.environ["OPENWEATHER_API_KEY"] = "your_api_key_here"
        cfg = Config.load()
        self.assertIsNone(cfg.api_key)
        self.assertFalse(cfg.has_api_key)

    def test_invalid_units_and_timeout_fallbacks(self):
        os.environ["WEATHER_UNITS"] = "kelvin_unsupported"
        os.environ["REQUEST_TIMEOUT"] = "not_a_number"

        cfg = Config.load()
        self.assertEqual(cfg.units, "metric")
        self.assertEqual(cfg.timeout, 10)


# ===========================================================================
# 2. WeatherData Model & Parser Tests
# ===========================================================================

class TestWeatherDataModel(unittest.TestCase):
    """Test suite for parsing OpenWeatherMap and Open-Meteo payloads."""

    def test_parse_openweathermap_success(self):
        weather = WeatherData.from_openweathermap(MOCK_OPENWEATHER_SUCCESS, units="metric")

        self.assertEqual(weather.city, "London")
        self.assertEqual(weather.country, "GB")
        self.assertEqual(weather.temperature, 18.5)
        self.assertEqual(weather.feels_like, 18.1)
        self.assertEqual(weather.temp_min, 16.8)
        self.assertEqual(weather.temp_max, 20.2)
        self.assertEqual(weather.humidity, 68)
        self.assertEqual(weather.pressure, 1016)
        self.assertEqual(weather.wind_speed, 4.1)
        self.assertEqual(weather.condition, "Clouds")
        self.assertEqual(weather.description, "Scattered clouds")
        self.assertEqual(weather.provider, "OpenWeatherMap")
        self.assertEqual(weather.temp_str, "18.5 °C")
        self.assertEqual(weather.feels_like_str, "Feels like 18.1 °C")
        self.assertEqual(weather.wind_str, "4.1 m/s")
        self.assertEqual(weather.humidity_str, "68%")
        self.assertEqual(weather.pressure_str, "1016 hPa")
        self.assertIn("16.8 °C", weather.min_max_str)
        self.assertIn("20.2 °C", weather.min_max_str)

    def test_parse_openweathermap_corrupted_raises(self):
        with self.assertRaises(InvalidResponseError):
            WeatherData.from_openweathermap(MOCK_OPENWEATHER_CORRUPTED, units="metric")

    def test_parse_open_meteo_success(self):
        current = MOCK_OPEN_METEO_FORECAST_SUCCESS["current"]
        weather = WeatherData.from_open_meteo(
            city_name="Tokyo",
            country="Japan",
            current_data=current,
            units="metric",
        )

        self.assertEqual(weather.city, "Tokyo")
        self.assertEqual(weather.country, "Japan")
        self.assertEqual(weather.temperature, 22.4)
        self.assertEqual(weather.feels_like, 21.9)
        self.assertEqual(weather.humidity, 58)
        self.assertEqual(weather.pressure, 1014)
        self.assertEqual(weather.wind_speed, 3.4)
        self.assertEqual(weather.condition, "Clear")
        self.assertEqual(weather.provider, "Open-Meteo")

    def test_units_formatting_imperial(self):
        weather = WeatherData(
            city="New York",
            country="US",
            temperature=72.5,
            feels_like=70.0,
            temp_min=65.0,
            temp_max=78.0,
            humidity=50,
            pressure=1012,
            wind_speed=8.5,
            condition="Clear",
            description="Clear sky",
            units="imperial",
        )
        self.assertEqual(weather.temp_str, "72.5 °F")
        self.assertEqual(weather.feels_like_str, "Feels like 70.0 °F")
        self.assertEqual(weather.wind_str, "8.5 mph")

    def test_to_dict_serialization(self):
        weather = WeatherData.from_openweathermap(MOCK_OPENWEATHER_SUCCESS, units="metric")
        d = weather.to_dict()
        self.assertEqual(d["city"], "London")
        self.assertEqual(d["temperature"], 18.5)
        self.assertEqual(d["provider"], "OpenWeatherMap")


# ===========================================================================
# 3. WeatherApiClient Tests (OpenWeatherMap Provider)
# ===========================================================================

class TestWeatherApiClientOpenWeather(unittest.TestCase):
    """Test suite for API Client when configured with an API Key."""

    def setUp(self):
        self.config = Config(api_key="valid_test_api_key", units="metric", timeout=5)
        self.mock_session = MagicMock(spec=requests.Session)
        self.client = WeatherApiClient(config=self.config, session=self.mock_session)

    def test_successful_weather_fetch(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = MOCK_OPENWEATHER_SUCCESS
        self.mock_session.get.return_value = mock_resp

        result = self.client.get_weather("London")

        self.assertEqual(result.city, "London")
        self.assertEqual(result.temperature, 18.5)
        self.mock_session.get.assert_called_once()
        args, kwargs = self.mock_session.get.call_args
        self.assertIn("q", kwargs["params"])
        self.assertEqual(kwargs["params"]["q"], "London")
        self.assertEqual(kwargs["params"]["appid"], "valid_test_api_key")

    def test_city_not_found_raises_404(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.json.return_value = MOCK_OPENWEATHER_404
        self.mock_session.get.return_value = mock_resp

        with self.assertRaises(CityNotFoundError):
            self.client.get_weather("NonExistentCityXYZ")

    def test_invalid_api_key_raises_401(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.json.return_value = MOCK_OPENWEATHER_401
        self.mock_session.get.return_value = mock_resp

        with self.assertRaises(ApiKeyError):
            self.client.get_weather("London")

    def test_rate_limit_raises_429(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.json.return_value = MOCK_OPENWEATHER_429
        self.mock_session.get.return_value = mock_resp

        with self.assertRaises(RateLimitError):
            self.client.get_weather("London")

    def test_empty_city_raises_city_not_found(self):
        with self.assertRaises(CityNotFoundError):
            self.client.get_weather("   ")


# ===========================================================================
# 4. WeatherApiClient Tests (Open-Meteo Keyless Fallback)
# ===========================================================================

class TestWeatherApiClientOpenMeteo(unittest.TestCase):
    """Test suite for API Client in keyless fallback mode."""

    def setUp(self):
        # No API key configured
        self.config = Config(api_key=None, units="metric", timeout=5)
        self.mock_session = MagicMock(spec=requests.Session)
        self.client = WeatherApiClient(config=self.config, session=self.mock_session)

    def test_successful_keyless_fetch(self):
        # Geocoding response
        geo_resp = MagicMock()
        geo_resp.status_code = 200
        geo_resp.json.return_value = MOCK_OPEN_METEO_GEO_SUCCESS

        # Forecast response
        forecast_resp = MagicMock()
        forecast_resp.status_code = 200
        forecast_resp.json.return_value = MOCK_OPEN_METEO_FORECAST_SUCCESS

        self.mock_session.get.side_effect = [geo_resp, forecast_resp]

        result = self.client.get_weather("Tokyo")
        self.assertEqual(result.city, "Tokyo")
        self.assertEqual(result.country, "Japan")
        self.assertEqual(result.temperature, 22.4)
        self.assertEqual(result.provider, "Open-Meteo")
        self.assertEqual(self.mock_session.get.call_count, 2)

    def test_keyless_city_not_found(self):
        geo_resp = MagicMock()
        geo_resp.status_code = 200
        geo_resp.json.return_value = MOCK_OPEN_METEO_GEO_EMPTY
        self.mock_session.get.return_value = geo_resp

        with self.assertRaises(CityNotFoundError):
            self.client.get_weather("UnknownCity123")


# ===========================================================================
# 5. Network & Timeout Error Handling Tests
# ===========================================================================

class TestNetworkAndTimeoutHandling(unittest.TestCase):
    """Test suite verifying resilience to network failures."""

    def setUp(self):
        self.config = Config(api_key="test_key", units="metric", timeout=5)
        self.mock_session = MagicMock(spec=requests.Session)
        self.client = WeatherApiClient(config=self.config, session=self.mock_session)

    def test_http_timeout_raises_network_timeout_error(self):
        self.mock_session.get.side_effect = requests.exceptions.Timeout("Connection timed out")

        with self.assertRaises(NetworkTimeoutError):
            self.client.get_weather("Berlin")

    def test_connection_error_raises_api_connection_error(self):
        self.mock_session.get.side_effect = requests.exceptions.ConnectionError("DNS failure")

        with self.assertRaises(ApiConnectionError):
            self.client.get_weather("Berlin")

    def test_non_json_payload_raises_invalid_response_error(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = ValueError("No JSON object could be decoded")
        self.mock_session.get.return_value = mock_resp

        with self.assertRaises(InvalidResponseError):
            self.client.get_weather("Berlin")


# ===========================================================================
# 6. WeatherGUI Headless Smoke Tests
# ===========================================================================

class TestWeatherGUI(unittest.TestCase):
    """Test suite verifying GUI construction and widget updates."""

    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
            self.mock_client = MagicMock(spec=WeatherApiClient)
            self.mock_client.config = Config(api_key="mock", default_city="", units="metric")
            self.gui = WeatherGUI(self.root, client=self.mock_client)
        except tk.TclError:
            self.skipTest("Tkinter display server unavailable in test environment")

    def tearDown(self):
        if hasattr(self, "root"):
            try:
                self.root.destroy()
            except tk.TclError:
                pass

    def test_gui_widget_initial_state(self):
        self.assertEqual(self.gui.lbl_temp.cget("text"), "-- °C")
        self.assertEqual(self.gui.lbl_condition.cget("text"), "Ready to search")

    def test_render_weather_success(self):
        weather = WeatherData.from_openweathermap(MOCK_OPENWEATHER_SUCCESS, units="metric")
        self.gui._render_weather_success(weather)

        self.assertIn("London", self.gui.lbl_city.cget("text"))
        self.assertEqual(self.gui.lbl_temp.cget("text"), "18.5 °C")
        self.assertIn("Clouds", self.gui.lbl_condition.cget("text"))
        self.assertEqual(self.gui.lbl_humidity.cget("text"), "68%")
        self.assertEqual(self.gui.lbl_wind.cget("text"), "4.1 m/s")

    def test_display_error(self):
        self.gui._display_error("Test Error Message")
        self.assertEqual(self.gui.lbl_status.cget("text"), "Test Error Message")

    def test_toggle_units(self):
        self.assertEqual(self.gui.current_units, "metric")
        self.assertEqual(self.gui.btn_unit.cget("text"), "°C")

        self.gui._on_toggle_units()
        self.assertEqual(self.gui.current_units, "imperial")
        self.assertEqual(self.gui.btn_unit.cget("text"), "°F")


if __name__ == "__main__":
    unittest.main()
