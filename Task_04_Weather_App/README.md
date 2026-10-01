# Task 04: Weather Information Application

A dual-mode (Desktop GUI & CLI) weather forecaster built with Python. Features real-time weather retrieval from OpenWeatherMap with automatic keyless fallback to Open-Meteo, asynchronous background data fetching, and dark-themed metric cards.

---

## 📌 Overview

The **Weather Information App** allows users to search for live weather conditions for cities worldwide. It delivers real-time meteorological metrics including temperature, feels-like temperature, humidity, wind speed, atmospheric pressure, and sunrise/sunset times.

The application operates in two modes:
1. **Desktop GUI Mode (Tkinter):** A modern dark-themed interface with threaded background fetching to prevent UI freezes.
2. **Command-Line Interface (CLI):** Designed for terminal usage, automated scripts, or headless servers.

---

## ✨ Features

- **Live Weather Data:** Temperature, weather condition description, humidity, wind speed, pressure, and sunrise/sunset.
- **Dual API Provider Architecture:**
  - **OpenWeatherMap:** Primary provider when an API key is configured.
  - **Open-Meteo:** Seamless, keyless fallback provider ensuring the app works out of the box without any mandatory API key.
- **Unit Toggle:** Easily switch between Metric (°C, m/s) and Imperial (°F, mph) units.
- **Asynchronous Data Retrieval:** Network calls run in background daemon threads to ensure smooth UI responsiveness.
- **Resilient Error Handling:** Graceful handling for unknown cities (404), unauthorized API keys (401), rate limits (429), and offline network timeouts.
- **Cross-Platform:** Works seamlessly across Windows, macOS, and Linux.

---

## 🛠️ Technologies Used

- **Language:** Python 3.10+
- **GUI Framework:** Tkinter
- **HTTP Client:** `requests`
- **Data Models:** `dataclasses`
- **Testing:** `unittest` with mock fixtures

---

## 📂 Project Structure

```text
Task_04_Weather_App/
├── assets/                # Screenshots and UI assets
├── src/
│   ├── __init__.py        # Package marker
│   ├── client.py          # WeatherApiClient (OpenWeatherMap + Open-Meteo fallback)
│   ├── config.py          # Environment variable and settings loader
│   ├── exceptions.py      # Custom error hierarchy
│   ├── gui.py             # Tkinter desktop GUI
│   └── models.py          # WeatherData model and JSON deserializers
├── tests/
│   ├── __init__.py
│   ├── mock_data.py       # API response test fixtures
│   └── test_weather.py    # 23 automated unit tests
├── .env.example           # Example configuration file
├── main.py                # Application entry point (GUI / CLI router)
├── requirements.txt       # Project dependencies
└── README.md              # Project documentation
```

---

## 🚀 Installation & Setup

1. Install project dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. *(Optional)* Configure your OpenWeatherMap API key:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Open `.env` and insert your free API key from [OpenWeatherMap](https://openweathermap.org/api):
     ```env
     OPENWEATHER_API_KEY=your_actual_key_here
     ```
   > **Note:** If no API key is provided, the application automatically uses **Open-Meteo** in keyless mode.

---

## 💻 How to Run

### Graphical Interface (Default)
```bash
python main.py
```

### Command-Line Interface (CLI)
Fetch weather for a city directly in the terminal:
```bash
python main.py --city "Tokyo"
```

Fetch with imperial units (°F):
```bash
python main.py --city "New York" --units imperial
```

---

## 🧪 Testing

Run the automated test suite with mock network fixtures:

```bash
python -m unittest discover tests -v
```

**Results:** 23 unit tests passing cleanly.
