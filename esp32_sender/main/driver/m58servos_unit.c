
#include <esp_log.h>
#include "m58servos_unit.h"
#if CONFIG_USE_8SERVOS_UNIT
#define I2C_MASTER_SCL_IO    CONFIG_SCL_PIN    // GPIO number for I2C master clock
#define I2C_MASTER_SDA_IO    CONFIG_SDA_PIN    // GPIO number for I2C master data
#define I2C_MASTER_NUM       I2C_NUM_0 // I2C port number for master dev
#define I2C_MASTER_FREQ_HZ   100000     // I2C master clock frequency
#define I2C_SLAVE_ADDR       CONFIG_SERVO_I2C_ADDR // I2C slave address for servo controller
#define I2C_MASTER_TIMEOUT_MS 10



void i2c_scan() {
    uint8_t addr;

    ESP_LOGI("I2C", "Scanning I2C bus...");

    for (addr = 0x01; addr < 0x7F; addr++) {
        i2c_cmd_handle_t cmd = i2c_cmd_link_create();
        i2c_master_start(cmd);
        i2c_master_write_byte(cmd, (addr << 1) | I2C_MASTER_WRITE, true);
        i2c_master_stop(cmd);
        int ret = i2c_master_cmd_begin(I2C_NUM_0, cmd, pdMS_TO_TICKS(I2C_MASTER_TIMEOUT_MS));
        i2c_cmd_link_delete(cmd);

        if (ret == ESP_OK) {
            ESP_LOGI("I2C", "Device found at address 0x%02x", addr);
        }
    }

    ESP_LOGI("I2C", "I2C bus scan complete");
}
esp_err_t SetMode(EightServosUnit* unit, uint8_t port, enum ServoMode mode){
    if (port >= 8) {
        ESP_LOGE("8servos", "Only 8 Ports! (0-7)");   
        return ESP_ERR_INVALID_ARG; 
    }
    i2c_cmd_handle_t cmd_handle = i2c_cmd_link_create();
    if (cmd_handle == NULL) {
        ESP_LOGE("8servos", "Failed to create I2C command link");
        return ESP_FAIL;
    }

    i2c_master_start(cmd_handle);
    i2c_master_write_byte(cmd_handle, (unit->i2c_addr << 1) | I2C_MASTER_WRITE, true);
    i2c_master_write_byte(cmd_handle, AddrModeRoot+port, true);
    i2c_master_write_byte(cmd_handle, mode, true);
    i2c_master_stop(cmd_handle);
    int ret = i2c_master_cmd_begin(unit->i2c_num, cmd_handle, pdMS_TO_TICKS(I2C_MASTER_TIMEOUT_MS));

    if (ret != ESP_OK) {
        ESP_LOGE("8servos", "I2C set 3 failed: %d", ret);
        return ret;
    }
    return ESP_OK;
}

esp_err_t i2creadBytes(EightServosUnit* unit, uint8_t reg, uint8_t *buffer, uint8_t length) {
    i2c_cmd_handle_t cmd = i2c_cmd_link_create();
    if (cmd == NULL) {
        ESP_LOGE("8servos", "Failed to create I2C command link");
        return ESP_FAIL;
    }
    uint8_t i2caddr = unit->i2c_addr;
    i2c_master_start(cmd);
    i2c_master_write_byte(cmd, (i2caddr << 1) | I2C_MASTER_WRITE, true);
    i2c_master_write_byte(cmd, reg, true);
    i2c_master_stop(cmd);
    esp_err_t err = i2c_master_cmd_begin(unit->i2c_num, cmd, pdMS_TO_TICKS(I2C_MASTER_TIMEOUT_MS));
    i2c_cmd_link_delete(cmd);

    if (err != ESP_OK) {
        return err;
    }

    cmd = i2c_cmd_link_create();
    i2c_master_start(cmd);
    i2c_master_write_byte(cmd, (unit->i2c_addr << 1) | I2C_MASTER_READ, true);
    i2c_master_read(cmd, buffer, length, I2C_MASTER_LAST_NACK);
    i2c_master_stop(cmd);
    err = i2c_master_cmd_begin(unit->i2c_num, cmd, pdMS_TO_TICKS(I2C_MASTER_TIMEOUT_MS));
    i2c_cmd_link_delete(cmd);

    return err;
}

bool checkDeviceVersion(EightServosUnit* unit) {
    uint8_t version = 0;
    i2c_cmd_handle_t cmd_handle = i2c_cmd_link_create();
    if (cmd_handle == NULL) {
        ESP_LOGE("8servos", "Failed to create I2C command link");
        return false;
    }

    bool read = i2creadBytes(unit,AddrVersion,&version,1);
    if (read != ESP_OK){
        ESP_LOGE("8servos", "Failed to read device");
        return false;
    }
    if (version <= 0) {
        ESP_LOGW("8servos", "Device version not found, Got: 0x%x", version);
        return false;
    }
    ESP_LOGI("8servos", "Device version: 0x%x", version);
    return true;
}

EightServosUnit* eightServosUnitCreate(uint8_t port,uint8_t addr) {
    EightServosUnit* unit = malloc(sizeof(EightServosUnit));
    unit->i2c_num = port;
    unit->i2c_addr = addr;

    i2c_config_t conf;
    conf.mode = I2C_MODE_MASTER;
    conf.sda_io_num = I2C_MASTER_SDA_IO;
    conf.sda_pullup_en = GPIO_PULLUP_ENABLE;
    conf.scl_io_num = I2C_MASTER_SCL_IO;
    conf.scl_pullup_en = GPIO_PULLUP_ENABLE;
    conf.master.clk_speed = I2C_MASTER_FREQ_HZ;
    esp_err_t err = i2c_param_config(unit->i2c_num, &conf);
    i2c_driver_install(unit->i2c_num, conf.mode, 0, 0, 0);
    if (err != ESP_OK) {
        return -1;
    }
    //i2c_scan();
    bool found = checkDeviceVersion(unit);
    if (!found) {
        return -2;
    }
    return unit;
}


esp_err_t setServoPulse(EightServosUnit* unit, uint8_t port,uint16_t position) {
    if (port >= 8) return ESP_ERR_INVALID_ARG; // We're only using the first 2 ports
    uint8_t cmd[3] = {0x60 + port * 2, (uint8_t)(position & 0xFF), (uint8_t)(position >> 8)};
    i2c_cmd_handle_t cmd_handle = i2c_cmd_link_create();
    i2c_master_start(cmd_handle);
    i2c_master_write_byte(cmd_handle, (I2C_SLAVE_ADDR << 1) | I2C_MASTER_WRITE, true);
    i2c_master_write(cmd_handle, cmd, 3, true);
    i2c_master_stop(cmd_handle);
    int ret = i2c_master_cmd_begin(unit->i2c_num, cmd_handle, 10);
    if (ret != ESP_OK) {
        ESP_LOGE("8servo", "I2C command failed: %d", ret);
    }
    i2c_cmd_link_delete(cmd_handle);
    return ret;
}
#endif //CONFIG_USE_8SERVOS_UNIT