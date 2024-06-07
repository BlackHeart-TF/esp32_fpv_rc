#ifndef M58SERVOUNIT
#define M58SERVOUNIT
#include "driver/i2c.h"
typedef struct {
    uint8_t i2c_num;
    uint8_t i2c_addr;
} EightServosUnit;

enum ServoMode {
    smInput,
    smDigitalOutput,
    smADC,
    smServo,
    smNeoPixel,
    smPWM
};

enum ServoAddress{
    AddrModeRoot = 0x00,
    AddrVersion = 0xFE
};

esp_err_t SetMode(EightServosUnit* unit,uint8_t port, enum ServoMode mode);
esp_err_t setServoPulse(EightServosUnit* unit, uint8_t port,uint16_t position);
EightServosUnit* eightServosUnitCreate(uint8_t port,uint8_t addr);

#endif