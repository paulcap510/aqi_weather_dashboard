THRESHOLDS = {
    "dewpoint_f": {
        "green_max": 58,
        "yellow_max": 65,

    },
    "aqi": {
        "green_max": 60,
        "yellow_max": 100,
    },
    "temp_f": {
        "green_min": 50,
        "green_max": 78,
        "yellow_max": 85,
    },
    "humidity_pct": {
        "low_max": 30,
        "high_min": 60,
    },
    "uv_index": {
        "low_max": 2,
        "moderate_max": 5,
        "high_max": 7,
        "very_high_max": 10,
    },
    "wind_mph": None,
    "pollen": None, #* Relevant for asthma
}


def rate_dewpoint(dewpoint_f: float) -> str:
    if dewpoint_f is None:
        return None
    cfg = THRESHOLDS["dewpoint_f"]
    if dewpoint_f < cfg["green_max"]:
        return "green"
    elif dewpoint_f <= cfg["yellow_max"]:
        return "yellow"
    else:
        return "red"


def rate_aqi(aqi: float) -> str:
    if aqi is None:
        return None
    cfg = THRESHOLDS["aqi"]
    if aqi < cfg["green_max"]:
        return "green"
    elif aqi <= cfg["yellow_max"]:
        return "yellow"
    else:
        return "red"


def rate_temp(temp_f: float) -> str | None:
    if temp_f is None:
        return None
    cfg = THRESHOLDS["temp_f"]
    if temp_f < cfg["green_min"]:
        return None
    elif temp_f <= cfg["green_max"]:
        return "green"
    elif temp_f <= cfg["yellow_max"]:
        return "yellow"
    else:
        return "red"

def rate_wind(wind_mph: float) -> str | None:
    return None

#! Incorporate later
def rate_pollen(pollen_level) -> str | None:
    return None


def rate_feels_like(feels_like_f: float) -> str | None:
    if feels_like_f is None:
        return None
    cfg = THRESHOLDS["temp_f"]
    if feels_like_f < cfg["green_min"]:
        return None
    elif feels_like_f <= cfg["green_max"]:
        return "green"
    elif feels_like_f <= cfg["yellow_max"]:
        return "yellow"
    else:
        return "red"


def rate_humidity(humidity_pct: float) -> str:
    if humidity_pct is None:
        return None
    cfg = THRESHOLDS["humidity_pct"]
    if humidity_pct < cfg["low_max"]:
        return "low"
    elif humidity_pct <= cfg["high_min"]:
        return "average"
    else:
        return "high"


def rate_uv(uv_index: float) -> str:
    if uv_index is None:
        return None
    cfg = THRESHOLDS["uv_index"]
    if uv_index <= cfg["low_max"]:
        return "low"
    elif uv_index <= cfg["moderate_max"]:
        return "moderate"
    elif uv_index <= cfg["high_max"]:
        return "high"
    elif uv_index <= cfg["very_high_max"]:
        return "very high"
    else:
        return "extreme"