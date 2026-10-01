"""
Graphical User Interface for the Weather Information Application.

Built with Python's standard Tkinter framework. Features background
asynchronous network fetching, modern dark-theme styling, metric cards,
unit toggle (°C / °F), and resilient error banners.
"""

import threading
import tkinter as tk
from tkinter import font as tkfont
from typing import Optional

from src.client import WeatherApiClient
from src.config import Config
from src.exceptions import WeatherAppError
from src.models import WeatherData


# Palette configuration (Modern Dark Theme)
COLOR_BG_MAIN = "#12141a"
COLOR_BG_CARD = "#1c202a"
COLOR_BG_INPUT = "#252b38"
COLOR_TEXT_PRIMARY = "#ffffff"
COLOR_TEXT_SECONDARY = "#94a3b8"
COLOR_TEXT_MUTED = "#64748b"
COLOR_ACCENT = "#38bdf8"
COLOR_ACCENT_HOVER = "#0284c7"
COLOR_ERROR_BG = "#3f1a1d"
COLOR_ERROR_TEXT = "#f87171"
COLOR_SUCCESS = "#4ade80"


class WeatherGUI:
    """Tkinter-based Graphical User Interface for Weather forecasting."""

    def __init__(self, root: tk.Tk, client: Optional[WeatherApiClient] = None):
        """Initialize weather GUI application.

        Args:
            root: Root Tkinter window.
            client: WeatherApiClient instance.
        """
        self.root = root
        self.client = client or WeatherApiClient()
        self.current_units = self.client.config.units
        self.active_weather: Optional[WeatherData] = None
        self._is_loading = False

        self._setup_window()
        self._setup_fonts()
        self._build_widgets()
        self._bind_events()

        # Trigger initial search for default city
        initial_city = self.client.config.default_city
        if initial_city:
            self.city_entry.delete(0, tk.END)
            self.city_entry.insert(0, initial_city)
            self.fetch_weather_async(initial_city)

    def _setup_window(self) -> None:
        """Configure root window parameters."""
        self.root.title("Weather Information App")
        self.root.geometry("440x620")
        self.root.minsize(380, 560)
        self.root.configure(bg=COLOR_BG_MAIN)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def _setup_fonts(self) -> None:
        """Initialize typographic font families."""
        self.font_title = tkfont.Font(family="Segoe UI", size=18, weight="bold")
        self.font_temp = tkfont.Font(family="Segoe UI", size=36, weight="bold")
        self.font_condition = tkfont.Font(family="Segoe UI", size=13, weight="bold")
        self.font_body = tkfont.Font(family="Segoe UI", size=11)
        self.font_small = tkfont.Font(family="Segoe UI", size=9)
        self.font_icon = tkfont.Font(family="Segoe UI", size=48)

    def _build_widgets(self) -> None:
        """Construct GUI container frames and components."""
        main_container = tk.Frame(self.root, bg=COLOR_BG_MAIN, padx=16, pady=16)
        main_container.grid(row=0, column=0, sticky="nsew")
        main_container.columnconfigure(0, weight=1)

        # 1. Header Bar with Provider Status
        header_frame = tk.Frame(main_container, bg=COLOR_BG_MAIN)
        header_frame.pack(fill="x", pady=(0, 10))

        lbl_app = tk.Label(
            header_frame,
            text="WEATHER FORECAST",
            font=self.font_small,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_BG_MAIN,
        )
        lbl_app.pack(side="left")

        provider_tag = "OpenWeatherMap" if self.client.config.has_api_key else "Open-Meteo (Free Mode)"
        self.lbl_provider = tk.Label(
            header_frame,
            text=f"API: {provider_tag}",
            font=self.font_small,
            fg=COLOR_SUCCESS if self.client.config.has_api_key else COLOR_ACCENT,
            bg=COLOR_BG_MAIN,
        )
        self.lbl_provider.pack(side="right")

        # 2. Search Box & Controls
        search_frame = tk.Frame(main_container, bg=COLOR_BG_MAIN)
        search_frame.pack(fill="x", pady=(0, 12))
        search_frame.columnconfigure(0, weight=1)
        search_frame.columnconfigure(1, weight=0)
        search_frame.columnconfigure(2, weight=0)

        self.city_entry = tk.Entry(
            search_frame,
            font=self.font_body,
            bg=COLOR_BG_INPUT,
            fg=COLOR_TEXT_PRIMARY,
            insertbackground=COLOR_TEXT_PRIMARY,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=COLOR_BG_CARD,
            highlightcolor=COLOR_ACCENT,
        )
        self.city_entry.grid(row=0, column=0, sticky="ew", ipady=8, padx=(0, 6))

        btn_search = tk.Button(
            search_frame,
            text="Search",
            font=self.font_body,
            bg=COLOR_ACCENT,
            fg="#0f172a",
            activebackground=COLOR_ACCENT_HOVER,
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=14,
            cursor="hand2",
            command=self._on_search_clicked,
        )
        btn_search.grid(row=0, column=1, sticky="ns", padx=(0, 6))

        self.btn_unit = tk.Button(
            search_frame,
            text="°C",
            font=self.font_body,
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_PRIMARY,
            activebackground=COLOR_BG_INPUT,
            relief="flat",
            bd=0,
            padx=10,
            cursor="hand2",
            command=self._on_toggle_units,
        )
        self.btn_unit.grid(row=0, column=2, sticky="ns")

        # 3. Status / Alert Bar
        self.alert_frame = tk.Frame(main_container, bg=COLOR_BG_MAIN)
        self.alert_frame.pack(fill="x", pady=(0, 8))

        self.lbl_status = tk.Label(
            self.alert_frame,
            text="",
            font=self.font_small,
            fg=COLOR_ACCENT,
            bg=COLOR_BG_MAIN,
            wraplength=380,
            justify="center",
        )
        self.lbl_status.pack(fill="x")

        # 4. Hero Weather Display Card
        self.hero_card = tk.Frame(main_container, bg=COLOR_BG_CARD, padx=20, pady=18)
        self.hero_card.pack(fill="x", pady=(0, 14))

        self.lbl_city = tk.Label(
            self.hero_card,
            text="--",
            font=self.font_title,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_CARD,
        )
        self.lbl_city.pack()

        self.lbl_icon = tk.Label(
            self.hero_card,
            text="🌤️",
            font=self.font_icon,
            bg=COLOR_BG_CARD,
        )
        self.lbl_icon.pack(pady=2)

        self.lbl_temp = tk.Label(
            self.hero_card,
            text="-- °C",
            font=self.font_temp,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_CARD,
        )
        self.lbl_temp.pack()

        self.lbl_condition = tk.Label(
            self.hero_card,
            text="Ready to search",
            font=self.font_condition,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_BG_CARD,
        )
        self.lbl_condition.pack(pady=(2, 4))

        self.lbl_feels_like = tk.Label(
            self.hero_card,
            text="",
            font=self.font_small,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_BG_CARD,
        )
        self.lbl_feels_like.pack()

        # 5. Detailed Metrics Grid Card
        self.metrics_card = tk.Frame(main_container, bg=COLOR_BG_CARD, padx=16, pady=14)
        self.metrics_card.pack(fill="both", expand=True)

        for col in range(2):
            self.metrics_card.columnconfigure(col, weight=1)

        # Humidity
        self.lbl_humidity = self._build_metric_tile(self.metrics_card, 0, 0, "💧 Humidity", "--")
        # Wind Speed
        self.lbl_wind = self._build_metric_tile(self.metrics_card, 0, 1, "💨 Wind Speed", "--")
        # Pressure
        self.lbl_pressure = self._build_metric_tile(self.metrics_card, 1, 0, "⏲ Pressure", "--")
        # Min/Max
        self.lbl_min_max = self._build_metric_tile(self.metrics_card, 1, 1, "🌡 Temp Range", "--")
        # Sunrise/Sunset
        self.lbl_sun = self._build_metric_tile(self.metrics_card, 2, 0, "🌅 Sunrise / Sunset", "--", colspan=2)

        # 6. Timestamp Footer
        self.lbl_timestamp = tk.Label(
            main_container,
            text="",
            font=self.font_small,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_BG_MAIN,
            pady=6,
        )
        self.lbl_timestamp.pack(fill="x")

    def _build_metric_tile(
        self,
        parent: tk.Widget,
        row: int,
        col: int,
        title: str,
        initial_val: str,
        colspan: int = 1,
    ) -> tk.Label:
        """Create a styled metric tile."""
        tile = tk.Frame(parent, bg=COLOR_BG_CARD, padx=6, pady=6)
        tile.grid(row=row, column=col, columnspan=colspan, sticky="nsew", padx=4, pady=4)

        lbl_title = tk.Label(
            tile,
            text=title,
            font=self.font_small,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_BG_CARD,
        )
        lbl_title.pack(anchor="w")

        lbl_val = tk.Label(
            tile,
            text=initial_val,
            font=self.font_body,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_CARD,
        )
        lbl_val.pack(anchor="w", pady=(2, 0))

        return lbl_val

    def _bind_events(self) -> None:
        """Bind keyboard interactions."""
        self.city_entry.bind("<Return>", lambda e: self._on_search_clicked())

    def _on_search_clicked(self) -> None:
        """Handle search button trigger."""
        city = self.city_entry.get().strip()
        if not city:
            self._display_error("Please enter a city name to search.")
            return
        self.fetch_weather_async(city)

    def _on_toggle_units(self) -> None:
        """Toggle between Metric (°C) and Imperial (°F) units."""
        self.current_units = "imperial" if self.current_units == "metric" else "metric"
        self.btn_unit.configure(text="°F" if self.current_units == "imperial" else "°C")

        # If data is currently shown, re-fetch in new units
        city = self.city_entry.get().strip()
        if city:
            self.fetch_weather_async(city)

    def fetch_weather_async(self, city: str) -> None:
        """Fetch weather data in a background thread to prevent UI freezing."""
        if self._is_loading:
            return

        self._is_loading = True
        self.lbl_status.configure(text=f"Fetching weather for '{city}'...", fg=COLOR_ACCENT)
        self.alert_frame.configure(bg=COLOR_BG_MAIN)

        def worker():
            try:
                data = self.client.get_weather(city, units=self.current_units)
                self.root.after(0, self._render_weather_success, data)
            except WeatherAppError as err:
                self.root.after(0, self._display_error, err.message)
            except Exception as exc:
                self.root.after(0, self._display_error, f"Unexpected error: {exc}")
            finally:
                self._is_loading = False

        threading.Thread(target=worker, daemon=True).start()

    def _render_weather_success(self, data: WeatherData) -> None:
        """Populate GUI widgets with fetched WeatherData."""
        self.active_weather = data
        self.lbl_status.configure(text="")

        city_country = f"{data.city}, {data.country}" if data.country else data.city
        self.lbl_city.configure(text=city_country)
        self.lbl_icon.configure(text=data.icon_emoji)
        self.lbl_temp.configure(text=data.temp_str)
        self.lbl_condition.configure(text=f"{data.condition} • {data.description}")
        self.lbl_feels_like.configure(text=data.feels_like_str)

        self.lbl_humidity.configure(text=data.humidity_str)
        self.lbl_wind.configure(text=data.wind_str)
        self.lbl_pressure.configure(text=data.pressure_str)
        self.lbl_min_max.configure(text=data.min_max_str)

        if data.sunrise != "N/A" and data.sunset != "N/A":
            self.lbl_sun.configure(text=f"🌅 {data.sunrise}   |   🌇 {data.sunset}")
        else:
            self.lbl_sun.configure(text="N/A (Keyless Mode)")

        self.lbl_timestamp.configure(
            text=f"Updated: {data.timestamp}  |  Source: {data.provider}"
        )

    def _display_error(self, message: str) -> None:
        """Render error message on status banner."""
        self.lbl_status.configure(text=message, fg=COLOR_ERROR_TEXT)
