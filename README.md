# Low Latency Camera Streaming with UDP for ESP32-Camera

Targetting M5 Stack and Seeed devices with OV2640. Unit Cam, Unit Cam S3, Seed Xiao S3 sense. Requires PSRAM.

## COMING SOON:
servo control: supporting M5 8servos unit or direct gpio

**CIF 60p**

[![](https://img.youtube.com/vi/SjpbKLbRCOo/0.jpg)](https://www.youtube.com/watch?v=SjpbKLbRCOo)

**SVGA 30p**

[![](https://img.youtube.com/vi/bDFTgpb2yXw/0.jpg)](https://www.youtube.com/watch?v=bDFTgpb2yXw)

**HD 15p**

[![](https://img.youtube.com/vi/p_f2DVExQYw/0.jpg)](https://www.youtube.com/watch?v=p_f2DVExQYw)

## esp32_sender

build with ESP-IDF 5.0

### WiFi
The SSID and Network key must be set before compiling. You can set it with IDF or from the config directly

```
cd esp32_sender
idf.py menuconfig
```
in sdkconfig:
```
CONFIG_ESP_WIFI_SSID="MyNetwork"
CONFIG_ESP_WIFI_PASSWORD="MyKey"
```

### Building for ESP32

Requires ESP-IDF and esp32_camera fragment mode: https://github.com/arms22/esp32-camera-fragment-mode

```
cd esp32_sender
idf.py -p PORT build flash monitor
```

## python_receiver

### Installing requirements

```
pip3 install --upgrade pip
pip3 install opencv-python
```

### Running the app
Listen_ip is the address you want to receive the video on. You can specify 0.0.0.0 if you dont know/care.
esp32_ip is the device, it will print it to console at boot
```
python3.exe python_receiver\receiver.py <listen_ip> <esp32_ip>
```
