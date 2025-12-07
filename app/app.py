import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, jsonify
from modules.main import check_plant_name

app = Flask(__name__)

# ========== 文件路径：保证和 app.py 同目录 ==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

WATERING_LOG_FILE = os.path.join(BASE_DIR, "watering_log.json")
SENSOR_LOG_FILE = os.path.join(BASE_DIR, "sensor_log.json")
POT_INFO_FILE = os.path.join(BASE_DIR, "pot_info.json")
HEALTH_LOG_FILE = os.path.join(BASE_DIR, "plant_health_log.json")
SCI_NAME_FILE = os.path.join(BASE_DIR, "sci_name.txt")

# ========== 工具函数 ==========

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("[load_json] 读取失败:", path, "error:", e)
        return default


def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[save_json] 已写入: {path}，当前记录数: {len(data)}")
    except Exception as e:
        print("[save_json] 写入失败:", path, "error:", e)


# ========== 主面板信息：完全从 watering_log.json 里算 ==========
def get_today_panel_info():
    today = datetime.now().date().isoformat()
    watering_log = load_json(WATERING_LOG_FILE, default=[])

    today_records = []
    for r in watering_log:
        date_str = r.get("date")

        # 如果没有 date，就尝试从 timestamp 推出日期
        if not date_str:
            ts = r.get("timestamp")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts)
                    date_str = dt.date().isoformat()
                except Exception:
                    pass

        if date_str == today:
            today_records.append(r)

    # 计算今天总浇水量
    today_total_ml = 0.0
    for r in today_records:
        try:
            today_total_ml += float(r.get("water_ml", 0) or 0)
        except (TypeError, ValueError):
            continue

    # 找到今天最新的一条记录（用来显示时间 & note）
    last_watering_time = None
    last_reason = None
    if today_records:
        today_records_sorted = sorted(
            today_records, key=lambda x: x.get("timestamp", "")
        )
        last_record = today_records_sorted[-1]
        last_watering_time = last_record.get("timestamp")
        last_reason = last_record.get("reason") or last_record.get("note")

    if today_records and today_total_ml > 0:
        status = "watered"
        if last_reason:
            note = last_reason
        else:
            note = f"The total amount of water watered today: <strong>{today_total_ml} ml</strong>"
    else:
        status = "no_water"
        if last_reason:
            note = last_reason
        else:
            note = "There is no automatic watering record yet."

    return {
        "status": status,
        "today_total_ml": today_total_ml,
        "note": note,
        "last_watering_time": last_watering_time,
    }


# ========== 读取最新的植物健康评估结果 ==========
def get_latest_health_panel():
    """
    从 plant_health_log.json 中读取最新一条健康评估结果。
    日志格式示例：
    [
      {
        "timestamp": "2025-12-06T12:30:05",
        "image_path": "./plant.jpg",
        "health_level": 4,
        "reasons": ["overwatered", "need more light"],
        "suggestions": [...]
      },
      ...
    ]
    """
    health_log = load_json(HEALTH_LOG_FILE, default=[])

    if not isinstance(health_log, list) or not health_log:
        return None

    # 按时间排序，取最新一条
    try:
        health_log_sorted = sorted(
            health_log, key=lambda x: x.get("timestamp", "")
        )
        last = health_log_sorted[-1]
    except Exception as e:
        print("[get_latest_health_panel] 排序失败:", e)
        return None

    health_level = last.get("health_level")
    try:
        health_level = int(health_level)
    except Exception:
        health_level = None

    reasons = last.get("reasons") or []
    if not isinstance(reasons, list):
        reasons = [str(reasons)]

    # 颜色映射：从绿到红
    color_map = {
        5: "#4CAF50",  # 绿色
        4: "#8BC34A",  # 黄绿
        3: "#FFC107",  # 琥珀
        2: "#FF9800",  # 橙色
        1: "#F44336",  # 红色
    }
    color = color_map.get(health_level, "#9E9E9E")  # 默认灰色

    return {
        "health_level": health_level,
        "reasons": reasons,
        "color": color,
        "timestamp": last.get("timestamp"),
    }

def reset_all():
    """
    重置系统：删除 images 里的图片，清空所有 log / txt 文件。
    """
    # 1. 清空 images 文件夹里的图片
    if os.path.exists(IMAGES_DIR):
        for name in os.listdir(IMAGES_DIR):
            path = os.path.join(IMAGES_DIR, name)
            if os.path.isfile(path):
                try:
                    os.remove(path)
                except Exception as e:
                    print("Failed to delete image:", path, e)
    
    os.remove("image.jpg")

    # 2. 清空 JSON 文件
    save_json(HEALTH_LOG_FILE, [])   # 植物健康评估记录
    save_json(POT_INFO_FILE, {})           # 花盆信息
    save_json(SENSOR_LOG_FILE, [])         # 传感器数据
    save_json(WATERING_LOG_FILE, [])       # 浇水记录

    # 3. 清空 sci_name.txt（植物学名）
    try:
        with open(SCI_NAME_FILE, "w", encoding="utf-8") as f:
            f.write("")
    except Exception as e:
        print("清空 sci_name.txt 失败:", e)



