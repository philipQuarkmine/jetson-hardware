#include <Servo.h>

// Motor ESC objects
Servo leftMotor;
Servo rightMotor;

// Pin definitions
const int LEFT_MOTOR_PIN = 5;
const int RIGHT_MOTOR_PIN = 6;
const int LEFT_DIR_PIN = 7;    // Optional
const int RIGHT_DIR_PIN = 8;   // Optional
const int STATUS_LED_PIN = 13;

// Motor state
int leftSpeed = 0;
int rightSpeed = 0;
bool emergencyStop = false;
unsigned long lastCommandTime = 0;
const unsigned long WATCHDOG_TIMEOUT = 1000; // 1 second

void setup() {
  Serial.begin(115200);
  
  // Initialize motors
  leftMotor.attach(LEFT_MOTOR_PIN);
  rightMotor.attach(RIGHT_MOTOR_PIN);
  
  // Initialize pins
  pinMode(LEFT_DIR_PIN, OUTPUT);
  pinMode(RIGHT_DIR_PIN, OUTPUT);
  pinMode(STATUS_LED_PIN, OUTPUT);
  
  // Set initial state
  setMotorSpeed(0, 0);  // Left motor stop
  setMotorSpeed(1, 0);  // Right motor stop
  
  digitalWrite(STATUS_LED_PIN, HIGH);
  delay(500);
  digitalWrite(STATUS_LED_PIN, LOW);
  
  Serial.println("Arduino Motor Controller Ready");
  lastCommandTime = millis();
}

void loop() {
  // Handle serial commands
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    handleCommand(command);
    lastCommandTime = millis();
  }
  
  // Watchdog timer - stop motors if no commands received
  if (millis() - lastCommandTime > WATCHDOG_TIMEOUT) {
    if (!emergencyStop) {
      emergencyStop = true;
      setMotorSpeed(0, 0);
      setMotorSpeed(1, 0);
      Serial.println("WATCHDOG_TIMEOUT");
    }
  }
  
  // Status LED blink
  static unsigned long lastBlink = 0;
  if (millis() - lastBlink > 1000) {
    digitalWrite(STATUS_LED_PIN, !digitalRead(STATUS_LED_PIN));
    lastBlink = millis();
  }
}

void handleCommand(String cmd) {
  cmd.trim();
  
  if (cmd == "PING") {
    Serial.println("PONG");
    
  } else if (cmd == "ESTOP") {
    emergencyStop = true;
    setMotorSpeed(0, 0);
    setMotorSpeed(1, 0);
    Serial.println("OK");
    
  } else if (cmd.startsWith("MOTOR:")) {
    if (emergencyStop) {
      Serial.println("ERROR");
      return;
    }
    
    int firstColon = cmd.indexOf(':');
    int secondColon = cmd.indexOf(':', firstColon + 1);
    
    if (firstColon != -1 && secondColon != -1) {
      int motorId = cmd.substring(firstColon + 1, secondColon).toInt();
      int speed = cmd.substring(secondColon + 1).toInt();
      
      if (motorId >= 0 && motorId <= 1 && speed >= -100 && speed <= 100) {
        setMotorSpeed(motorId, speed);
        Serial.println("OK");
      } else {
        Serial.println("ERROR");
      }
    } else {
      Serial.println("ERROR");
    }
    
  } else if (cmd == "STATUS") {
    Serial.print("MOTORS:");
    Serial.print(leftSpeed);
    Serial.print(",");
    Serial.print(rightSpeed);
    Serial.print(" ESTOP:");
    Serial.println(emergencyStop ? "1" : "0");
    
  } else {
    Serial.println("ERROR");
  }
}

void setMotorSpeed(int motorId, int speed) {
  // Clamp speed to valid range
  speed = constrain(speed, -100, 100);
  
  // Convert percentage to PWM microseconds
  // 1500µs = stop, 1000µs = full reverse, 2000µs = full forward
  int pwmValue = map(speed, -100, 100, 1000, 2000);
  
  if (motorId == 0) {
    leftSpeed = speed;
    leftMotor.writeMicroseconds(pwmValue);
    digitalWrite(LEFT_DIR_PIN, speed >= 0 ? HIGH : LOW);
  } else if (motorId == 1) {
    rightSpeed = speed;
    rightMotor.writeMicroseconds(pwmValue);
    digitalWrite(RIGHT_DIR_PIN, speed >= 0 ? HIGH : LOW);
  }
}