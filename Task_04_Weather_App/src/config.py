"""
Configuration management for the Weather Information Application.

Loads settings from environment variables and local .env files without
requiring third-party packages, while supporting python-dotenv if present.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


DEFAULT_UNITS = "metric"
DEFAULT_TIMEOUT = 10
DEFAULT_CITY = "London"


def load_env_file(filepath: Path | str | None = None) -> None:
    """Load key-value pairs from a .env file into os.environ.

    Attempts to use python-dotenv if installed, otherwise uses a clean
    standard-library parser. Does not overwrite already established env vars.
    """
    if filepath is None:
        filepath = Path(__file__).resolve().parent.parent / ".env"
    else:
        filepath = Path(filepath)

    if not filepath.exists():
        return

    # Try python-dotenv first
    try:
        from dotenv import load_dotenv
        load_dotenv(filepath)
        return
    except ImportError:
        pass

    # Built-in lightweight .env parser
    try:
        content = filepath.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip("'\"")
            if key and key not in os.environ:
                os.environ[key] = val
    except OSError:
        pass


@dataclass
class Config:
    """Application configuration holder.

    Attributes:
        api_key: OpenWeatherMap API key (from OPENWEATHER_API_KEY or WEATHER_API_KEY).
        units: Default units ('metric' for Celsius, 'imperial' for Fahrenheit).
        timeout: HTTP request timeout in seconds.
        default_city: Initial city shown on startup.
    """

    api_key: Optional[str] = None
    units: str = DEFAULT_UNITS
    timeout: int = DEFAULT_TIMEOUT
    default_city: str = DEFAULT_CITY

    @property
    def has_api_key(self) -> bool:
        """Return True if a valid non-empty API key is configured."""
        return bool(self.api_key and self.api_key.strip() and self.api_key.strip() != "your_api_key_here")

    @classmethod
    def load(cls, env_path: Optional[Path | str] = None) -> "Config":
        """Instantiate Config populated from environment and local .env."""
        load_env_file(env_path)

        api_key = os.getenv("OPENWEATHER_API_KEY") or os.getenv("WEATHER_API_KEY")
        if api_key:
            api_key = api_key.strip()
            if api_key == "your_api_key_here":
                api_key = None

        units = os.getenv("WEATHER_UNITS", DEFAULT_UNITS).lower().strip()
        if units not in ("metric", "imperial"):
            units = DEFAULT_UNITS

        raw_timeout = os.getenv("REQUEST_TIMEOUT", str(DEFAULT_TIMEOUT))
        try:
            timeout = int(raw_timeout)
            if timeout <= 0:
                timeout = DEFAULT_TIMEOUT
        except ValueError:
            timeout = DEFAULT_TIMEOUT

        default_city = os.getenv("DEFAULT_CITY", DEFAULT_CITY).strip() or DEFAULT_CITY

        return cls(
            api_key=api_key,
            units=units,
            timeout=timeout,
            default_city=default_city,
        )
