# main.py - Feather ESP32 V2
# Sensors: BH1750, Capacitive Soil Moisture (ADC), DS18B20, DHT22
# Upload data to Flask HTTP server as JSON.

import time
import json
from machine import Pin, I2C, ADC
import network
import dht
import onewire
import ds18x20

try:
    import urequests as requests
except ImportError:
    import requests  # fallback


# ---------- WiFi + Server Config ----------
WIFI_SSID = "Columbia University"
WIFI_PASSWORD = ""

SERVER_JSON_URL = "http://10.206.182.201:5000/upload"   # Flask /upload endpoint


# ---------- Pin Definitions (Feather V2) ----------
I2C_SDA_PIN = 22      # BH1750 SDA
I2C_SCL_PIN = 20      # BH1750 SCL

SOIL_MOISTURE_PIN = 34   # Capacitive soil moisture -> ADC

DS18B20_PIN = 13         # DS18B20 DATA (module with pull-up)
DHT22_PIN = 33           # DHT22 DATA


# ---------- BH1750 Driver ----------
class BH1750:
    PWR_OFF = 0x00
    PWR_ON = 0x01
    RESET = 0x07
    CONT_H_RES_MODE = 0x10

    def __init__(self, i2c, addr=0x23):
        self.i2c = i2c
        self.addr = addr
        self.i2c.writeto(self.addr, bytes([self.PWR_ON]))
        self.i2c.writeto(self.addr, bytes([self.RESET]))

    def luminance(self):
        self.i2c.writeto(self.addr, bytes([self.CONT_H_RES_MODE]))
        time.sleep_ms(180)
        data = self.i2c.readfrom(self.addr, 2)
        raw = (data[0] << 8) | data[1]
        return raw / 1.2  # lux


# ---------- WiFi Helpers ----------
def connect_wifi(ssid, password, timeout=15):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(ssid, password)
        t0 = time.time()
        while not wlan.isconnected():
            if time.time() - t0 > timeout:
                print("WiFi connection timeout")
                return False
            time.sleep(1)
    print("WiFi connected:", wlan.ifconfig())
    return True


def http_post_json(url, data):
    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.post(url, data=json.dumps(data), headers=headers)
        print("HTTP JSON status:", resp.status_code)
        resp.close()
        return True
    except Exception as e:
        print("HTTP JSON POST failed:", e)
        return False


# ---------- Sensor Init ----------
i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=100_000)
light_sensor = BH1750(i2c)

soil_adc = ADC(Pin(SOIL_MOISTURE_PIN))
soil_adc.atten(ADC.ATTN_11DB)
soil_adc.width(ADC.WIDTH_12BIT)

ow = onewire.OneWire(Pin(DS18B20_PIN))
ds = ds18x20.DS18X20(ow)
roms = ds.scan()
print("DS18B20 devices:", roms)

dht22 = dht.DHT22(Pin(DHT22_PIN))


# ---------- Sensor Read Helpers ----------
def read_light():
    try:
        return light_sensor.luminance()
    except Exception as e:
        print("BH1750 error:", e)
        return None


def read_soil_moisture():
    raw = soil_adc.read()
    percent = (raw / 4095) * 100
    percent = max(0, min(100, percent))
    return raw, percent


def read_soil_temperature():
    if not roms:
        return None
    try:
        ds.convert_temp()
        time.sleep_ms(750)
        temp_c = ds.read_temp(roms[0])
        return temp_c
    except Exception as e:
        print("DS18B20 error:", e)
        return None


def read_air_temp_hum():
    try:
        dht22.measure()
        t = dht22.temperature()
        h = dht22.humidity()
        return t, h
    except Exception as e:
        print("DHT22 error:", e)
        return None, None


# ---------- Main Loop ----------
def main():
    wifi_ok = connect_wifi(WIFI_SSID, WIFI_PASSWORD)
    if not wifi_ok:
        print("No WiFi, JSON upload will fail.")

    while True:
        print("====== Sensor Readings ======")

        lux = read_light()
        soil_raw, soil_percent = read_soil_moisture()
        soil_temp = read_soil_temperature()
        air_temp, air_hum = read_air_temp_hum()

        if lux is not None:
            print("Light: {:.2f} lux".format(lux))
        else:
            print("Light: ERROR")

        print("Soil moisture: raw = {}  approx = {:.1f}%".format(
            soil_raw, soil_percent
        ))

        if soil_temp is not None and -50 < soil_temp < 125:
            print("Soil temperature (DS18B20): {:.2f} °C".format(soil_temp))
        else:
            print("Soil temperature (DS18B20): ERROR")

        if air_temp is not None:
            print("Air temperature (DHT22): {:.2f} °C".format(air_temp))
            print("Air humidity (DHT22): {:.2f}% RH".format(air_hum))
        else:
            print("Air temperature/humidity (DHT22): ERROR")

        payload = {
            "light_lux": lux,
            "soil_moisture_percent": soil_percent,
            "soil_temperature_c": soil_temp,
            "air_temperature_c": air_temp,
            "air_humidity_percent": air_hum,
            "device": "feather-esp32-v2",
        }

        print("Uploading JSON...")
        http_post_json(SERVER_JSON_URL, payload)
        print()
        time.sleep(5)


if __name__ == "__main__":
    main()
