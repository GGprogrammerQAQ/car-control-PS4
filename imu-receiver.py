#include <Arduino.h>
#include <esp_now.h>
#include <WiFi.h>

// Motor control constants
#define FORWARD 1
#define BACKWARD 2
#define LEFT 3
#define RIGHT 4
#define STOP 0

// Motor pin definitions
//const int enableFrontRightMotor = 25;
const int FrontRightMotorPin1 = 18;
const int FrontRightMotorPin2 = 19;

//const int enableBackRightMotor = 27;
const int BackRightMotorPin1 = 4;
const int BackRightMotorPin2 = 16;

//const int enableFrontLeftMotor = 33;
const int FrontLeftMotorPin1 = 12;
const int FrontLeftMotorPin2 = 13;

//const int enableBackLeftMotor = 26;
const int BackLeftMotorPin1 = 21;
const int BackLeftMotorPin2 = 22;

// Structure for receiving data
typedef struct struct_message {
    int forward;
    int backward;
    int left;
    int right;
} struct_message;

struct_message receivedData; // Variable to store received data

void initializeMotors() {
    // Set all motor pins to OUTPUT mode
    pinMode(enableFrontRightMotor, OUTPUT);
    pinMode(FrontRightMotorPin1, OUTPUT);
    pinMode(FrontRightMotorPin2, OUTPUT);

    pinMode(enableBackRightMotor, OUTPUT);
    pinMode(BackRightMotorPin1, OUTPUT);
    pinMode(BackRightMotorPin2, OUTPUT);

    pinMode(enableFrontLeftMotor, OUTPUT);
    pinMode(FrontLeftMotorPin1, OUTPUT);
    pinMode(FrontLeftMotorPin2, OUTPUT);

    pinMode(enableBackLeftMotor, OUTPUT);
    pinMode(BackLeftMotorPin1, OUTPUT);
    pinMode(BackLeftMotorPin2, OUTPUT);

    // Stop all motors initially
    digitalWrite(enableFrontRightMotor, LOW);
    digitalWrite(enableBackRightMotor, LOW);
    digitalWrite(enableFrontLeftMotor, LOW);
    digitalWrite(enableBackLeftMotor, LOW);
}

void controlMotor(int motorID, int direction) {
    int pin1, pin2;

    // Select motor pins based on motorID
    switch (motorID) {
        case 1: // Back Right Motor
            pin1 = BackRightMotorPin1;
            pin2 = BackRightMotorPin2;
            break;
        case 2: // Back Left Motor
            pin1 = BackLeftMotorPin1;
            pin2 = BackLeftMotorPin2;
            break;
        case 3: // Front Right Motor
            pin1 = FrontRightMotorPin1;
            pin2 = FrontRightMotorPin2;
            break;
        case 4: // Front Left Motor
            pin1 = FrontLeftMotorPin1;
            pin2 = FrontLeftMotorPin2;
            break;
        default:
            return;
    }

    // Set motor direction
    digitalWrite(pin1, direction > 0 ? HIGH : LOW);
    digitalWrite(pin2, direction < 0 ? HIGH : LOW);

    // Enable all motors
    digitalWrite(enableFrontRightMotor, HIGH);
    digitalWrite(enableBackRightMotor, HIGH);
    digitalWrite(enableFrontLeftMotor, HIGH);
    digitalWrite(enableBackLeftMotor, HIGH);
}

void executeMovement(int command) {
    switch (command) {
        case FORWARD:
            controlMotor(1, 1); // Back Right Motor forward
            controlMotor(2, 1); // Back Left Motor forward
            controlMotor(3, 1); // Front Right Motor forward
            controlMotor(4, 1); // Front Left Motor forward
            break;

        case BACKWARD:
            controlMotor(1, -1); // Back Right Motor backward
            controlMotor(2, -1); // Back Left Motor backward
            controlMotor(3, -1); // Front Right Motor backward
            controlMotor(4, -1); // Front Left Motor backward
            break;

        case LEFT:
            controlMotor(1, 1);  // Back Right Motor forward
            controlMotor(2, -1); // Back Left Motor backward
            controlMotor(3, 1);  // Front Right Motor forward
            controlMotor(4, -1); // Front Left Motor backward
            break;

        case RIGHT:
            controlMotor(1, -1); // Back Right Motor backward
            controlMotor(2, 1);  // Back Left Motor forward
            controlMotor(3, -1); // Front Right Motor backward
            controlMotor(4, 1);  // Front Left Motor forward
            break;

        case STOP:
        default:
            // Stop all motors by disabling their enable pins
            digitalWrite(enableFrontRightMotor, LOW);
            digitalWrite(enableBackRightMotor, LOW);
            digitalWrite(enableFrontLeftMotor, LOW);
            digitalWrite(enableBackLeftMotor, LOW);
            break;
    }
}

void onDataReceived(const uint8_t *mac, const uint8_t *data, int len) {
    memcpy(&receivedData, data, sizeof(receivedData));
    Serial.print("Forward: ");
    Serial.println(receivedData.forward);
    Serial.print("Backward: ");
    Serial.println(receivedData.backward);
    Serial.print("Left: ");
    Serial.println(receivedData.left);
    Serial.print("Right: ");
    Serial.println(receivedData.right);
}

void setup() {
    Serial.begin(115200);

    // Set WiFi to station mode
    WiFi.mode(WIFI_MODE_STA);

    // Initialize ESP-NOW
    if (esp_now_init() != ESP_OK) {
        Serial.println("ESP-NOW initialization failed!");
        return;
    }

    Serial.println("ESP-NOW initialized successfully");
    esp_now_register_recv_cb(onDataReceived);

    // Initialize motor pins
    initializeMotors();
}

void loop() {
    if (receivedData.forward >= 10) {
        executeMovement(FORWARD);
    } else if (receivedData.backward >= 10) {
        executeMovement(BACKWARD);
    } else if (receivedData.left >= 10) {
        executeMovement(LEFT);
    } else if (receivedData.right >= 10) {
        executeMovement(RIGHT);
    } else {
        executeMovement(STOP); // Stop the car if no command is received
    }
}
