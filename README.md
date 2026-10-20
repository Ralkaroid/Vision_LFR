# Vision_LFR
This project detects a black line using an IMX219 camera connected to a Raspberry Pi Zero 2 W. OpenCV processes the camera frames to estimate the line's horizontal position. The Raspberry Pi sends the resulting error to an ESP32 over UART, and the ESP32 uses PID control to adjust the motors through a TB6612FNG motor driver.
