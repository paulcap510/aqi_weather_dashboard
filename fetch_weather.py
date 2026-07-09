import requests

# Brooklyn, NY coordinates
LATITUDE = 40.742054
LONGITUDE = -73.769417


def get_current_weather():
    # Fetch data from Open Metro API
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "current": "temperature_2m,relative_humidity_2m,dew_point_2m,apparent_temperature,wind_speed_10m",
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    current = data["current"]

    return {
        "temp_f": current["temperature_2m"],
        "feels_like_f": current["apparent_temperature"],
        "humidity_pct": current["relative_humidity_2m"],
        "dewpoint_f": current["dew_point_2m"],
        "wind_mph": current["wind_speed_10m"],
    }


def get_current_air_quality():
    """Fetch US AQI and UV index from Open-Meteo's air-quality API."""
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "current": "us_aqi,uv_index",
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    current = data["current"]

    return {
        "aqi": current["us_aqi"],
        "uv_index": current["uv_index"],
    }


if __name__ == "__main__":
    weather = get_current_weather()
    air_quality = get_current_air_quality()

    print("Current weather (Brooklyn, NY):")
    for key, value in weather.items():
        print(f"  {key}: {value}")

    print()
    print("Current air quality (Brooklyn, NY):")
    for key, value in air_quality.items():
        print(f"  {key}: {value}")