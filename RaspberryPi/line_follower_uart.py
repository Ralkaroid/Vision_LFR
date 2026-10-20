import time
import cv2
import serial
import numpy as np
from picamera2 import Picamera2

# Camera settings
WIDTH, HEIGHT = 320, 240
BAUD_RATE = 115200
SERIAL_PORT = "/dev/serial0"

# Black-line detection settings
ROI_START = int(HEIGHT * 0.55)
THRESHOLD = 75
SEND_INTERVAL = 0.02  # target interval: 20 ms

# UART
uart = serial.Serial(
    SERIAL_PORT,
    BAUD_RATE,
    timeout=0.01
)
time.sleep(2)

# Camera
camera = Picamera2()
config = camera.create_video_configuration(
    main={"size": (WIDTH, HEIGHT), "format": "RGB888"}
)
camera.configure(config)
camera.start()
time.sleep(1)

print("Camera line detection and UART transmission started.")
print("Close the window or press q to exit.")

try:
    while True:
        frame = camera.capture_array()

        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

        # Use the lower part of the image
        roi = gray[ROI_START:HEIGHT, :]

        # Black line becomes white in the binary mask
        _, binary = cv2.threshold(
            roi, THRESHOLD, 255, cv2.THRESH_BINARY_INV
        )

        # Remove small noise
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.morphologyEx(
            binary, cv2.MORPH_OPEN, kernel
        )

        # Find black-line pixels
        ys, xs = np.where(binary > 0)

        if len(xs) > 30:
            cx = int(np.mean(xs))
            error = cx - (WIDTH // 2)

            # Send pixel error: negative = left, positive = right
            message = f"E:{error}\n"
            uart.write(message.encode("ascii"))
            print(f"Line detected | Error: {error}", flush=True)

            # Display detected line position
            display = frame.copy()
            cv2.line(
                display, (WIDTH // 2, ROI_START),
                (WIDTH // 2, HEIGHT - 1), (0, 0, 255), 1
            )
            cv2.circle(
                display, (cx, ROI_START + (HEIGHT - ROI_START) // 2),
                5, (0, 255, 0), -1
            )
            cv2.putText(
                display, f"Error: {error}",
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (0, 255, 0), 2
            )
        else:
            # Invalid-line signal; ESP32 must stop motors
            uart.write(b"E:999\n")
            display = frame.copy()
            cv2.putText(
                display, "LINE LOST",
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (0, 0, 255), 2
            )
            print("Line lost | Sending E:999", flush=True)


        time.sleep(SEND_INTERVAL)

finally:
    # Tell the ESP32 to stop if the program exits normally
    try:
        uart.write(b"E:999\n")
    except Exception:
        pass

    camera.stop()
    uart.close()
