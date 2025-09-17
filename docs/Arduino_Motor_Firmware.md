# Arduino Motor Control Firmware

This document describes the Arduino firmware required for the Jetson Hardware motor control system.

## Hardware Setup

### Arduino Nano Connections
- **USB**: Connect to Jetson for serial communication
- **Pin 5**: PWM output to Left Motor ESC
- **Pin 6**: PWM output to Right Motor ESC  
- **Pin 7**: Direction control for Left Motor (optional)
- **Pin 8**: Direction control for Right Motor (optional)
- **Pin 13**: Built-in LED for status indication

### ESC Configuration
- **PWM Frequency**: 50Hz (20ms period)
- **Pulse Width Range**: 1000-2000µs
  - 1500µs = Neutral/Stop
  - 1000µs = Full Reverse
  - 2000µs = Full Forward

## Communication Protocol

### Serial Settings
- **Baud Rate**: 115200
- **Data Format**: 8N1 (8 data bits, no parity, 1 stop bit)
- **Line Ending**: `\n` (newline)

### Command Format
All commands are ASCII strings terminated with newline (`\n`):

```
PING                    - Test connection (respond with "PONG")
ESTOP                   - Emergency stop all motors
MOTOR:<id>:<speed>      - Set motor speed
SERVO:<id>:<angle>      - Set servo angle (future)
LED:<r>:<g>:<b>         - Set status LED (future)
STATUS                  - Get Arduino status
```

### Motor Commands
```
MOTOR:0:50     - Left motor 50% forward
MOTOR:1:-30    - Right motor 30% reverse
MOTOR:0:0      - Left motor stop
```

- **Motor ID**: 0 = Left, 1 = Right
- **Speed**: -100 to +100 (percentage)
  - Negative = Reverse
  - Positive = Forward
  - 0 = Stop

### Responses
- **"OK"** - Command executed successfully
- **"PONG"** - Response to PING command
- **"ERROR"** - Command failed or invalid

## Sample Arduino Code

```cpp
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
```

## Safety Features

### Watchdog Timer
- Arduino stops all motors if no commands received for 1 second
- Prevents runaway if Jetson crashes or disconnects
- Sends "WATCHDOG_TIMEOUT" message

### Emergency Stop
- `ESTOP` command immediately stops all motors
- Blocks all subsequent motor commands until restart
- Can be triggered by hardware button (future enhancement)

### Input Validation
- All commands validated before execution
- Invalid commands return "ERROR"
- Speed values clamped to safe ranges

## Status Monitoring

### LED Indicators
- **Pin 13 LED**: Blinks every second when running
- **Solid ON**: During initialization
- **Fast Blink**: Emergency stop active (future)

### Serial Monitoring
- All commands logged to serial output
- Status command provides current motor states
- Error messages for debugging

## Future Enhancements

### Additional Devices
```cpp
// Servo control
SERVO:0:90     - Set servo 0 to 90 degrees

// LED control  
LED:255:0:0    - Set status LED to red

// Sensor reading
SENSOR:0       - Read sensor 0 value
```

### Hardware Additions
- Current sensing on analog pins
- Encoder inputs for feedback
- I2C expansion for additional sensors
- CAN bus communication

## Installation Steps

1. **Install Arduino IDE**
2. **Connect Arduino Nano via USB**
3. **Select Board**: Arduino Nano
4. **Select Processor**: ATmega328P (Old Bootloader if needed)
5. **Select Port**: Usually `/dev/ttyUSB0` on Linux
6. **Upload Code**: Paste the sample code and upload
7. **Test**: Use Serial Monitor at 115200 baud to test commands

## Troubleshooting

### Connection Issues
- Check USB cable and port
- Verify Arduino appears as `/dev/ttyUSB0`
- Test with Arduino IDE Serial Monitor first

### Motor Issues
- Verify ESC calibration and wiring
- Check power supply to motors
- Test ESCs individually with servo tester

### Communication Issues
- Confirm baud rate (115200)
- Check for electrical interference
- Verify command format exactly matches protocol