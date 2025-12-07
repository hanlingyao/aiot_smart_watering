import os
import json
import datetime
import base64
from typing import Dict, Any, Tuple

from openai import OpenAI

# 如果在包里，用相对导入
from .plant_recognition_module import identify_plant_plantnet, extract_scientific_name

# ========= 配置 =========
OPENAI_API_KEY = ""
PLANTNET_API_KEY = ""

client = OpenAI(api_key=OPENAI_API_KEY)


# ========= 工具函数 =========

def encode_image_to_base64(image_path: str) -> str:
    """读取本地图片文件并转为 base64 字符串（不包含 data: 前缀）"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def append_json_log(entry: dict, log_path: str):
    """
    追加一条记录到 JSON log 文件（数组形式存储）。
    """
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = []
    else:
        data = []

    data.append(entry)

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[LOG] Saved record to {log_path}")


def check_plant_name(image_path: str = "image.jpg") -> str:
    """
    优先从 sci_name.txt 读取植物学名；如果没有，则调用 PlantNet 识别并写入文件。
    """
    sci_file = "sci_name.txt"

    plant_name = ""
    if os.path.exists(sci_file):
        with open(sci_file, "r", encoding="utf-8") as f:
            plant_name = f.read().strip()

    if not plant_name:
        # 用 PlantNet 识别
        plantnet_result = identify_plant_plantnet(image_path, PLANTNET_API_KEY)
        plant_name = extract_scientific_name(plantnet_result)
        with open(sci_file, "w", encoding="utf-8") as f:
            f.write(plant_name)

    return plant_name


def get_sensor_data(sensor_log_path: str = "sensor_log.json") -> Tuple[float, float, float, float, float]:
    """
    从传感器日志中取最后一条数据：
    返回：
        soil_temperature_c, soil_moisture_percent, light_lux,
        air_temperature_c, air_humidity_percent
    """
    with open(sensor_log_path, "r", encoding="utf-8") as f:
        sensor_log = json.load(f)
    last = sensor_log[-1]

    soil_moisture_percent = last["soil_moisture_percent"]
    light_lux = last["light_lux"]
    soil_temperature_c = last["soil_temperature_c"]
    air_temperature_c = last["air_temperature_c"]
    air_humidity_percent = last["air_humidity_percent"]

    return soil_temperature_c, soil_moisture_percent, light_lux, air_temperature_c, air_humidity_percent


# ========= 合并后的 SYSTEM PROMPT =========

COMBINED_SYSTEM_PROMPT = """
You are an outdoor plant assistant with two tasks:

(1) Plant Health Assessment
(2) Irrigation Recommendation

You will receive:
- 1 plant photo (image input)
- plant_name: scientific name of the plant species
- pot_diameter: pot diameter (cm)
- pot_height: pot height (cm)
- soil_moisture_percent: soil moisture (0–100)
- light_lux: light level (lux)
- soil_temperature_c: soil temperature (°C)
- air_temperature_c: air temperature (°C)
- air_humidity_percent: air humidity (0–100%)
- will_rain_next_24h: expected rain in next 24h (true/false)
- rain_mm_next_24h: expected rainfall (mm)
- max_temp_next_24h_c: max air temp next 24h (°C)

========================
Task (1): Health Assessment
========================

Carefully inspect the plant image for visual signs of health or stress.
Combine image + plant_name + sensor data to judge health.

Health scale:
- 5 = healthy
- 4 = minor_issue
- 3 = slightly_unhealthy
- 2 = warning
- 1 = critical

For "reasons", you MUST output only short standardized tags from the following fixed list:

- need more light
- need less light
- light inconsistent
- drainage issue
- temperature too high
- temperature too low
- temperature fluctuating
- pest suspected
- disease suspected
- fungus suspected
- need pruning
- nutrient deficiency suspected
- overgrowth
- weak growth
- environmental stress
- uncertain assessment
- healthy

