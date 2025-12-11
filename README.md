# 🌱 AIoT Smart Watering System

**ESP32 + Soil Sensor + Flask Backend + Data Logging + AI Recommendation**

---

## 1. Project Overview

This project is an AIoT-based smart irrigation system that collects soil moisture using ESP32, uploads data to a server, and produces watering decisions automatically. Data is logged historically, and dashboards can be used to observe trends. Optionally, the system supports AI reasoning for irrigation suggestion.

---

## 2. Features

- 🌡 Real-time soil moisture sensing
- 📡 WiFi data upload with JSON
- 🗄 Backend logging + visualization
- 💧 Automatic watering logic
- 🤖 AI watering suggestion
- 🧩 Multi-plant scalable architecture

---

## 3. System Architecture

Soil Sensor → ESP32 → WiFi(JSON POST) → Flask Server → DB → Dashboard
└→ AI Watering 

---

## 4. Project Structure
```
.
├─app
│  │  .DS_Store
│  │  app.py
│  │  image.jpg
│  │  plant_health_log.json
│  │  pot_info.json
│  │  scheduler.py
│  │  sci_name.txt
│  │  sensor_log.json
│  │  watering_log.json
│  │
│  ├─images
│  │      .DS_Store
│  │      20251207_154348.jpg
│  │      20251207_154457.jpg
│  │      20251207_154601.jpg
│  │      20251207_154616.jpg
│  │      20251207_154630.jpg
│  │      20251207_154646.jpg
│  │      20251207_154702.jpg
│  │      20251207_154716.jpg
│  │      20251207_154731.jpg
│  │      20251207_154745.jpg
│  │      20251207_154759.jpg
│  │      20251207_154814.jpg
│  │      20251207_154829.jpg
│  │      20251207_154843.jpg
│  │      20251207_154857.jpg
│  │      20251207_155252.jpg
│  │      20251207_155307.jpg
│  │      20251207_155325.jpg
│  │      20251207_155338.jpg
│  │      20251207_155353.jpg
│  │      20251207_155408.jpg
│  │      20251207_155422.jpg
│  │      20251207_155435.jpg
│  │      20251207_155449.jpg
│  │      20251207_155505.jpg
│  │      20251207_155519.jpg
│  │      20251207_155533.jpg
│  │      20251207_155547.jpg
│  │      20251207_155601.jpg
│  │      20251207_155621.jpg
│  │      20251207_155635.jpg
│  │      20251207_155658.jpg
│  │      20251207_155713.jpg
│  │
│  ├─modules
│  │      ai_test.py
│  │      irrigation_plan.py
│  │      main.py
│  │      plant_recognition_module.py
│  │      weather_module.py
│  │      __init__.py
│  │
│  ├─static
│  │      styles.css
│  │
│  ├─templates
│  │      base.html
│  │      dashboard.html
│  │      index.html
│  │      setup.html
│  │
│  └─__pycache__
│          ai_module.cpython-312.pyc
│          irrigation_plan.cpython-312.pyc
│          main.cpython-312.pyc
│          plant_recognition_module.cpython-312.pyc
│          weather_module.cpython-312.pyc
│
└─hardware
    │  main.py
    │
    └─camera
            camera.ino
```
---

## 5. Hardware Required

| Component | Qty | Notes |
|---|---|---|
| ESP32 | 1 | WiFi MCU |
| Soil sensor | 1 | Analog input |
| Relay + Pump | optional | For autowater |
| Power supply | 5V | USB or adapter |

---

