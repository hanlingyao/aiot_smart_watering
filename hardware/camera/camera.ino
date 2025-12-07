#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>

// ================== 1. WiFi settings ==================
const char* ssid     = "Columbia University";    // your 2.4 GHz WiFi SSID
const char* password = "";     // your WiFi password

// Change this to development backend URL
String serverUrl = "http://10.206.162.113:5000/esp32_upload";


#define CAMERA_MODEL_AI_THINKER
// --- AI Thinker ESP32-CAM (pin mapping) ---
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22




// ================== 2. WiFi helpers ==================
void connectToWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);          // disable power save for better stability

  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  uint8_t retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 40) { // ~20 seconds
    delay(500);
    Serial.print(".");
    retries++;
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("WiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("WiFi connect FAILED");
  }
}

void ensureWiFi() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi lost, reconnecting...");
    WiFi.disconnect(true, true);
    delay(1000);
    connectToWiFi();
  }
}



// ================== 3. Camera init ==================
bool initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;

  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;

  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  // choose a reasonable frame size
  config.frame_size   = FRAMESIZE_HD;  // 640x480
  config.jpeg_quality = 5;             // lower = better quality, bigger size
  config.fb_count     = 1;


// | FRAMESIZE_QQVGA    | 160×120         |
// | FRAMESIZE_QVGA     | 320×240         |
// | FRAMESIZE_VGA      | 640×480         |
// | **FRAMESIZE_SVGA** | **800×600（建议）** |
// | FRAMESIZE_XGA      | 1024×768        |
// | FRAMESIZE_SXGA     | 1280×1024       |
// | FRAMESIZE_UXGA     | 1600×1200       |
// | FRAMESIZE_HD       | 1280×720        |
// | FRAMESIZE_FHD      | 1920×1080       |


  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    return false;
  }

  Serial.println("Camera init success!");
  return true;
}



// ================== 4. Capture and upload one frame ==================
void captureAndUpload() {
  // Make sure WiFi is ready
  ensureWiFi();
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("No WiFi, skip this frame");
    return;
  }

  // Capture JPEG frame
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    return;
  }

  Serial.print("Captured image, size = ");
  Serial.print(fb->len);
  Serial.println(" bytes");

  HTTPClient http;

  // Start HTTP connection
  if (!http.begin(serverUrl)) {
    Serial.println("HTTP begin() failed");
    esp_camera_fb_return(fb);
    return;
  }

  http.addHeader("Content-Type", "image/jpeg");
  http.setTimeout(15000);     // 15s timeout for sending + waiting response
  http.setReuse(false);       // do not reuse connection, safer for long runs


  // POST raw JPEG bytes
  int httpCode = http.POST(fb->buf, fb->len);

  if (httpCode > 0) {
    Serial.printf("HTTP POST code: %d\n", httpCode);
    String payload = http.getString();
    Serial.println("Response:");
    Serial.println(payload);
  } else {
    Serial.printf("HTTP POST failed: %s\n",
                  http.errorToString(httpCode).c_str());
  }

  http.end();
  esp_camera_fb_return(fb);
}



// ================== 5. Arduino setup / loop ==================
void setup() {
  Serial.begin(115200);
  delay(2000);
  Serial.println();
  Serial.println("Booting ESP32-CAM uploader...");

  connectToWiFi();

  if (!initCamera()) {
    Serial.println("Camera init failed, restarting in 5 seconds...");
    delay(5000);
    ESP.restart();
  }
}

void loop() {
  Serial.println();
  Serial.println("Taking picture and uploading...");
  captureAndUpload();
  delay(10000);   // capture every 10 seconds
}
