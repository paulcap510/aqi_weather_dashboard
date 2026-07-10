# Sky Check — Personalized Outdoor Conditions Dashboard

A weather dashboard designed for people managing respiratory or heat-sensitive health conditions who need more than a generic forecast to decide whether it's safe to go outside.

## Why this exists

Generic weather apps show raw numbers (temperature, humidity, AQI, etc.) without helping someone with a health condition interpret what those numbers actually mean *for them*. Sky Check rates each metric against configurable personal thresholds, so instead of "AQI: 52," you see "AQI: 52 (Good to go)."

A key design decision: **there is no single combined "safe to go outside" score.** Collapsing multiple health-relevant factors into one number would hide which specific factor is driving the day's risk, e.g. high humidity and high AQI require different responses, even if a naive average made the day look the same. Each metric is rated and displayed independently.

The app was originally designed for a family member suffering from these conditions, but is being expanded for more general usage.

## Features

- Real-time data from three independent government/public sources (see below)
- Configurable thresholds per metric, tuned to the individual using the dashboard
- Color-coded ratings (green / yellow / red) plus broader reference scales for metrics without personalized thresholds (e.g. UV index)
- Server-side caching (15-minute window) to minimize redundant API calls
- Graceful degradation — if a data source is temporarily unavailable, the app falls back to the last known-good data rather than crashing
- Accessibility-focused UI: large text, high-contrast color banners, and a legend explaining what each color means

## Data sources

| Source | Data | Why this source |
|---|---|---|
| [National Weather Service](https://api.weather.gov) | Temperature, feels-like, humidity, dewpoint, wind | Official US government API, no key required |
| [EPA AirNow](https://docs.airnowapi.org) | Air Quality Index | Free, account-based API key (not IP-based rate limiting) |
| [Open-Meteo](https://open-meteo.com) | UV Index | Reliable, well-established open weather data provider |

## Tech stack

- **Backend:** Python, FastAPI
- **Templating:** Jinja2
- **Frontend:** Custom CSS (no framework) — Fraunces, Inter, and IBM Plex Mono typefaces
- **Hosting:** Render (free tier)

## Architecture notes

- `fetch_weather.py` — handles all external API calls, returns plain dictionaries
- `thresholds.py` — pure rating logic (no API calls, no side effects); given a number, returns a rating
- `dashboard_data.py` — orchestration layer; combines fetched data with rating logic, includes the caching layer
- `main.py` — FastAPI routes and display configuration (display names, card groupings, color mappings)
- `templates/dashboard.html` — Jinja2 template, no business logic

This separation means the entire data source layer (`fetch_weather.py`) was swapped out mid-project — from a single weather API to three separate government sources — without touching the rating logic, orchestration, or display layers at all.

## Running locally

1. Clone the repo and create a virtual environment
2. `pip install -r requirements.txt`
3. Create a `.env` file with:
   ```
   NWS_USER_AGENT=(your-app-name, your-email@example.com)
   AIRNOW_API_KEY=your-airnow-api-key
   ```
4. `uvicorn main:app --reload`

## Known limitations

- Free-tier hosting means the app may take up to a minute to "wake up" after a period of inactivity
- Wind and pollen are not yet rated against personal thresholds (displayed as reference data only)
- Location is currently fixed to a single set of coordinates; multi-location search is a planned future addition

## Planned Features

- Allow users to search for data by city (right now it only shows data from New York City)
- UI improvement (hover effect to show what each metric means) and FAQ sections