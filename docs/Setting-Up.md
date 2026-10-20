# Raspberry Pi Zero 2 W Setup Guide

## Camera-Based Line Follower Robot

This guide is for a beginner setting up a Raspberry Pi Zero 2 W from
scratch for the vision-based line follower project. It covers the
operating system, Wi-Fi/SSH access, IMX219 camera, Python dependencies,
and UART connection to an ESP32.

> **Important:** The Raspberry Pi runs the camera and computer-vision
> code. The ESP32 receives the line-position error over UART and
> controls the motors. Test the motors with the wheels lifted before
> running the robot on the floor.

## 1. What you need

-   Raspberry Pi Zero 2 W
-   microSD card (8 GB minimum; 16 GB or larger recommended)
-   Compatible power supply and USB power cable
-   IMX219 camera module and compatible ribbon cable for the Pi Zero
    camera connector
-   A Windows computer for preparing the microSD card
-   Wi-Fi network or phone hotspot
-   ESP32-WROOM-32, TB6612FNG, motors, and suitable motor power supply
    for the complete robot
-   Optional: mini-HDMI adapter, monitor, USB OTG adapter, keyboard for
    local troubleshooting

## 2. Install Raspberry Pi OS

1.  Download and install **Raspberry Pi Imager** on your computer from
    the official Raspberry Pi website:
    https://www.raspberrypi.com/software/
2.  Insert the microSD card into your computer. **Imaging erases the
    card**, so back up anything important first.
3.  Open Raspberry Pi Imager.
4.  Select **Raspberry Pi Zero 2 W** as the device if prompted.
5.  Choose **Raspberry Pi OS Lite (32-bit)** for a lightweight headless
    robot setup. If you prefer a desktop, choose the standard Raspberry
    Pi OS, but it uses more memory.
6.  Select the microSD card as the storage device. Check the selected
    device carefully.
7.  In the OS customisation settings, configure:
    -   **Hostname:** `raspi0`
    -   **Username:** `pi0` (or another username you will remember)
    -   **Password:** create a strong password and store it safely
    -   **Wireless LAN:** enter the correct Wi-Fi country, network name
        (SSID), and password
    -   **Locale/time zone:** select your location and keyboard layout
    -   **Remote access:** enable SSH and select password
        authentication, unless you already use SSH keys
8.  Save the settings and write the OS to the card.
9.  Safely eject the card from the computer.

The exact Imager screens may differ slightly by version. If a
customisation option is not shown, complete the first boot and configure
it afterward.

## 3. First boot and SSH connection

1.  With the Pi powered off, insert the microSD card.

2.  Connect the camera only while the Pi is powered off. Open the camera
    connector carefully, insert the ribbon in the orientation specified
    for your board/cable, and close the latch. Do not force the
    connector.

3.  Power on the Pi and wait a few minutes for its first boot.

4.  Connect your Windows computer to the **same Wi-Fi network or phone
    hotspot** configured on the Pi.

5.  Open PowerShell and try:

    ``` powershell
    ssh pi0@raspi0.local
    ```

6.  Accept the host key only if you are confident this is your Pi, then
    enter the password you set in Imager.

### If `raspi0.local` cannot be resolved

Windows may not resolve `.local` hostnames on every network.

-   Check the connected-device list in your router or phone hotspot for
    `raspi0`.

-   Alternatively, use a monitor and keyboard and run `hostname -I` on
    the Pi.

-   Connect using the actual IP address:

    ``` powershell
    ssh pi0@192.168.1.25
    ```

    Replace `192.168.1.25` with the IP address shown for your Pi.

If SSH says `Connection refused`, SSH may not be enabled or the Pi may
not have finished booting. If it says `Permission denied`, verify the
username and password you configured.

## 4. Update the operating system

After connecting over SSH, run:

``` bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

Wait for the Pi to restart, then reconnect using SSH. An update can take
some time and may require a reboot.

## 5. Connect and test the camera

Check whether the IMX219 is detected:

``` bash
rpicam-hello --list-cameras
```

The output should list a camera such as `imx219`. Then test a short
preview:

``` bash
rpicam-hello -t 5000
```

On a Lite/headless installation, a preview window may not be available.
That alone does not prove the camera is broken. The camera list should
still show the camera. You can test capture using Picamera2 in the next
section.

**Camera ownership rule:** only one application can normally use the
camera at a time. Stop `cv_web.py`, `line_follower_uart.py`, and other
camera applications before testing another one.

If you see `Device or resource busy`, inspect running processes:

``` bash
ps aux | grep -E 'cv_web.py|line_follower_uart.py|rpicam|libcamera' | grep -v grep
```

Stop the specific application from its terminal with `Ctrl+C`. If it is
stuck, use its process ID with `kill PID`; use `sudo kill -9 PID` only
as a last resort for that confirmed process.

## 6. Install the Python packages

Use the operating system packages for Picamera2 on Raspberry Pi OS. This
is usually the simplest approach for beginners and avoids isolating
Picamera2 from its system camera libraries.

``` bash
sudo apt install -y python3-picamera2 python3-opencv python3-numpy python3-serial
```

Check the imports:

``` bash
python3 -c "from picamera2 import Picamera2; import cv2, numpy, serial; print('Camera and Python packages imported successfully')"
```

If the package is unavailable, confirm that you are running Raspberry Pi
OS and that `sudo apt update` completed successfully. Do not install
random camera packages from unofficial sources.

## 7. Create the project folders

``` bash
mkdir -p ~/line_follower_cv
cd ~/line_follower_cv
```

Create or copy the project's Raspberry Pi script into this directory.
For example:

``` bash
micro line_follower_uart.py
```

If `micro` is not installed, use `nano` instead:

``` bash
nano line_follower_uart.py
```

Paste the tested Python code, save the file, and exit the editor. In
`nano`, save with `Ctrl+O`, press Enter, and exit with `Ctrl+X`. In
`micro`, use its on-screen shortcuts/help if unfamiliar.

## 8. Configure UART for the ESP32

The Raspberry Pi UART uses GPIO14 (TXD) and GPIO15 (RXD). Configure the
serial interface:

``` bash
sudo raspi-config
```

Open **Interface Options → Serial Port** (the wording may vary by OS
version):

-   Answer **No** when asked whether to enable a login shell over
    serial.
-   Answer **Yes** when asked whether to enable the serial hardware.
-   Finish and reboot if prompted.

If the menu differs on your OS version, consult the official Raspberry
Pi documentation for enabling the serial port.

### UART wiring

Power both boards off before connecting wires.

  Raspberry Pi Zero 2 W     Physical pin ESP32-WROOM-32
  ----------------------- -------------- ----------------
  GPIO14 / TXD                         8 GPIO3 / RX0
  GPIO15 / RXD                        10 GPIO1 / TX0
  GND                                  6 GND

-   TX must connect to the other board's RX.
-   RX must connect to the other board's TX.
-   The grounds must be connected.
-   Both UARTs use 3.3 V logic. **Never connect 5 V to a UART signal
    pin.**
-   Do not connect the Raspberry Pi's 5 V pin to an ESP32 GPIO.
-   ESP32 UART0 is shared with USB serial programming/debugging.
    Disconnect the Pi TX/RX wires while uploading firmware if uploading
    fails. Avoid USB Serial Monitor output while the Pi is using UART0.

Check the serial device:

``` bash
ls -l /dev/serial0
```

The Pi script should open `/dev/serial0` at the same baud rate
configured in the ESP32 code (115200 in this project).

## 9. Run the camera line-detection program

Make sure no other camera program is running. Then:

``` bash
cd ~/line_follower_cv
python3 line_follower_uart.py
```

The program should report that camera line detection and UART
transmission have started. If the script uses `cv2.imshow()` over SSH
without a graphical display, it may fail with a Qt/XCB display error.
For headless use, disable the `cv2.imshow()`, `cv2.waitKey()`, and
`cv2.destroyAllWindows()` calls and print the detected error to the
terminal instead.

Expected UART message format:

-   `E:-20` --- line is left of the image center
-   `E:0` --- line is centered
-   `E:20` --- line is right of the image center
-   `E:999` --- line is lost or invalid

These are examples; the exact values depend on the line position. The
ESP32 must interpret `E:999` as invalid and stop the motors.

To stop the Python program, press `Ctrl+C`. The script should close the
camera and serial port in its cleanup handler.

## 10. First robot test checklist

Do not place the robot on the floor until the following checks are
complete.

1.  **Camera:** IMX219 appears in `rpicam-hello --list-cameras`.
2.  **Vision:** the program detects the black line and reports changing
    error values as the line moves left and right.
3.  **UART:** the ESP32 receives valid newline-terminated `E:<error>`
    messages at 115200 baud.
4.  **Line loss:** the ESP32 stops the motors on `E:999` and if messages
    time out.
5.  **Motor direction:** test with wheels lifted and at low speed;
    verify the robot corrects toward the line.
6.  **Power:** motor supply, logic supply, and common ground are wired
    correctly. Do not power motors from a Pi GPIO.
7.  **Autonomous run:** start with a slow speed on a clear, short track
    and keep a hand near the power switch.

## 11. Troubleshooting

### SSH hostname does not work

Use the Pi's actual IP address instead of `raspi0.local`. Make sure both
devices are on the same network.

### Camera is busy

Stop the other camera application. Do not run the web dashboard and UART
camera script simultaneously if both create their own `Picamera2`
instance.

### Camera is not detected

Power off before reseating the ribbon cable. Check the connector
orientation and latch, then run `rpicam-hello --list-cameras` again.

### `No module named picamera2`

Install the OS package:

``` bash
sudo apt install python3-picamera2
```

Run the script with the system `python3`, especially if using
system-installed Picamera2 packages.

### UART does not work

Verify TX/RX crossover, common ground, `/dev/serial0`, matching baud
rates, and that serial login is disabled. Do not send debugging text
over ESP32 UART0 while it carries the line-error protocol.

### OpenCV says it cannot connect to a display

The script is running without a desktop display. Disable OpenCV GUI
calls or run a version designed for headless operation.

### Wi-Fi disconnects or SSH drops

Check the power supply and Wi-Fi signal. Reconnect using the current IP
address if `.local` resolution fails. A low-quality or insufficient
power supply can cause instability.

## 12. Useful commands

``` bash
# Show IP address
hostname -I

# Show OS version
cat /etc/os-release

# Check camera detection
rpicam-hello --list-cameras

# Check serial device
ls -l /dev/serial0

# Find project processes
ps aux | grep -E 'cv_web.py|line_follower_uart.py' | grep -v grep

# Stop the current program
# Press Ctrl+C in its terminal
```

## 13. Official resources

-   Raspberry Pi Imager: https://www.raspberrypi.com/software/
-   Raspberry Pi camera software:
    https://www.raspberrypi.com/documentation/computers/camera_software.html
-   Raspberry Pi serial interfaces:
    https://www.raspberrypi.com/documentation/computers/configuration.html
-   Picamera2 documentation and examples:
    https://github.com/raspberrypi/picamera2

## Setup completion

When setup is complete, record the OS version, camera model, Python
version, UART baud rate, and the date of your successful test in the
project README. This makes the project easier for other people to
reproduce.