# ========== 首页：主面板 + 近期浇水记录 ==========
@app.route("/")
def index():
    today = datetime.now().date().isoformat()

    # 1）主面板信息
    panel = get_today_panel_info()
    today_flag = panel.get("status")         # "watered" / "no_water"
    today_total_ml = panel.get("today_total_ml", 0)
    today_note = panel.get("note")
    last_watering_time = panel.get("last_watering_time")

    # 2）近期浇水记录（最近15天）
    watering_log = load_json(WATERING_LOG_FILE, default=[])
    watering_log = [x for x in watering_log if x.get("water_ml", 0) > 0]

    now = datetime.now()
    cutoff = now - timedelta(days=15)

    filtered = []
    for entry in watering_log:
        ts = entry.get("timestamp")
        if not ts:
            continue

        try:
            dt = datetime.fromisoformat(ts)
        except Exception:
            continue

        if dt >= cutoff:
            filtered.append(entry)

    recent_records = sorted(
        filtered, key=lambda x: x.get("timestamp", ""), reverse=True
    )

    # 3）花盆信息
    pot_info = load_json(POT_INFO_FILE, default={})

    # 4）植物健康信息（来自 plant_health_log.json）
    health_panel = get_latest_health_panel()


    plant_name = check_plant_name()

    return render_template(
        "index.html",
        today=today,
        today_flag=today_flag,
        today_total_ml=today_total_ml,
        today_note=today_note,
        last_watering_time=last_watering_time,
        recent_records=recent_records,
        pot_info=pot_info,
        health_panel=health_panel,  # 新增：传给模板
        plant_name=plant_name
    )


# ========== API：自动浇水系统上报“浇水事件” ==========
@app.route("/api/report_watering", methods=["POST"])
def report_watering():
    try:
        data = request.get_json(force=True, silent=False)
    except Exception as e:
        print("[/api/report_watering] get_json error:", e)
        return jsonify({"status": "error", "msg": "invalid json"}), 400

    if not data or "water_ml" not in data:
        return jsonify({"status": "error", "msg": "water_ml required"}), 400

    try:
        water_ml = float(data["water_ml"])
    except ValueError:
        return jsonify({"status": "error", "msg": "water_ml must be number"}), 400

    now = datetime.now()
    record = {
        "timestamp": now.isoformat(timespec="seconds"),
        "date": now.date().isoformat(),
        "water_ml": water_ml,
        "reason": data.get("reason"),
        "soil_moisture_before": data.get("soil_moisture_before"),
        "soil_moisture_after": data.get("soil_moisture_after"),
        "source": "auto",
    }

    log = load_json(WATERING_LOG_FILE, default=[])
    log.append(record)
    save_json(WATERING_LOG_FILE, log)

    return jsonify({"status": "ok"})

# ========== 重置植物 ==========
# @app.route("/reset", methods=["POST"])
# def reset_route():
#     reset_all()
#     # 重置后回到主页
#     return redirect(url_for("index"))
@app.route("/reset", methods=["POST"])
def reset_route():
    reset_all()
    # 重置完成后，不回 index，而是进入引导页 /setup
    return redirect(url_for("setup"))

@app.route("/setup", methods=["GET", 'POST'])
def setup():
    """
    第一次使用 / 重置之后的引导页面：
    - 上传植物图片
    - 填写花盆信息
    - 填写经纬度（可用“获取当前定位”按钮）
    填完后保存，并跳转到 index。
    """
    if request.method == "POST":
        # 1. 处理图片上传
        file = request.files.get("plant_image")

        if file and file.filename:
            file.save("image.jpg")


        # 2. 读取表单的花盆信息和位置信息
        pot_diameter = request.form.get("pot_diameter", type=float)
        pot_height = request.form.get("pot_height", type=float)
        latitude = request.form.get("latitude", "")
        longitude = request.form.get("longitude", "")

        pot_info = {
            "pot_diameter": pot_diameter,
            "pot_height": pot_height,
            "latitude": latitude,
            "longitude": longitude,
        }
        

        save_json(POT_INFO_FILE, pot_info)

        # 这里以后也可以顺便触发一次健康评估等逻辑

        return redirect(url_for("index"))

    # GET 请求：展示表单（如果已经有 pot_info，就当作默认值）
    pot_info = load_json(POT_INFO_FILE, default={})
    return render_template("setup.html", pot_info=pot_info)



