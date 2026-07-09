from datetime import timedelta, datetime
import requests
from fetch_weather import get_current_weather, get_current_air_quality
from thresholds import (
    rate_aqi,
    rate_dewpoint,
    rate_uv,
    rate_temp,
    rate_humidity,
    rate_feels_like,
    rate_wind,
)


def get_dashboard_data():
    current_weather = get_current_weather()
    current_air_quality = get_current_air_quality()

    metrics = {
        "aqi": (current_air_quality["aqi"], rate_aqi),
        "dewpoint": (current_weather["dewpoint_f"], rate_dewpoint),
        "uv": (current_air_quality["uv_index"], rate_uv),
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


if __name__ == "__main__":
    data = get_dashboard_data()
    for metric_name, metric_info in data.items():
        print(metric_name, ":", metric_info["value"], metric_info["rating"])



#! CACHING
#* Instead of calling Open-Meteo on every page load, we remember the last result and re-use loads that
#* are recent enough

_cache = {"data": None, "fetched_at": None}
CACHE_DURATION = timedelta(minutes=15)

def get_dashboard_data_cached():
    now = datetime.now()

    cache_is_empty = _cache["data"] is None
    cache_is_stale = (
        _cache["fetched_at"] is None
        or (now - _cache["fetched_at"]) > CACHE_DURATION
    )

    if cache_is_empty or cache_is_stale:
        try:
            _cache["data"] = get_dashboard_data()
            _cache["fetched_at"] = now
        except requests.exceptions.RequestException:
            pass

    return _cache["data"]


if __name__ == "__main__":
    data = get_dashboard_data_cached()
    for metric_name, metric_info in data.items():
        print(metric_name, ":", metric_info["value"], metric_info["rating"])
