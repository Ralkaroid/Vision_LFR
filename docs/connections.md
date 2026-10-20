# Hardware Connections

## 1. System Components

This project uses a Raspberry Pi Zero 2 W for camera-based line detection and an ESP32-WROOM-32 for motor control.

| Component | Purpose |
|---|---|
| Raspberry Pi Zero 2 W | Image processing and line detection |
| IMX219 camera | Captures the track |
| ESP32-WROOM-32 | Receives line error and controls motors |
| TB6612FNG | Dual DC motor driver |
| DC geared motors | Robot movement |
| Power supply | Powers the motors and electronics as required |

## 2. Raspberry Pi to ESP32 UART

UART communication transfers the horizontal line-position error from the Raspberry Pi to the ESP32.

| Raspberry Pi Zero 2 W | Physical Pin | ESP32-WROOM-32 |
|---|---:|---|
| GPIO14 / TXD | 8 | GPIO3 / RX0 |
| GPIO15 / RXD | 10 | GPIO1 / TX0 |
| GND | 6 | GND |

**UART configuration**
- Baud rate: 115200
- Data format: newline-terminated ASCII messages
- Logic level: 3.3 V

**Important:** Connect TX to RX and RX to TX. Connect the grounds together. Never connect 5 V to the UART signal pins.

ESP32 UART0 is shared with the USB programming and serial interface. Disconnect the Raspberry Pi UART wires if they interfere with uploading firmware.

## 3. ESP32 to TB6612FNG

| TB6612FNG Pin | ESP32 GPIO |
|---|---:|
| AIN1 | GPIO2 |
| AIN2 | GPIO4 |
| PWMA | GPIO15 |
| BIN1 | GPIO17 |
| BIN2 | GPIO5 |
| PWMB | GPIO18 |
| STBY | GPIO16 |

Motor A and Motor B are controlled independently using direction pins and PWM signals.

The TB6612FNG motor supply must match the motors' voltage requirements. Connect the motor driver's ground, ESP32 ground, and other grounds together. Supply the motors from a suitable motor power source rather than powering them from a Raspberry Pi GPIO pin.

Check the TB6612FNG breakout board's pin labels and power requirements before wiring.

## 4. Camera Connection

Connect the IMX219 camera to the Raspberry Pi Zero 2 W using the compatible camera ribbon cable and CSI connector. Ensure the cable is inserted in the correct orientation and the connector latch is secured.

Check camera detection with:

```bash
rpicam-hello --list-cameras
```

## 5. Communication Protocol

The Raspberry Pi sends messages in this format:

| Example | Meaning |
|---|---|
| `E:-20` | Line centroid is 20 pixels left of image center |
| `E:0` | Line is centered |
| `E:20` | Line centroid is 20 pixels right of image center |
| `E:999` | Line is lost or invalid |

Each message ends with a newline character (`\n`).

The error is calculated as:

`error = centroid_x - image_center_x`

The ESP32 uses the error to calculate motor corrections. The exact steering direction depends on motor wiring and controller sign conventions, so test with the wheels lifted first.

## 6. Safety Checks

- Verify polarity and supply voltage before powering the motors.
- Keep the robot wheels lifted during initial testing.
- Test UART communication before enabling motor movement.
- Ensure the controller stops the motors when the line is lost or communication times out.
- Avoid powering the motors directly from the Raspberry Pi.
