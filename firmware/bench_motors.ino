// UAV Mini bench output driver. Original integration code; no flight output path.
// Demand telemetry may be nonzero; physical pins below always remain LOW.
#include <initializer_list>
float motors[4] = {0, 0, 0, 0};
int motorPins[4] = {4, 5, 6, 7};
int pwmFrequency = 38000;
int pwmResolution = 10;
int pwmStop = 0;
int pwmMin = 0;
int pwmMax = -1;
const int MOT_RL = 0, MOT_RR = 1, MOT_FR = 2, MOT_FL = 3;

void uavMiniHoldMotorPinsLow() {
    // Ignore mutable Flix parameters: they cannot redirect this output driver.
    for (int pin : {4, 5, 6, 7}) {
        digitalWrite(pin, LOW);
        pinMode(pin, OUTPUT);
    }
}

void setupMotors() {
    uavMiniHoldMotorPinsLow();
    print("UAV MINI BENCH: motor outputs permanently inhibited\n");
}

void sendMotors() { uavMiniHoldMotorPinsLow(); }
int getDutyCycle(float) { return 0; }

bool motorsActive() {
    // Retain demand-based semantics for upstream parameter/log handling.
    for (float demand : motors) if (demand != 0) return true;
    return false;
}

void testMotor(int, float) {
    for (float &demand : motors) demand = 0;
    uavMiniHoldMotorPinsLow();
    print("Motor test rejected: bench firmware has no PWM output\n");
}
