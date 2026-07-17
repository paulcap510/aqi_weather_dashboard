import os
import requests
from datetime import timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

from timezonefinder import TimezoneFinder

load_dotenv()

# Queens, NY
LATITUDE = 40.71709
LONGITUDE = -73.88056
# ZIP_CODE = "11379"

TIMEZONE = TimezoneFinder().timezone_at(lat=LATITUDE, lng=LONGITUDE)

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


def get_current_weather(latitude: float, longitude: float):
    """Fetch temp, feels-like, humidity, dewpoint, and wind from NWS."""
    headers = {"User-Agent": NWS_USER_AGENT}

    # Step 1: find which observation stations serve this location
    points_url = f"https://api.weather.gov/points/{latitude},{longitude}"
    points_response = requests.get(points_url, headers=headers)
    points_response.raise_for_status()
    stations_url = points_response.json()["properties"]["observationStations"]

    # Step 2: get the list of nearby stations, use the first (nearest) one
    stations_response = requests.get(stations_url, headers=headers)
    stations_response.raise_for_status()
    station_url = stations_response.json()["features"][0]["id"]

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


def get_current_aqi(latitude: float, longitude: float):
    api_key = os.environ.get("AIRNOW_API_KEY")
    if not api_key:
        raise RuntimeError(
            "AIRNOW_API_KEY environment variable is not set. "
            "Sign up at docs.airnowapi.org and set this before running."
        )

    url = "https://www.airnowapi.org/aq/observation/latLong/current/"
    params = {
        "format": "application/json",
        "latitude": latitude,
        "longitude": longitude,
        "distance": 25,
        "API_KEY": api_key,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    observations = response.json()

    if not observations:
        raise RuntimeError("AirNow returned no observations for this location")

    # AirNow returns one entry per pollutant (O3, PM2.5, PM10, etc).
    # The AQI reported to the public is the WORST of these, which is EPA convention.
    return max(obs["AQI"] for obs in observations)


def get_current_uv(latitude: float, longitude: float):
    """Fetch current UV index from Open-Meteo's air-quality endpoint.

    Switched away from EPA Envirofacts after discovering its hourly UV
    forecast isn't stable -- two back-to-back tests showed the same
    hour's forecast value changing significantly within minutes.
    """
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "uv_index",
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    return data["current"]["uv_index"]


def get_coordinates_for_city(city_name):
    """Given a city name, return (latitude, longitude, display_name).
    Isolated and standalone. Does not affect any existing function."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city_name, "count": 1}
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    results = data.get("results")
    if not results:
        raise ValueError(f"No location found for '{city_name}'")

    result = results[0]
    display_name = f"{result['name']}, {result.get('admin1', '')}".rstrip(", ")
    return result["latitude"], result["longitude"], display_name


if __name__ == "__main__":
    print("Weather (NWS):")
    weather = get_current_weather(LATITUDE, LONGITUDE)
    for key, value in weather.items():
        print(f"  {key}: {value}")

    print()
    print("AQI (AirNow):")
    try:
        print(" ", get_current_aqi(LATITUDE, LONGITUDE))
    except RuntimeError as e:
        print("  ERROR:", e)

    print()
    print("Geocoding test:")
    lat, lon, name = get_coordinates_for_city("Miami")
    print(f"{name} -> ({lat}, {lon})")

    print()
    print("UV (Open-Meteo):")
    print(" ", get_current_uv(LATITUDE, LONGITUDE))



