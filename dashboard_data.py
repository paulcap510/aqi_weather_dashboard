from datetime import datetime, timedelta
import requests
from fetch_weather import get_current_weather, get_current_aqi, get_current_uv, LATITUDE, LONGITUDE
from thresholds import (
    rate_aqi,
    rate_dewpoint,
    rate_uv,
    rate_temp,
    rate_humidity,
    rate_feels_like,
    rate_wind,
)


def get_dashboard_data(latitude: float, longitude: float):
    current_weather = get_current_weather(latitude, longitude)
    aqi_value = get_current_aqi(latitude, longitude)
    uv_value = get_current_uv(latitude, longitude)

    metrics = {
        "aqi": (aqi_value, rate_aqi),
        "dewpoint": (current_weather["dewpoint_f"], rate_dewpoint),
        "uv": (uv_value, rate_uv),
        "temp": (current_weather["temp_f"], rate_temp),
        "feels_like": (current_weather["feels_like_f"], rate_feels_like),
        "humidity": (current_weather["humidity_pct"], rate_humidity),
        "wind": (current_weather["wind_mph"], rate_wind),
    }

    results = {}
    for name, (value, rate_function) in metrics.items():
        rating = rate_function(value)
        results[name] = {"value": value, "rating": rating}

    return results

# _cache = {"data": None, "fetched_at": None}
# CACHE_DURATION = timedelta(minutes=15)
#! Caching layer = One cache entry PER (latitude, longitude) pair, so different cities don't overwrite each other
_cache = {}
CACHE_DURATION = timedelta(minutes=15)


def get_dashboard_data_cached(latitude, longitude):
    now = datetime.now()
    location_key = (latitude, longitude)

    location_is_new = location_key not in _cache
    if location_is_new:
        cache_is_stale = True
    else:
        fetched_at = _cache[location_key]["fetched_at"]
        cache_is_stale = (now - fetched_at) > CACHE_DURATION

    if location_is_new or cache_is_stale:
        try:
            _cache[location_key] = {
                "data": get_dashboard_data(latitude, longitude),
                "fetched_at": now,
            }
        except (requests.exceptions.RequestException, RuntimeError, KeyError):
            # If this location has never been successfully fetched before,
            # there's nothing to fall back to -- surface that as no data.
            if location_is_new:
                return None
            # Otherwise, keep serving this location's last good data.

    return _cache[location_key]["data"]



if __name__ == "__main__":
    data = get_dashboard_data_cached(LATITUDE, LONGITUDE)
    for metric_name, metric_info in data.items():
        print(metric_name, ":", metric_info["value"], metric_info["rating"])