#include <esp_now.h>
#include <WiFi.h>
#include <MPU9250_asukiaaa.h>

// Define global variables
int16_t accelRaw[3], gyroRaw[3], tempRaw; // Raw sensor data arrays
double accel[3], gyro[3]; // Processed acceleration and gyroscope data
double thetaAcc, phiAcc; // Angle calculated from accelerometer
double thetaLP = 0, phiLP = 0; // Low-pass filter values for angles
double thetaGyro = 0, phiGyro = 0; // Angle calculated from gyroscope
double thetaComp, phiComp; // Complementary filtered angles
unsigned long prevTime = 0; // Previous time for calculations
const uint8_t interval = 500; // Interval for data processing (milliseconds)
int forward = 0, backward = 0, left = 0, right = 0; // Movement direction flags

// Receiver MAC address
uint8_t broadcastAddress[] = { 0x3C, 0xE9, 0x0E, 0x83, 0x86, 0x04 };

// Structure for control message
typedef struct {
    int forward;
    int backward;
    int left;
    int right;
} ControlMessage;

ControlMessage message; // Control message instance
esp_now_peer_info_t peer; // Peer device information

bool readyToPrint = false; // Flag for printing debug info
long lastPrintTime = 0; // Last time debug info was printed

// ESP-NOW data send callback function
void onSendComplete(const uint8_t *macAddr, esp_now_send_status_t status) {
    Serial.printf("Send Status: %s\n", status == ESP_NOW_SEND_SUCCESS ? "Success" : "Failed");
}

// Initialize MPU9250 sensor
void initializeMPU9250() {
    Wire.beginTransmission(MPU9250_ADDRESS_AD0_LOW);
    Wire.write(0x6B); // PWR_MGMT_1 register
    Wire.write(0x00); // Wake up MPU9250
    Wire.endTransmission(true);

    Wire.beginTransmission(MPU9250_ADDRESS_AD0_LOW);
    Wire.write(0x1C); // ACCEL_CONFIG register
    Wire.write(ACC_FULL_SCALE_2_G); // Set full scale to ±2g
    Wire.endTransmission(true);

    Wire.beginTransmission(MPU9250_ADDRESS_AD0_LOW);
    Wire.write(0x1B); // GYRO_CONFIG register
    Wire.write(GYRO_FULL_SCALE_250_DPS); // Set full scale to ±250°/s
    Wire.endTransmission(true);

    Wire.beginTransmission(MPU9250_ADDRESS_AD0_LOW);
    Wire.write(0x37); // INT_PIN_CFG register
    Wire.write(0x02); // Enable bypass mode
    Wire.endTransmission(true);

    delay(100); // Delay to allow sensor to stabilize
}

// Initialize ESP-NOW communication
void initializeESPNow() {
    if (esp_now_init() != ESP_OK) {
        Serial.println("ESP-NOW initialization failed");
        ESP.restart(); // Restart if initialization fails
    }

    // Register send callback function
    esp_now_register_send_cb(onSendComplete);

    // Set peer device information
    memcpy(peer.peer_addr, broadcastAddress, 6);
    peer.channel = 0; // Use default channel
    peer.encrypt = false; // No encryption

    // Add peer device to the list
    if (esp_now_add_peer(&peer) != ESP_OK) {
        Serial.println("Failed to add peer device");
        ESP.restart(); // Restart if adding peer fails
    }
}

// Read data from MPU9250 sensor
void readMPU9250Data() {
    Wire.beginTransmission(MPU9250_ADDRESS_AD0_LOW);
    Wire.write(0x3B); // Start reading from ACCEL_XOUT_H register
    Wire.endTransmission(false);
    Wire.requestFrom(MPU9250_ADDRESS_AD0_LOW, 14, true); // Request 14 bytes of data

    accelRaw[0] = Wire.read() << 8 | Wire.read(); // Read acceleration X-axis raw value
    accelRaw[1] = Wire.read() << 8 | Wire.read(); // Read acceleration Y-axis raw value
    accelRaw[2] = Wire.read() << 8 | Wire.read(); // Read acceleration Z-axis raw value
    tempRaw = Wire.read() << 8 | Wire.read();     // Read temperature raw value
    gyroRaw[0] = Wire.read() << 8 | Wire.read();   // Read gyroscope X-axis raw value
    gyroRaw[1] = Wire.read() << 8 | Wire.read();   // Read gyroscope Y-axis raw value
    gyroRaw[2] = Wire.read() << 8 | Wire.read();   // Read gyroscope Z-axis raw value
}

