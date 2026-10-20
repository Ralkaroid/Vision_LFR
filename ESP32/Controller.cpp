// TB6612FNG motor pins
#define AIN1  2
#define AIN2  4
#define PWMA  15

#define BIN1  17
#define BIN2  5
#define PWMB  18

#define STBY  16

// Camera error arrives as E:<integer>\n over UART0
#define BAUD_RATE 115200

// Start conservatively; tune after testing
#define BASE_SPEED 55
#define MAX_SPEED 100

// Camera error is in pixels, roughly -160 to +160
// These are initial values, not final tuning values.
#define KP 0.35f
#define KI 0.0f
#define KD 0.15f

#define LINE_TIMEOUT_MS 300
#define MAX_VALID_ERROR 160

float lastError = 0;
float integral = 0;

unsigned long lastMessageTime = 0;
bool haveValidError = false;

String inputLine = "";

void stopMotors() {
  ledcWrite(PWMA, 0);
  ledcWrite(PWMB, 0);

  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, LOW);
  digitalWrite(BIN1, LOW);
  digitalWrite(BIN2, LOW);
}

void setMotor(int in1, int in2, int pwmPin, int speed) {
  speed = constrain(speed, -MAX_SPEED, MAX_SPEED);

  if (speed >= 0) {
    digitalWrite(in1, HIGH);
    digitalWrite(in2, LOW);
    ledcWrite(pwmPin, speed);
  } else {
    digitalWrite(in1, LOW);
    digitalWrite(in2, HIGH);
    ledcWrite(pwmPin, -speed);
  }
}

void resetController() {
  integral = 0;
  lastError = 0;
  haveValidError = false;
}

void processMessage(String msg) {
  msg.trim();

  if (!msg.startsWith("E:")) {
    return;
  }

  int error = msg.substring(2).toInt();

  // E:999 means the camera cannot see the line.
  if (error == 999 || abs(error) > MAX_VALID_ERROR) {
    stopMotors();
    resetController();
    lastMessageTime = millis();
    return;
  }

  lastMessageTime = millis();
  haveValidError = true;

  integral += error;
  integral = constrain(integral, -100.0f, 100.0f);

  float derivative = error - lastError;
  float correction = KP * error
                   + KI * integral
                   + KD * derivative;

  lastError = error;

  int leftSpeed  = (int)(BASE_SPEED - correction);
  int rightSpeed = (int)(BASE_SPEED + correction);

  leftSpeed = constrain(leftSpeed, -MAX_SPEED, MAX_SPEED);
  rightSpeed = constrain(rightSpeed, -MAX_SPEED, MAX_SPEED);

  setMotor(AIN1, AIN2, PWMA, leftSpeed);
  setMotor(BIN1, BIN2, PWMB, rightSpeed);
}

void setup() {
  // UART0: shared by ESP32 GPIO1/TX0 and GPIO3/RX0
  Serial.begin(BAUD_RATE);

  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);
  pinMode(BIN1, OUTPUT);
  pinMode(BIN2, OUTPUT);
  pinMode(STBY, OUTPUT);

  digitalWrite(STBY, HIGH);

  // ESP32 Arduino Core 3.x PWM API
  ledcAttach(PWMA, 1000, 8);
  ledcAttach(PWMB, 1000, 8);

  stopMotors();
  lastMessageTime = millis();
}

void loop() {
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n') {
      processMessage(inputLine);
      inputLine = "";
    } else if (c != '\r') {
      if (inputLine.length() < 32) {
        inputLine += c;
      } else {
        inputLine = "";
        stopMotors();
        resetController();
      }
    }
  }

  // Stop if camera messages stop arriving
  if (millis() - lastMessageTime > LINE_TIMEOUT_MS) {
    stopMotors();
    resetController();
  }
}
