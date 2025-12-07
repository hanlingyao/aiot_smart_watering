import requests
import json

OPENWEATHER_API_KEY=""

def get_24h_forecast():
    """
    Returns:
    - max_temperature (°C)
    - rain_expected (True/False)
    - max_rain (mm)
    """

    api_key = OPENWEATHER_API_KEY

    location_path = "pot_info.json"
    with open(location_path,"r") as f:
        loc_info = json.load(f)
    lat, lon = loc_info["latitude"], loc_info["longitude"]


    url = "https://api.openweathermap.org/data/2.5/forecast"

    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric"   # Celsius
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        forecast_list = data["list"]  # Each entry is 3-hour step
        next_24h = forecast_list[:8]  # 8 entries = 24 hours

        # Max temperature
        max_temp = max(item["main"]["temp"] for item in next_24h)

        # Rain info
        max_rain = 0.0
        rain_expected = False

        for item in next_24h:
            if "rain" in item:
                rain_amount = item["rain"].get("3h", 0)
                if rain_amount > 0:
                    rain_expected = True
                    max_rain = max(max_rain, rain_amount)
        
        return {
            "rain_expected": rain_expected,
            "max_rain": max_rain if rain_expected else 0.0,
            "max_temperature": max_temp
        }

    except Exception as e:
        print("❌ Failed to fetch forecast:", e)
        return None


# Test output
if __name__ == "__main__":
    result = get_24h_forecast()
    print(result)
