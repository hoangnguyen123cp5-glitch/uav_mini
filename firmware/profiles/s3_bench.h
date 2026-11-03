// UAV Mini bench defaults. Pin mapping is a proposal, not a verified board pinout.
// Called from upstream setDefaults(); stored parameters use a separate namespace.
motorPins[MOT_RL] = 4;
motorPins[MOT_RR] = 5;
motorPins[MOT_FR] = 6;
motorPins[MOT_FL] = 7;
pwmFrequency = 38000;
pwmResolution = 10;
pwmStop = 0;
pwmMin = 0;
pwmMax = -1;
imuModel = 1; // FlixPeriph MPU9250/MPU6500 family; confirm WHO_AM_I on purchase.
imuBus = 0;
imuSckPin = 12;
imuMisoPin = 13;
imuMosiPin = 11;
imuCsPin = 10;
imuIntPin = -1; // timer/polling; measure actual sample timing
imuRotation = Vector(0, 0, 0); // MUST verify physical axis alignment
voltagePin = -1; // leave disconnected until divider/power-off behavior verified
voltageScale = 2;
rcRxPin = -1;

