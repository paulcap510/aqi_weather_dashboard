from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from dashboard_data import get_dashboard_data_cached

app = FastAPI()
templates = Jinja2Templates(directory="templates")


# Reader-friendly display names that appear on UI
DISPLAY_NAMES = {
    "aqi": "AQI",
    "uv": "UV Index",
    "dewpoint": "Dewpoint",
    "temp": "Temperature",
    "feels_like": "Feels Like",
    "humidity": "Humidity",
    "wind": "Wind Speed",
}


METRIC_INFO = {
    "aqi": "Measures how clean or polluted the air is, based on pollutants like ozone and fine particles. Higher numbers mean more people may start to notice effects, especially those with respiratory or heart conditions.",
    "dewpoint": "Measures how much moisture is in the air. Above 65°F, air starts to feel heavy and humi. The higher it climbs, the harder it is for your body to cool itself.",
    "temp": "The actual air temperature, measured in the shade, away from direct sun.",
    "feels_like": "How the temperature actually feels on your skin, accounting for humidity and wind. This is often a better guide than the raw temperature alone.",
    "humidity": "The percentage of moisture in the air relative to the maximum it could hold at the current temperature.",
    "uv": "Measures the strength of the sun's ultraviolet rays. Higher numbers mean skin can burn more quickly without protection.",
    "wind": "Current wind speed. Personal thresholds for this haven't been set yet.",
}


# Card groupings
GROUPS = {
    "Key Thresholds": ["temp", "feels_like", "dewpoint", "aqi"],
    "Additional Reference": ["humidity", "uv"],
    "Not Yet Rated": ["wind"],
}


COLOR_RULES = {
    "temp": {"green": "green", "yellow": "yellow", "red": "red"},
    "feels_like": {"green": "green", "yellow": "yellow", "red": "red"},
    "dewpoint": {"green": "green", "yellow": "yellow", "red": "red"},
    "aqi": {"green": "green", "yellow": "yellow", "red": "red"},
    "uv": {
        "low": "green",
        "moderate": "yellow",
        "high": "orange",
        "very high": "red",
        "extreme": "deepred",
    },
    "humidity": {
        "low": "blue",
        "average": "green",
        "high": "red",
    },
    "wind": {},
}


def get_greeting():
    hour = datetime.now(ZoneInfo("America/New_York")).hour
    if hour < 12:
        return "Good morning"
    elif hour < 18:
        return "Good afternoon"
    else:
        return "Good evening"


@app.get("/")
def show_dashboard(request: Request):
    data = get_dashboard_data_cached()
    last_updated = datetime.now(ZoneInfo("America/New_York")).strftime("%I:%M %p")

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "data": data,
            "display_names": DISPLAY_NAMES,
            "groups": GROUPS,
            "color_rules": COLOR_RULES,
            "metric_info": METRIC_INFO,
            "last_updated": last_updated,
            "greeting": get_greeting(),
        },
    )