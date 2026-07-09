from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from dashboard_data import get_dashboard_data
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

# Card groupings to display on the UI
GROUPS = {
    "Key Thresholds": ["temp", "feels_like", "dewpoint", "aqi"],
    "Additional Reference": ["humidity", "uv"],
    "Not Yet Rated": ["wind"],
}

# Maps each metric's rating word to a CSS color class.
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
    "wind": {},  # wind is always gray
}


def get_greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 18:
        return "Good afternoon"
    else:
        return "Good evening"


@app.get("/")
def show_dashboard(request: Request):
    data = get_dashboard_data_cached()
    last_updated = datetime.now().strftime("%I:%M %p")

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "data": data,
            "display_names": DISPLAY_NAMES,
            "groups": GROUPS,
            "color_rules": COLOR_RULES,
            "last_updated": last_updated,
            "greeting": get_greeting(),
        },
    )