// Process sensor data to calculate angles and movement directions
void processSensorData() {
    // Convert accelerometer data to g's
    accel[0] = accelRaw[0] / 16384.0;
    accel[1] = accelRaw[1] / 16384.0;
    accel[2] = accelRaw[2] / 16384.0;

    // Convert gyroscope data to degrees per second (dps)
    gyro[0] = gyroRaw[0] / 131.0;
    gyro[1] = gyroRaw[1] / 131.0;
    gyro[2] = gyroRaw[2] / 131.0;

    // Calculate angles using accelerometer data (in degrees)
    thetaAcc = atan2(accel[0], accel[2]) * 180 / PI; 
    phiAcc = atan2(accel[1], accel[2]) * 180 / PI;

    // Apply low-pass filter to angle calculations 
    thetaLP = 0.7 * thetaLP + 0.3 * thetaAcc;
    phiLP = 0.7 * phiLP + 0.3 * phiAcc;

    // Calculate angles using gyroscope data over time (dt)
    unsigned long currTime = millis();
    double dt = (currTime - prevTime) / 1000.0; 
    prevTime = currTime;

    thetaGyro -= gyro[1] * dt; 
    phiGyro += gyro[0] * dt;

    // Apply complementary filter to combine accelerometer and gyroscope data for angles 
    thetaComp = 0.95 * (thetaComp - gyro[1] * dt) + 0.05 * thetaAcc;
    phiComp = 0.95 * (phiComp + gyro[0] * dt) + 0.05 * phiAcc;
}

// Determine movement direction based on accelerometer readings 
void determineMovement() {
    forward = accel[1] > 0.7 ? 1 : 0;   // Forward if acceleration in Y-axis is positive and exceeds threshold 
    backward = accel[1] < -0.7 ? 1 : 0;   // Backward if acceleration in Y-axis is negative and exceeds threshold 
    left = accel[0] > 0.7 ? 1 : 0;       // Left if acceleration in X-axis is positive and exceeds threshold 
    right = accel[0] < -0.7 ? 1 : 0;     // Right if acceleration in X-axis is negative and exceeds threshold 

   message.forward = forward * 10;       // Set forward movement value in message structure 
   message.backward = backward * 10;     // Set backward movement value in message structure 
   message.left = left * 10;             // Set left movement value in message structure 
   message.right = right * 10;           // Set right movement value in message structure 
}

// Send control data over ESP-NOW communication 
void sendControlData() {
   esp_err_t result = esp_now_send(broadcastAddress, (uint8_t *)&message, sizeof(message)); 
   if (result != ESP_OK) { 
       Serial.println("Data send failed"); 
   }
}

// Print debug information to the serial monitor 
void printDebugInfo() {
   if (readyToPrint) { 
       Serial.printf("ax: %.2f, ay: %.2f, az: %.2f\n", accel[0], accel[1], accel[2]); 
       Serial.printf("Forward: %d, Backward: %d, Left: %d, Right: %d\n", forward, backward, left, right); 
       readyToPrint = false; 
   }
}

void setup() {
   Serial.begin(115200);                  // Start serial communication at baud rate of 115200 
   WiFi.mode(WIFI_STA);                   // Set WiFi mode to Station mode 
   initializeESPNow();                    // Initialize ESP-NOW communication 
   Wire.begin();                          // Initialize I2C communication 
   initializeMPU9250();                   // Initialize MPU9250 sensor 
   prevTime = millis();                   // Initialize previous time variable 
}

void loop() {
   if (millis() - lastPrintTime > interval) {  
       lastPrintTime = millis();            // Update last print time  
       readyToPrint = true;                 

       readMPU9250Data();                   // Read data from MPU9250 sensor  
       processSensorData();                 // Process the sensor data  
       determineMovement();                 // Determine the movement direction  
       sendControlData();                   // Send control data via ESP-NOW  
       printDebugInfo();                    // Print debug information  
   }
}
