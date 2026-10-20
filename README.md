# Vision-Based Line Follower Robot

A camera-based line-following robot using a Raspberry Pi Zero 2 W for computer vision and an ESP32 for real-time motor control.

## Overview

This project detects a black line using an IMX219 camera connected to a Raspberry Pi Zero 2 W. OpenCV processes the camera frames to estimate the line's horizontal position. The Raspberry Pi sends the resulting error to an ESP32 over UART, and the ESP32 uses PID control to adjust the motors through a TB6612FNG motor driver.

## System Architecture

```text
IMX219 Camera
      |
      v
Raspberry Pi Zero 2 W
      |
      v
OpenCV Line Detection
      |
      v
Line Centroid and Error
      |
      v
UART Communication (115200 baud)
      |
      v
ESP32-WROOM-32
      |
      v
PID Motor Control
      |
      v
TB6612FNG Motor Driver
      |
      v
Left and Right Motors
```

## Hardware Requirements

- Raspberry Pi Zero 2 W
- IMX219 camera module
- ESP32-WROOM-32 development board
- TB6612FNG dual motor driver
- Two DC geared motors and robot chassis
- Suitable motor power supply
- Jumper wires

## Software Requirements

- Raspberry Pi OS
- Python 3
- Picamera2
- OpenCV
- NumPy
- PySerial
- Arduino IDE with ESP32 board support

## Computer Vision Pipeline

1. Capture a camera frame at 320 × 240 resolution.
2. Convert the frame to grayscale.
3. Select the lower region of interest (ROI).
4. Apply inverse binary thresholding to isolate the black line.
5. Apply morphological opening to reduce small noise.
6. Calculate the centroid of the detected line pixels.
7. Calculate the horizontal error relative to the image center.
8. Transmit the error to the ESP32 over UART.

The horizontal error is:

`error = line_centroid_x - image_center_x`

A negative error indicates that the detected line is left of the image center; a positive error indicates that it is right of the center.

## UART Protocol

The Raspberry Pi transmits newline-terminated messages at 115200 baud.

| Message | Meaning |
|---|---|
| `E:-20` | Line is 20 pixels left of center |
| `E:0` | Line is centered |
| `E:20` | Line is 20 pixels right of center |
| `E:999` | Line is lost or invalid |

The ESP32 parses these messages and adjusts the left and right motor speeds. If valid messages stop arriving, the controller stops the motors as a safety measure.

## Hardware Connections

### Raspberry Pi to ESP32 UART

| Raspberry Pi Zero 2 W | ESP32-WROOM-32 |
|---|---|
| GPIO14 / TXD, physical pin 8 | GPIO3 / RX0 |
| GPIO15 / RXD, physical pin 10 | GPIO1 / TX0 |
| GND, physical pin 6 | GND |

Both UART devices use 3.3 V logic. Do not connect 5 V to the UART pins.

### ESP32 to TB6612FNG

| TB6612FNG signal | ESP32 GPIO |
|---|---:|
| AIN1 | 2 |
| AIN2 | 4 |
| PWMA | 15 |
| BIN1 | 17 |
| BIN2 | 5 |
| PWMB | 18 |
| STBY | 16 |

Verify motor polarity and power connections before operating the robot.

## Installation

Install the Raspberry Pi dependencies:

```bash
sudo apt update
sudo apt install python3-picamera2 python3-opencv python3-serial python3-numpy
```

Clone this repository:

```bash
git clone https://github.com/YOUR_USERNAME/Vision-Based-Line-Follower.git
cd Vision-Based-Line-Follower
```

Run the Raspberry Pi program:

```bash
python3 raspberry_pi/line_follower_uart.py
```

Upload `esp32/camera_line_follower.ino` to the ESP32 using the Arduino IDE. Disconnect the Pi's UART wires during flashing if necessary because UART0 is shared with the USB programming interface.

## Safety and Troubleshooting

- Run only one camera application at a time.
- If Picamera2 reports that the camera is busy, stop other camera processes.
- If OpenCV reports a display error over SSH, disable `cv2.imshow()` and `cv2.waitKey()` or use a graphical display.
- Check UART TX/RX crossover, common ground, and baud rate if communication fails.
- Test with the wheels lifted before placing the robot on the floor.
- Tune PID gains at low speed and verify steering direction.


## Future Improvements

- Adaptive thresholding for changing lighting conditions
- More robust line-loss recovery
- PID tuning and speed optimization
- Live telemetry and performance logging
- Camera-based curves and intersections handling

## License

This project is released under the MIT License. See `LICENSE` for details.
