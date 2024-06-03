#include "driver/i2c.h"

#define I2C_MASTER_SCL_IO    SCL_PIN    // GPIO number for I2C master clock
#define I2C_MASTER_SDA_IO    SCL_PIN    // GPIO number for I2C master data
#define I2C_MASTER_NUM       I2C_NUM_0 // I2C port number for master dev
#define I2C_MASTER_FREQ_HZ   100000     // I2C master clock frequency
#define I2C_SLAVE_ADDR       SERVO_I2C_ADDR // I2C slave address for servo controller

class 8ServosUnit {
private:
    i2c_port_t i2c_num;

public:
    8ServosUnit(i2c_port_t port) : i2c_num(port) {
        i2c_config_t conf;
        conf.mode = I2C_MODE_MASTER;
        conf.sda_io_num = I2C_MASTER_SDA_IO;
        conf.sda_pullup_en = GPIO_PULLUP_ENABLE;
        conf.scl_io_num = I2C_MASTER_SCL_IO;
        conf.scl_pullup_en = GPIO_PULLUP_ENABLE;
        conf.master.clk_speed = I2C_MASTER_FREQ_HZ;
        i2c_param_config(i2c_num, &conf);
        i2c_driver_install(i2c_num, conf.mode, 0, 0, 0);
    }

    void setServoMode(uint8_t port, uint8_t mode) {
        if (port >= 8) return; // Only supports 8
        uint8_t cmd[2] = {port, mode};
        i2c_cmd_handle_t cmd_handle = i2c_cmd_link_create();
        i2c_master_start(cmd_handle);
        i2c_master_write_byte(cmd_handle, (I2C_SLAVE_ADDR << 1) | I2C_MASTER_WRITE, true);
        i2c_master_write(cmd_handle, cmd, 2, true);
        i2c_master_stop(cmd_handle);
        i2c_master_cmd_begin(i2c_num, cmd_handle, 1000 / portTICK_RATE_MS);
        i2c_cmd_link_delete(cmd_handle);
    }

    void setServoPosition(uint8_t port, uint16_t position) {
        if (port >= 2) return; // We're only using the first 2 ports
        uint8_t cmd[3] = {0x60 + port * 2, (uint8_t)(position & 0xFF), (uint8_t)(position >> 8)};
        i2c_cmd_handle_t cmd_handle = i2c_cmd_link_create();
        i2c_master_start(cmd_handle);
        i2c_master_write_byte(cmd_handle, (I2C_SLAVE_ADDR << 1) | I2C_MASTER_WRITE, true);
        i2c_master_write(cmd_handle, cmd, 3, true);
        i2c_master_stop(cmd_handle);
        i2c_master_cmd_begin(i2c_num, cmd_handle, 1000 / portTICK_RATE_MS);
        i2c_cmd_link_delete(cmd_handle);
    }
};

// void app_main() {
//     8ServosUnit servoController(I2C_MASTER_NUM);
//     // Use servoController object to control servos
// }
