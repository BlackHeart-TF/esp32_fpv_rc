# Low Latency Camera Streaming with UDP for ESP32-Camera

Targetting M5 Stack and Seeed devices with OV2640. Unit Cam, Unit Cam S3, Seed Xiao S3 sense. Requires PSRAM.

## COMING SOON:
servo control: supporting M5 8servos unit or direct gpio  
vr/ar viewer for racing rig

**CIF 60p**

[![](https://img.youtube.com/vi/SjpbKLbRCOo/0.jpg)](https://www.youtube.com/watch?v=SjpbKLbRCOo)

**SVGA 30p**

[![](https://img.youtube.com/vi/bDFTgpb2yXw/0.jpg)](https://www.youtube.com/watch?v=bDFTgpb2yXw)

**HD 15p**

[![](https://img.youtube.com/vi/p_f2DVExQYw/0.jpg)](https://www.youtube.com/watch?v=p_f2DVExQYw)

## esp32_sender

Tested with ESP-IDF 5.4.

All settings can be configured through menuconfig.  
Supports Logging to UDP, can receive with `nc -u -l 55557` if ESP_UDP_LOG is enabled

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
pip3 install -r ./python_receiver/requirements.txt
```

### Running the app
The easiest way to conenct is with the scanning and launching script 'main.py'. This file will broadcast for any running cameras and list the IP addresses. You can select 1-2 cameras and pass them to the QT or GL viewers.
```
python3 python_receiver/main.py
```

Yuu can also launch a viewer directly by specifying the addresses
```
python3.exe python_receiver/qtcontroller.py <esp32_ip>
```
For the VR/OpenGL viewer: (work in progress)
```
python3.exe python_receiver/vrcontroller.py <esp32_ip_1> <esp32_ip_2:optional>
```

## Project Status
### esp32_sender
#### Working
- Send camera stream with very low latency.
- Redirect logs to UDP
#### Issues
- Servo Control not fully implemented

### QT Viewer
#### Working
- receives low latency camera
#### Issues
- does not send control info

### GL Viewer
#### Working
- receives low latency camera
- receives second camera
#### Issues
- second camera not drawing fast enough
- coded like a wild monkey did it
- does not send control info
