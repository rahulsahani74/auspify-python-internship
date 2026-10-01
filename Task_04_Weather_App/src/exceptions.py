"""
Custom exceptions for the Weather Information Application.

Defines a clean error hierarchy mapping network, HTTP, API authentication,
and response parsing errors to actionable, user-friendly descriptions.
"""


class WeatherAppError(Exception):
    """Base exception for all weather application errors."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class CityNotFoundError(WeatherAppError):
    """Raised when the specified city cannot be found by the weather provider."""

    def __init__(self, city: str):
        super().__init__(
            f"City '{city}' not found. Please verify spelling and try again.",
            status_code=404,
        )
        self.city = city


class ApiKeyError(WeatherAppError):
    """Raised when an API key is missing, invalid, or unauthorized."""

    def __init__(self, message: str = "Invalid or unauthorized API key. Check your .env configuration."):
        super().__init__(message, status_code=401)


class RateLimitError(WeatherAppError):
    """Raised when the provider's rate limit has been exceeded."""

    def __init__(self, message: str = "Weather API rate limit exceeded. Please try again later."):
        super().__init__(message, status_code=429)


class NetworkTimeoutError(WeatherAppError):
    """Raised when an API HTTP request times out."""

    def __init__(self, message: str = "Request timed out while connecting to weather service. Please check your internet connection."):
        super().__init__(message, status_code=408)


class ApiConnectionError(WeatherAppError):
    """Raised when unable to establish a connection to the weather service."""

    def __init__(self, message: str = "Network connection failed. Unable to reach weather service."):
        super().__init__(message, status_code=503)


class InvalidResponseError(WeatherAppError):
    """Raised when the weather service returns unexpected or malformed payload data."""

    def __init__(self, message: str = "Received invalid or malformed data from weather service."):
        super().__init__(message, status_code=502)
