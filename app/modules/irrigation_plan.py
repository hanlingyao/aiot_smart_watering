# main.py
from .plant_recognition_module import identify_plant_plantnet, extract_scientific_name
from .weather_module import get_24h_forecast
# from soil_moisture_module import TODO

from .ai_module import call_irrigation_assistant
from .ai_test import assess_health_and_irrigation

PLANTNET_API_KEY = ""

def irrigation_plan(
        image_path: str,
        plant_name: str,
        pot_diameter: float,
        pot_height: float,
        ) -> str:

    # 1. Get soil moisture TODO
    with open("sensor_log.json","r") as f:
        sensor_log = json.load(f)[-1] # the most recent data
    soil_moisture, light_lux, soil_temprature_c, air_temperature_c, air_humidity_percent = \
        sensor_log["soil_moisture_percent"], sensor_log["light_lux"], sensor_log["soil_temperature_c"], sensor_log["air_temperature_c"], sensor_log["air_humidity_percent"] 

    # 2. Get Weather
    will_rain_next_24h, rain_mm_next_24h, max_temp_next_24h_c = \
        get_24h_forecast()["rain_expected"], get_24h_forecast()["max_rain"], get_24h_forecast()["max_temperature"]
    print("🌧️ Weather Forecast: ", get_24h_forecast())


    # 3. Irrigation Plan
    # irrigation_plan = call_irrigation_assistant(
    #     plant_name=plant_name,
    #     pot_diameter=pot_diameter,
    #     pot_height=pot_height,
    #     soil_moisture_percent=soil_moisture,
    #     will_rain_next_24h=will_rain_next_24h,
    #     rain_mm_next_24h=rain_mm_next_24h,
    #     max_temp_next_24h_c=max_temp_next_24h_c,
    #     light_lux=light_lux,
    #     soil_temprature_c=soil_temprature_c,
    #     air_temperature_c=air_temperature_c,
    #     air_humidity_percent=air_humidity_percent
    # )
    irrigation_plan = assess_health_and_irrigation(
        image_path="image.jpg",
        pot_diameter=pot_diameter,
        pot_height=pot_height,
        will_rain_next_24h=will_rain_next_24h,
        rain_mm_next_24h=rain_mm_next_24h,
        max_temp_next_24h_c=max_temp_next_24h_c,
    )

    print("💧 Irrigation Plan：", irrigation_plan)
    return irrigation_plan


import json
if __name__ == "__main__":
    image_path = "image.jpg"
    plantnet_result = identify_plant_plantnet(image_path, PLANTNET_API_KEY)
    sci_name = extract_scientific_name(plantnet_result)
    print("✅ Plant Name:", sci_name)

    pot_path = "pot_info.json"
    with open(pot_path,"r") as f:
        pot_info = json.load(f)
    pot_diameter, pot_height = pot_info["pot_diameter"], pot_info["pot_height"]
 
    irrigation_plan(
                    image_path=image_path,
                    plant_name=sci_name,
                    pot_diameter=pot_diameter,
                    pot_height=pot_height,
                    )