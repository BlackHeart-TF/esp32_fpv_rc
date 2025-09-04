# ESP32 FPV RC - Android Receiver

Android app that receives video streams from ESP32 cameras and provides remote control functionality.

## Features

- **Device Discovery**: Automatically discover ESP32 cameras on the local network
- **Live Video**: Receive and display MJPEG video streams via UDP
- **Remote Control**: Virtual joystick for controlling servos
- **Future Ready**: Structured for multi-camera and VR support

## Architecture

### Core Components

- **UdpReceiver**: Handles all UDP communication (discovery, streaming, servo commands)
- **MainScreen**: Device discovery and selection interface  
- **ViewerScreen**: Video display with virtual joystick controls
- **Navigation**: Compose Navigation between screens

### Network Protocol

Matches the Python receiver protocol:

- **Discovery**: Broadcast `0x55` to `255.255.255.255:55555`, listen for responses on `55556`
- **Start Stream**: Send `0x55` then `0x57` to target IP:55555
- **Stop Stream**: Send `0x56` to target IP:55555  
- **Servo Control**: Send `0x54` + little-endian shorts (X, Y) every 20ms

### Frame Assembly

JPEG frames are reassembled from UDP packets using SOI/EOI markers:
- Start of Image: `0xFF 0xD8 0xFF`
- End of Image: `0xFF 0xD9`

## Setup

1. Open in Android Studio
2. Build and install on device
3. Ensure device and ESP32 are on same WiFi network
4. Tap "Scan for Cameras" to discover devices
5. Tap a discovered camera to connect and view

## Future Extensions

The architecture supports:
- **Multi-camera**: Additional camera slots in UI state
- **VR Mode**: Cardboard/split-screen rendering in ViewerScreen
- **Additional Controls**: More complex control schemes
- **Recording**: Local video recording capabilities

## Requirements

- Android 7.0+ (API 24)
- WiFi connection to same network as ESP32 devices
- Network permissions (automatically requested)
