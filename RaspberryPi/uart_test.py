import serial
import time

ser = serial.Serial(
    "/dev/serial0",
    115200,
    timeout=1
)

time.sleep(2)

try:
    while True:
        ser.write(b"ERROR:3\n")
        ser.flush()

        print("Sent: ERROR:3")

        response = ser.readline().decode(
            "utf-8", errors="replace"
        ).strip()

        if response:
            print("ESP32 replied:", response)

        time.sleep(0.5)

except KeyboardInterrupt:
    pass

finally:
    ser.close()
