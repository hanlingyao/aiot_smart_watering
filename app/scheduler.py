import time
import os
from modules.main import main
import json
from datetime import datetime
# from modules.ai_image_module import assess_plant_health
from modules.ai_test import assess_health_and_irrigation
from modules.weather_module import get_24h_forecast

WATERING_LOG_FILE = "watering_log.json"
HEALTH_LOG_FILE = "plant_health_log.json"

def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def append_watering_log(water_ml, status):
    log = load_json(WATERING_LOG_FILE, [])
    now = datetime.now()

    log.append({
        "timestamp": now.isoformat(timespec="seconds"),
        "date": now.date().isoformat(),
        "water_ml": water_ml,         # 0 if not watered
        "reason": status,             # "watered" / "skipped"
    })

    save_json(WATERING_LOG_FILE, log)

def append_health_log(health):
    log = load_json(HEALTH_LOG_FILE, [])
    now = datetime.now()

    log.append({
        "timestamp": now.isoformat(timespec="seconds"),
        "date": now.date().isoformat(),
        **health
    })

    save_json(HEALTH_LOG_FILE, log)


def loop():
    while True:
        # watering_result = main()
        # should_water = watering_result.get("should_water", False)
        # note = watering_result.get("note", "No note")

        # # if should_water:
        # #     water_ml = watering_result.get("water_ml", 0)
        # #     # TODO: 控制水泵浇水
        # #     append_watering_log(water_ml, note)
        # # else:
        # #     append_watering_log(0, note)


        folder = "images"

        files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        files.sort()

        if files:
            image_path = files[-1]
        else:
            image_path = ""
            print("no files found")

        # with open("sci_name.txt", "r", encoding="utf-8") as f:
        #     plant_name = f.readline().strip()

        # # assess_plant_health(image_path=folder+'/'+image_path,
        #                     # plant_name=plant_name,
        #                     # )
        pot_path = "pot_info.json"
        with open(pot_path,"r") as f:
            pot_info = json.load(f)
        pot_diameter, pot_height = pot_info["pot_diameter"], pot_info["pot_height"]

        will_rain_next_24h, rain_mm_next_24h, max_temp_next_24h_c = get_24h_forecast()
        if image_path:
            image_path = "images/"+image_path
        else:
            image_path = "image.jpg"
        assess_health_and_irrigation(
            image_path=image_path,
            pot_diameter=pot_diameter,
            pot_height=pot_height,
            will_rain_next_24h=will_rain_next_24h,
            rain_mm_next_24h=rain_mm_next_24h,
            max_temp_next_24h_c=max_temp_next_24h_c,
        )

        time.sleep(5)  # 24 hours




if __name__ == "__main__":
    loop()
