/**
 * Motor Controller for Jetson Hardware Platform
 * 
 * Controls two DC motors via PWM ESCs (Electronic Speed Controllers)
 * Communicates with Jetson via serial at 115200 baud
 * 
 * Commands:
 * - PING: Test connectivity (responds with PONG)
 * - ESTOP: Emergency stop all motors
 * - RESET: Clear emergency stop state and reset motors to zero
 * - MOTOR:id:speed: Set motor speed (-100 to 100%)
 * - STATUS: Get current motor speeds and emergency stop state
 * 
 * Pin Configuration:
 * - Pin 5: Left Motor PWM (ESC signal)
 * - Pin 6: Right Motor PWM (ESC signal)
 * - Pin 7: Left Motor Direction (optional direction indicator)
 * - Pin 8: Right Motor Direction (optional direction indicator)
 * 
 * Safety Features:
 * - Emergency stop functionality
 * - Speed range validation
 * - Watchdog timer (500ms timeout)
 * - PWM signal validation
 */

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
const unsigned long WATCHDOG_TIMEOUT = 5000; // 5 seconds (extended for testing)

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
    static bool watchdogWarning = false;
    if (!watchdogWarning) {
      setMotorSpeed(0, 0);
      setMotorSpeed(1, 0);
      Serial.println("WATCHDOG_TIMEOUT");
      watchdogWarning = true;
      // Don't set emergency stop, just stop motors
    }
  } else {
    static bool watchdogWarning = false;
    watchdogWarning = false; // Reset warning flag when commands resume
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
    emergencyStop = false; // Clear emergency stop on ping
    
  } else if (cmd == "ESTOP") {
    emergencyStop = true;
    setMotorSpeed(0, 0);
    setMotorSpeed(1, 0);
    Serial.println("OK");
    
  } else if (cmd == "RESET") {
    // Reset emergency stop state
    emergencyStop = false;
    setMotorSpeed(0, 0);
    setMotorSpeed(1, 0);
    Serial.println("OK");
    
  } else if (cmd.startsWith("MOTOR:")) {
    if (emergencyStop) {
      Serial.println("ERROR:ESTOP");
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
        Serial.println("ERROR:RANGE");
      }
    } else {
      Serial.println("ERROR:FORMAT");
    }
    
  } else if (cmd == "STATUS") {
    Serial.print("MOTORS:");
    Serial.print(leftSpeed);
    Serial.print(",");
    Serial.print(rightSpeed);
    Serial.print(" ESTOP:");
    Serial.print(emergencyStop ? "1" : "0");
    Serial.print(" TIME:");
    Serial.println(millis());
    
  } else if (cmd == "") {
    // Ignore empty commands
    return;
    
  } else {
    Serial.println("ERROR:UNKNOWN");
  }
}

void setMotorSpeed(int motorId, int speed) {
  // Clamp speed to valid range
  speed = constrain(speed, -100, 100);
  
  // Convert percentage to PWM microseconds
  // 1500µs = stop, 1000µs = full reverse, 2000µs = full forward
  int pwmValue = map(speed, -100, 100, 1000, 2000);
  
  // Ensure PWM value is within safe ESC range
  pwmValue = constrain(pwmValue, 1000, 2000);
  
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