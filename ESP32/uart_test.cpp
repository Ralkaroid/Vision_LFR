
#include <Arduino.h>

String receivedMessage = "";

void setup() {
  Serial.begin(115200);  // UART0: TX0 GPIO1, RX0 GPIO3
  Serial.setTimeout(100);

  delay(1000);
  Serial.println("ESP32 UART0 test ready");
  Serial.println("Waiting for Raspberry Pi messages...");
}

void loop() {
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n') {
      receivedMessage.trim();

      if (receivedMessage.length() > 0) {
        // Print received message to USB Serial Monitor
        Serial.print("Received: ");
        Serial.println(receivedMessage);

        // Send acknowledgement back to Raspberry Pi
        Serial.print("ACK:");
        Serial.println(receivedMessage);
      }

      receivedMessage = "";
    } else if (c != '\r') {
      if (receivedMessage.length() < 64) {
        receivedMessage += c;
      } else {
        receivedMessage = "";
      }
    }
  }
}
