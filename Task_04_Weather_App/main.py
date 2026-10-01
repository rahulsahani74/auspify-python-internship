"""
Main entry point for Task 04: Weather Information Application.

Launches the Tkinter GUI interface by default, and supports a command-line
mode (--city <name>) for terminal execution or headless server environments.
"""

import argparse
import sys
import tkinter as tk

from src.client import WeatherApiClient
from src.config import Config
from src.exceptions import WeatherAppError
from src.gui import WeatherGUI


def run_cli_mode(city: str, units: str = "metric") -> int:
    """Fetch and display weather in terminal format."""
    client = WeatherApiClient()
    provider_name = "OpenWeatherMap" if client.config.has_api_key else "Open-Meteo (Keyless Mode)"
    print(f"\nFetching weather for '{city}' using {provider_name}...")

    try:
        data = client.get_weather(city, units=units)
    except WeatherAppError as err:
        print(f"\n[!] Error: {err.message}\n")
        return 1
    except Exception as exc:
        print(f"\n[!] Unexpected error: {exc}\n")
        return 1

    country_tag = f", {data.country}" if data.country else ""
    print()
    print("+------------------------------------------------------+")
    print(f"|  {data.city}{country_tag:<40}  |")
    print("+------------------------------------------------------+")
    print(f"|  Condition   : {data.icon_emoji}  {data.condition:<34}|")
    print(f"|  Description : {data.description:<38}|")
    print(f"|  Temperature : {data.temp_str:<38}|")
    print(f"|  Feels Like  : {data.feels_like_str:<38}|")
    print(f"|  Min / Max   : {data.min_max_str:<38}|")
    print(f"|  Humidity    : {data.humidity_str:<38}|")
    print(f"|  Wind Speed  : {data.wind_str:<38}|")
    print(f"|  Pressure    : {data.pressure_str:<38}|")
    if data.sunrise != "N/A" and data.sunset != "N/A":
        print(f"|  Sun Schedule: 🌅 {data.sunrise}  |  🌇 {data.sunset:<18}|")
    print("+------------------------------------------------------+")
    print(f"|  Source: {data.provider:<16}  Updated: {data.timestamp:<14}|")
    print("+------------------------------------------------------+\n")
    return 0


def run_gui_mode() -> int:
    """Launch the Tkinter GUI window."""
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print(f"[!] Graphical display unavailable ({exc}). Falling back to CLI mode.\n")
        config = Config.load()
        return run_cli_mode(config.default_city, units=config.units)

    # Center window on screen
    width, height = 440, 620
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    pos_x = max(0, int((screen_w - width) / 2))
    pos_y = max(0, int((screen_h - height) / 2))
    root.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

    # Launch GUI
    app = WeatherGUI(root)
    root.mainloop()
    return 0


def main() -> None:
    """Parse command line flags and execute application."""
    parser = argparse.ArgumentParser(
        description="Weather Information App - Live Weather Forecaster"
    )
    parser.add_argument(
        "--city",
        type=str,
        help="City name to fetch weather for directly via terminal.",
    )
    parser.add_argument(
        "--units",
        type=str,
        choices=["metric", "imperial"],
        default="metric",
        help="Temperature unit: metric (°C) or imperial (°F).",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Force CLI terminal mode instead of launching GUI.",
    )

    args = parser.parse_args()

    if args.city or args.cli:
        target_city = args.city or Config.load().default_city
        sys.exit(run_cli_mode(target_city, units=args.units))
    else:
        sys.exit(run_gui_mode())


if __name__ == "__main__":
    main()