# ========== 接收传感器信息，写入 sensor_log.json ==========
@app.route("/upload", methods=["POST"])
def upload_sensor():
    """
    接收板子上传的传感器数据，追加写入 SENSOR_LOG_FILE（sensor_log.json）。
    你现在 ESP32 发的 payload 已经 OK，不需要改。
    """
    print("\n[/upload] 收到请求，remote_addr =", request.remote_addr)

    try:
        data = request.get_json(force=True, silent=False)
    except Exception as e:
        print("[/upload] get_json error:", e)
        return jsonify({"status": "error", "msg": "invalid json"}), 400

    print("[/upload] 原始 JSON:", data)

    if not isinstance(data, dict):
        print("[/upload] JSON 不是对象，丢弃")
        return jsonify({"status": "error", "msg": "json must be object"}), 400

    now = datetime.now()
    record = {
        "timestamp": now.isoformat(timespec="seconds"),
        "date": now.date().isoformat(),
        "remote_addr": request.remote_addr,
    }
    record.update(data)

    sensor_log = load_json(SENSOR_LOG_FILE, default=[])
    sensor_log.append(record)
    save_json(SENSOR_LOG_FILE, sensor_log)

    print("[/upload] 已追加一条记录，目前总条数:", len(sensor_log))
    return jsonify({"status": "ok"}), 200


# ========== 接收摄像头照片，保存图片 ==========
@app.route("/esp32_upload", methods=["POST"])
def esp32_upload():

    img_bytes = request.get_data(cache=False)

    if not img_bytes:
        return jsonify({"status": "error", "msg": "empty body"}), 400

    # 文件名：20251207_142205.jpg
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{ts}.jpg"
    save_path = os.path.join(IMAGES_DIR, filename)

    try:
        with open(save_path, "wb") as f:
            f.write(img_bytes)
    except Exception as e:
        print("[/esp32_upload] 保存失败:", e)
        return jsonify({"status": "error", "msg": "failed to save file"}), 500

    print(f"[/esp32_upload] ✅Image Saved: {save_path}")

    return jsonify({
        "status": "ok",
        "filename": filename,
    }), 200


# ========== 可视化页面 ==========
@app.route("/dashboard")
def dashboard():
    sensor_log = load_json(SENSOR_LOG_FILE, default=[])
    pot_info = load_json(POT_INFO_FILE, default={})  # 给 base.html 的花盆弹窗用

    now = datetime.now()
    cutoff = now - timedelta(hours=24)

    def in_last_24h(rec):
        ts = rec.get("timestamp")
        if not ts:
            return False
        try:
            dt = datetime.fromisoformat(ts)
            return dt >= cutoff
        except Exception:
            return False

    recent_sensor_data = [r for r in sensor_log if in_last_24h(r)]
    recent_sensor_data.sort(key=lambda x: x.get("timestamp", ""))

    return render_template(
        "dashboard.html",
        sensor_data=recent_sensor_data,
        pot_info=pot_info,   # 🔴 关键：传给 base.html
    )



# ========== 读取sensor历史信息（API） ==========
@app.route("/api/sensor_24h")
def api_sensor_24h():
    sensor_log = load_json(SENSOR_LOG_FILE, default=[])
    now = datetime.now()
    cutoff = now - timedelta(hours=24)

    result = []
    for rec in sensor_log:
        ts = rec.get("timestamp")
        if not ts:
            continue
        try:
            dt = datetime.fromisoformat(ts)
        except Exception:
            continue
        if dt >= cutoff:
            result.append(rec)

    result.sort(key=lambda x: x.get("timestamp", ""))
    return jsonify(result)


# ========== 花盆信息设置 ==========
@app.route("/save_pot", methods=["POST"])
def save_pot():
    pot_diameter = request.form.get("pot_diameter")
    pot_height = request.form.get("pot_height")
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")

    pot_info = {
        "pot_diameter": pot_diameter,
        "pot_height": pot_height,
        "latitude": latitude,
        "longitude": longitude,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    save_json(POT_INFO_FILE, pot_info)

    return redirect(url_for("index"))


if __name__ == "__main__":
    print("[INFO] BASE_DIR =", BASE_DIR)
    print("[INFO] SENSOR_LOG_FILE =", SENSOR_LOG_FILE)
    print("[INFO] WATERING_LOG_FILE =", WATERING_LOG_FILE)
    print("[INFO] POT_INFO_FILE =", POT_INFO_FILE)
    print("[INFO] HEALTH_LOG_FILE =", HEALTH_LOG_FILE)
    app.run(host="0.0.0.0", port=5000, debug=True)
