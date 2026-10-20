# Troubleshooting Guide

## 1. Camera Is Busy

**Error:**

```text
RuntimeError: Failed to acquire camera: Device or resource busy
```

**Cause:** Another application may already be using the camera, such as `cv_web.py`, `line_follower_uart.py`, or `rpicam-hello`.

**Solution:**

```bash
ps aux | grep -E 'cv_web.py|line_follower_uart.py|rpicam|libcamera' | grep -v grep
```

Stop the specific camera application before starting another. If a confirmed, unresponsive process remains, terminate that process. Only one application should own the camera at a time.

## 2. OpenCV Cannot Open a Display

**Error:**

```text
qt.qpa.xcb: could not connect to display
```

**Cause:** The application is trying to open an OpenCV window during an SSH session without a graphical display.

**Solution:** Remove or disable:

```python
cv2.imshow(...)
cv2.waitKey(...)
cv2.destroyAllWindows()
```

Print the detected error to the terminal instead, or use a separately configured graphical display. Do not run a second camera application just to view the feed.

## 3. Raspberry Pi SSH Hostname Cannot Be Resolved

**Error:**

```text
ssh: Could not resolve hostname raspi0.local
```

**Cause:** Windows cannot resolve the Pi's `.local` hostname, often due to an mDNS or network issue.

**Solution:**

1. Confirm the Pi is powered on and connected to Wi-Fi.
2. Ensure the computer and Pi are on the same network.
3. Find the Pi's IP address in the router or hotspot's connected-device list.
4. Connect using the IP address:

```powershell
ssh pi0@192.168.1.25
```

Replace the example IP with the Pi's actual address.

## 4. UART Communication Does Not Work

**Possible causes:**
- TX and RX are connected incorrectly.
- Grounds are not connected together.
- The baud rates do not match.
- The Pi is using the wrong serial device.
- Another program is using the UART.
- ESP32 UART0 is being shared with USB serial output.

**Checks:**

On the Raspberry Pi:

```bash
ls -l /dev/serial0
```

Confirm the Pi script opens `/dev/serial0` at 115200 baud.

Verify the wiring:

- Pi GPIO14 TXD → ESP32 GPIO3 RX0
- Pi GPIO15 RXD ← ESP32 GPIO1 TX0
- Pi GND → ESP32 GND

Use a simple UART receiver test before enabling the motors. Avoid printing debug messages over UART0 because those messages can corrupt the protocol.

## 5. Line Is Not Detected

**Possible causes:**
- Poor lighting or glare.
- Incorrect threshold.
- ROI excludes the line.
- Camera is too high, too low, or angled incorrectly.
- The threshold mask contains noise or too few pixels.

**Checks:**

1. Inspect the threshold mask.
2. Adjust the threshold value for the track and lighting.
3. Verify the ROI includes the part of the image where the line appears.
4. Check the number of detected pixels before accepting a centroid.
5. Test on a clear black line against a contrasting surface.

## 6. Robot Turns in the Wrong Direction

**Cause:** The motor polarity, left/right assignment, or controller correction sign may be reversed.

**Solution:**

1. Lift the wheels off the ground.
2. Move the line to the left of the camera center and observe the error sign.
3. Check the motor response.
4. Reverse the steering correction sign or correct motor polarity as needed.
5. Retest at low speed.

## 7. Motors Do Not Run

**Checks:**
- Confirm the motor supply is connected.
- Confirm the ESP32 and TB6612FNG share ground.
- Verify STBY is HIGH when motor operation is enabled.
- Check PWM and direction pin assignments.
- Confirm the controller has received a valid line-error message.
- Check whether the safety timeout or line-loss condition is stopping the motors.

## 8. General Debugging Procedure

Test one subsystem at a time:

1. Confirm camera detection with `rpicam-hello --list-cameras`.
2. Confirm OpenCV line detection on the Raspberry Pi.
3. Confirm UART messages are transmitted and received.
4. Test motor direction without the camera controller.
5. Enable closed-loop control at low speed.
6. Tune PID gains and test on a clear track.

Always keep the wheels lifted during initial motor and steering tests.
