#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_timer.h"
#include <esp_log.h>

#if CONFIG_USE_8SERVOS_UNIT
    #include "driver/8servos_unit.h"
    8ServosUnit unit_8servo(I2C_MASTER_NUM);
#else
    
#endif


bool servoRunning = false;
short servoX = 1500;
short servoY = 1500;
long lastAction = 0;

static const char *TAG = "servo";

#define IDLE_TIMEOUT 800 //ms before resetting axis

inline int max(int a, int b) {
    return a > b ? a : b;
}

inline int min(int a, int b) {
    return a < b ? a : b;
}

void stop_servos(){
    ESP_LOGI(TAG, "Ending servo loop...");
    servoRunning = false;
}

void SetServo(short valueX,short valueY){
    servoX = min((uint16_t)2000,max((uint16_t)1000,valueX));
    servoY = min((uint16_t)2000,max((uint16_t)1000,valueY));
    lastAction = esp_timer_get_time() / 1000;
}

void commit_servos(){
#if CONFIG_USE_8SERVOS_UNIT
    unit_8servo.setServoPosition(0,servoX);
    unit_8servo.setServoPosition(1,servoY);
#else

#endif
}

void threadLoop(){
    while (servoRunning){
        long curtime = esp_timer_get_time() / 1000;
        if(curtime -lastAction > IDLE_TIMEOUT)
            SetServo((short)1500,(short)1500);
        commit_servos();
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}




void start_servos(void)
{
    servoRunning = true;
    xTaskCreatePinnedToCore(&threadLoop, "servo", 4096, NULL, 10, NULL, tskNO_AFFINITY);
}
