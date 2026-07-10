import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

# Queens, NY
LATITUDE = 40.71709
LONGITUDE = -73.88056
# ZIP_CODE = "11379"


NWS_USER_AGENT = os.environ.get("NWS_USER_AGENT")
if not NWS_USER_AGENT:
    raise RuntimeError(
        "NWS_USER_AGENT environment variable is not set. "
        "Add it to your .env file before running."
    )


def celsius_to_fahrenheit(celsius):
    if celsius is None:
        return None
    return celsius * 9 / 5 + 32


def kmh_to_mph(kmh):
    if kmh is None:
        return None
    return kmh * 0.621371


def safe_round(value, digits=1):
    if value is None:
        return None
    return round(value, digits)


def get_current_weather():
    """Fetch temp, feels-like, humidity, dewpoint, and wind from NWS."""
    headers = {"User-Agent": NWS_USER_AGENT}

    # Step 1: find which observation stations serve this location
    points_url = f"https://api.weather.gov/points/{LATITUDE},{LONGITUDE}"
    points_response = requests.get(points_url, headers=headers)
    points_response.raise_for_status()
    stations_url = points_response.json()["properties"]["observationStations"]

    # Step 2: get the list of nearby stations, use the first (nearest) one
    stations_response = requests.get(stations_url, headers=headers)
    stations_response.raise_for_status()
    station_url = stations_response.json()["features"][0]["id"]
    print("DEBUG: using weather station:", stations_response.json()["features"][0]["properties"]["name"])

    # Step 3: get that station's latest actual observation
    obs_response = requests.get(f"{station_url}/observations/latest", headers=headers)
    obs_response.raise_for_status()
    props = obs_response.json()["properties"]

    temp_f = celsius_to_fahrenheit(props["temperature"]["value"])
    dewpoint_f = celsius_to_fahrenheit(props["dewpoint"]["value"])
    humidity_pct = props["relativeHumidity"]["value"]
    wind_mph = kmh_to_mph(props["windSpeed"]["value"])

    # heatIndex/windChill are only present when relevant (hot/cold enough).
    # Fall back to plain temperature the rest of the time.
    heat_index_f = celsius_to_fahrenheit(props["heatIndex"]["value"])
    wind_chill_f = celsius_to_fahrenheit(props["windChill"]["value"])
    if heat_index_f is not None:
        feels_like_f = heat_index_f
    elif wind_chill_f is not None:
        feels_like_f = wind_chill_f
    else:
        feels_like_f = temp_f

    return {
        "temp_f": safe_round(temp_f, 1),
        "feels_like_f": safe_round(feels_like_f, 1),
        "humidity_pct": safe_round(humidity_pct, 0),
        "dewpoint_f": safe_round(dewpoint_f, 1),
        "wind_mph": safe_round(wind_mph, 1),
    }


def get_current_aqi():
    api_key = os.environ.get("AIRNOW_API_KEY")
    if not api_key:
        raise RuntimeError(
            "AIRNOW_API_KEY environment variable is not set. "
            "Sign up at docs.airnowapi.org and set this before running."
        )

    url = "https://www.airnowapi.org/aq/observation/latLong/current/"
    params = {
        "format": "application/json",
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "distance": 25,
        "API_KEY": api_key,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    observations = response.json()
    print("DEBUG: AQI readings by area:", [(o["ReportingArea"], o["ParameterName"], o["AQI"]) for o in observations])

    if not observations:
        raise RuntimeError("AirNow returned no observations for this location")

    # AirNow returns one entry per pollutant (O3, PM2.5, PM10, etc).
    # The AQI reported to the public is the WORST of these, which is EPA convention.
    return max(obs["AQI"] for obs in observations)


def get_current_uv():
    """Fetch current UV index from Open-Meteo's air-quality endpoint.

    Switched away from EPA Envirofacts after discovering its hourly UV
    forecast isn't stable -- two back-to-back tests showed the same
    hour's forecast value changing significantly within minutes.
    """
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "current": "uv_index",
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    return data["current"]["uv_index"]

# def get_current_uv():
#     """Fetch the current UV index from EPA Envirofacts (hourly forecast),
#     interpolated between the current and next hour's values.

#     EPA only gives one value per whole hour, but real UV rises and falls
#     continuously through the day. Snapping to the start-of-hour value
#     alone can be noticeably off, especially near the top of the next
#     hour (e.g. at 9:51, most of the way from the 9 AM value toward the
#     10 AM value already). Interpolating between the two gives a closer
#     approximation of what's actually happening right now.
#     """
#     url = f"https://data.epa.gov/dmapservice/getEnvirofactsUVHOURLY/ZIP/{ZIP_CODE}/JSON"
#     response = requests.get(url)
#     response.raise_for_status()
#     data = response.json()

#     if not data:
#         raise RuntimeError(f"EPA UV API returned no data for ZIP {ZIP_CODE}")

#     #! Needs to be changed when we allow searching
#     eastern_now = datetime.now(ZoneInfo("America/New_York")).replace(tzinfo=None)

#     parsed_entries = [
#         (datetime.strptime(entry["DATE_TIME"], "%b/%d/%Y %I %p"), entry["UV_VALUE"])
#         for entry in data
#     ]

#     #! This calculates how much of the hour has passed to get a more accurate UV esimate
#     current_value = None
#     next_value = None
#     for i, (entry_time, value) in enumerate(parsed_entries):
#         if entry_time.date() == eastern_now.date() and entry_time.hour == eastern_now.hour:
#             current_value = value
#             if i + 1 < len(parsed_entries):
#                 next_value = parsed_entries[i + 1][1]
#             break

#     if current_value is None:
#         return 0.0

#     if next_value is None:
#         return float(current_value)

#     fraction_through_hour = (eastern_now.minute + eastern_now.second / 60) / 60

#     interpolated = current_value + (next_value - current_value) * fraction_through_hour
#     print(f"DEBUG: now={eastern_now}, current_hour_value={current_value}, next_hour_value={next_value}, fraction={fraction_through_hour:.2f}, result={interpolated:.2f}")
#     return round(interpolated, 1)


if __name__ == "__main__":
    print("Weather (NWS):")
    weather = get_current_weather()
    for key, value in weather.items():
        print(f"  {key}: {value}")

    print()
    print("AQI (AirNow):")
    try:
        print(" ", get_current_aqi())
    except RuntimeError as e:
        print("  ERROR:", e)

    print()
    print("UV (Open-Meteo):")
    print(" ", get_current_uv())