Rules for "reasons":
- Use 1–4 tags.
- Only use tags from this list.
- Do not invent new words or phrases.
- Do not explain the tags.
- If the plant is healthy, you may output exactly ["healthy"].

========================
Task (2): Irrigation Recommendation
========================

Use plant_name, pot size, soil_moisture_percent, light, temperature, humidity and 24h weather forecast.

Your task:
1. Decide whether the plant should be watered now.
2. If watering is needed, estimate water_ml (milliliters).
3. Suggest a target soil moisture range after watering.

========================
OUTPUT FORMAT (VERY IMPORTANT)
========================

Respond ONLY with ONE JSON object with EXACTLY TWO top-level keys:

{
  "health": {
    "health_level": integer 1–5,
    "reasons": array of 1–4 short tags (from the fixed list),
    "suggestions": array of 2–5 short English sentences
  },
  "irrigation": {
    "should_water": true or false,
    "water_ml": integer (0 if no watering is needed),
    "target_soil_moisture_percent_min": integer,
    "target_soil_moisture_percent_max": integer,
    "note": a very short English explanation (max 25 words)
  }
}

Rules:
- DO NOT add any extra keys at any level.
- DO NOT include any extra text outside the JSON.
"""


def build_combined_text_block(
    plant_name: str,
    pot_diameter: float,
    pot_height: float,
    soil_moisture_percent: float,
    will_rain_next_24h: bool,
    rain_mm_next_24h: float,
    max_temp_next_24h_c: float,
    light_lux: float,
    soil_temperature_c: float,
    air_temperature_c: float,
    air_humidity_percent: float,
) -> str:
    """
    构造给 GPT 的纯文本部分（和图片一起发）。
    """
    will_rain_str = "true" if will_rain_next_24h else "false"

    text = (
        f"plant_name: {plant_name}\n"
        f"pot_diameter: {pot_diameter}\n"
        f"pot_height: {pot_height}\n"
        f"soil_moisture_percent: {soil_moisture_percent}\n"
        f"will_rain_next_24h: {will_rain_str}\n"
        f"rain_mm_next_24h: {rain_mm_next_24h}\n"
        f"max_temp_next_24h_c: {max_temp_next_24h_c}\n"
        f"light_lux: {light_lux}\n"
        f"soil_temperature_c: {soil_temperature_c}\n"
        f"air_temperature_c: {air_temperature_c}\n"
        f"air_humidity_percent: {air_humidity_percent}\n"
    )
    return text


# ========= 主函数：一次 GPT 调用，返回两个结果 =========

def assess_health_and_irrigation(
    image_path: str,
    pot_diameter: float,
    pot_height: float,
    will_rain_next_24h: bool,
    rain_mm_next_24h: float,
    max_temp_next_24h_c: float,
    sensor_log_path: str = "sensor_log.json",
    model: str = "gpt-4o-mini",
) -> Dict[str, Any]:
    """
    一次性调用 GPT：
    - 输入：图片 + 传感器数据 + 花盆信息 + 天气信息
    - 输出：一个 JSON，包含 "health" 和 "irrigation" 两部分

    同时分别写入：
    - plant_health_log.json
    - irrigation_decision_log.json
    """

    # 1. 植物学名（从 sci_name.txt 或 PlantNet 得到）
    plant_name = check_plant_name(image_path=image_path)

    # 2. 传感器数据（最近一条）
    (
        soil_temperature_c,
        soil_moisture_percent,
        light_lux,
        air_temperature_c,
        air_humidity_percent,
    ) = get_sensor_data(sensor_log_path=sensor_log_path)

    # 3. 图片转 base64 → data URL
    base64_str = encode_image_to_base64(image_path)
    image_data_url = f"data:image/jpeg;base64,{base64_str}"

    # 4. 文本部分（所有数值 + 植物名 + 天气信息）
    text_block = build_combined_text_block(
        plant_name=plant_name,
        pot_diameter=pot_diameter,
        pot_height=pot_height,
        soil_moisture_percent=soil_moisture_percent,
        will_rain_next_24h=will_rain_next_24h,
        rain_mm_next_24h=rain_mm_next_24h,
        max_temp_next_24h_c=max_temp_next_24h_c,
        light_lux=light_lux,
        soil_temperature_c=soil_temperature_c,
        air_temperature_c=air_temperature_c,
        air_humidity_percent=air_humidity_percent,  # NOTE: see correction below
    )

    # !!! 注意：上面这行变量名应该是 air_humidity_percent，写代码时不要拼错
    # 这里为了防止你直接复制出错，下面我会给一个修正版本：
    # 把上一行改成：
    #    air_humidity_percent=air_humidity_percent,

    # 5. 构造 messages
    messages = [
        {"role": "system", "content": COMBINED_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": text_block},
                {
                    "type": "image_url",
                    "image_url": {"url": image_data_url},
                },
            ],
        },
    ]

    # 6. 调用 GPT
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
    )

    content = response.choices[0].message.content or ""
    content = content.strip()

    # 7. 处理可能出现的 ```json 包裹
    if content.startswith("```"):
        lines = content.splitlines()
        cleaned_lines = []
        for line in lines:
            if line.strip().startswith("```"):
                continue
            cleaned_lines.append(line)
        content = "\n".join(cleaned_lines).strip()

    # 8. 只取第一个 { 和最后一个 } 之间
    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1 and start < end:
        content = content[start : end + 1].strip()

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        raise ValueError(f"Model output is not valid JSON even after cleaning: {content}")

    # 9. 校验结构
    if "health" not in result or "irrigation" not in result:
        raise ValueError(f"Missing 'health' or 'irrigation' key: {result}")

    health = result["health"]
    irrigation = result["irrigation"]

    for key in ["health_level", "reasons", "suggestions"]:
        if key not in health:
            raise ValueError(f"Missing key in health: {key}")

    for key in [
        "should_water",
        "water_ml",
        "target_soil_moisture_percent_min",
        "target_soil_moisture_percent_max",
        "note",
    ]:
        if key not in irrigation:
            raise ValueError(f"Missing key in irrigation: {key}")

    # 10. 分别写入两个 log
    timestamp = datetime.datetime.now().isoformat()

    health_entry = {
        "timestamp": timestamp,
        "image_path": image_path,
        "plant_name": plant_name,
        "soil_temperature_c": soil_temperature_c,
        "soil_moisture_percent": soil_moisture_percent,
        "light_lux": light_lux,
        "air_temperature_c": air_temperature_c,
        "air_humidity_percent": air_humidity_percent,
        **health,
    }

    irrigation_entry = {
        "timestamp": timestamp,
        "plant_name": plant_name,
        "pot_diameter": pot_diameter,
        "pot_height": pot_height,
        "soil_moisture_percent": soil_moisture_percent,
        "will_rain_next_24h": will_rain_next_24h,
        "rain_mm_next_24h": rain_mm_next_24h,
        "max_temp_next_24h_c": max_temp_next_24h_c,
        "light_lux": light_lux,
        "soil_temperature_c": soil_temperature_c,
        "air_temperature_c": air_temperature_c,
        "air_humidity_percent": air_humidity_percent,
        **irrigation,
    }

    append_json_log(health_entry, "plant_health_log.json")
    append_json_log(irrigation_entry, "watering_log.json")

    return result


# ========= 示例运行 =========
if __name__ == "__main__":
    # 示例：手动传入花盆和天气信息
    demo_result = assess_health_and_irrigation(
        image_path="image.jpg",          # 你当前植物照片路径
        pot_diameter=18.0,               # 花盆直径 (cm)
        pot_height=20.0,                 # 花盆高度 (cm)
        will_rain_next_24h=True,
        rain_mm_next_24h=3.0,
        max_temp_next_24h_c=27.0,
        sensor_log_path="sensor_log.json",
        model="gpt-4o-mini",
    )

    print(json.dumps(demo_result, indent=2, ensure_ascii=False))
