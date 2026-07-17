from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import FastAPI, Request, Depends, HTTPException
from collections import defaultdict
from fastapi.templating import Jinja2Templates
from dashboard_data import get_dashboard_data_cached, LATITUDE, LONGITUDE
from fetch_weather import LATITUDE, LONGITUDE, get_coordinates_for_city
from timezonefinder import TimezoneFinder

app = FastAPI()
templates = Jinja2Templates(directory="templates")


# Protects AirNow's shared 500-calls/hour budget from any single visitor (or bot) exhausting it via repeated searches.
RATE_LIMIT = 15  # searches per hour, per visitor IP
_request_log = defaultdict(list)
#** _request_log = indicates this will be used in this file specifically

def check_rate_limit(request: Request):
    ip = request.client.host
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)
    _request_log[ip] = [t for t in _request_log[ip] if t > one_hour_ago]

    if len(_request_log[ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="You've made a lot of searches. Please wait a bit before searching again.")

    _request_log[ip].append(now)

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



    #** Depends() runs check_rate_limit before this route's code executes.
    #** If it raises (429), this whole function is skipped and the error
    #** handler takes over. If it doesn't raise, execution just continues
    #** normally -- the returned None (held in `_`) is never used.

@app.get("/")
def show_dashboard(request: Request, city: str = None, _: None = Depends(check_rate_limit)):
    if city:
        try:
            latitude, longitude, location_name = get_coordinates_for_city(city)
        except ValueError:
            return templates.TemplateResponse(
                request,
                "dashboard.html",
                {
                    "data": None,
                    "error_message": f"Couldn't find a location matching '{city}'.",
                    "display_names": DISPLAY_NAMES,
                    "groups": GROUPS,
                    "color_rules": COLOR_RULES,
                    "metric_info": METRIC_INFO,
                    "last_updated": "",
                    "greeting": get_greeting(),
                    "location_name": city,
                },
            )
    else:
        latitude, longitude, location_name = LATITUDE, LONGITUDE, "Queens, NY"

    data = get_dashboard_data_cached(latitude, longitude)

    location_timezone = TimezoneFinder().timezone_at(lat=latitude, lng=longitude)
    eastern_now = datetime.now(ZoneInfo(location_timezone))
    last_updated = eastern_now.strftime("%I:%M %p")

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
            "location_name": location_name,
            "error_message": None,
        },
    )


@app.exception_handler(HTTPException)
async def friendly_error_handler(request: Request, exc: HTTPException):
    if exc.status_code == 429:
        return templates.TemplateResponse(
            request,
            "dashboard.html",
            {
                "data": None,
                "error_message": exc.detail,
                "display_names": DISPLAY_NAMES,
                "groups": GROUPS,
                "color_rules": COLOR_RULES,
                "metric_info": METRIC_INFO,
                "last_updated": "",
                "greeting": get_greeting(),
                "location_name": "",
            },
        )
    raise exc