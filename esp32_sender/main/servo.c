#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

bool servoRunning = false;
short servoX = 1500;
short servoY = 1500;
long lastAction = 0;

void stop_servos(){
    ESP_LOGI(TAG, "Ending servo loop...");
    servoRunning = false;
}

void threadLoop(){
    while (servoRunning){

        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

void SetServo(short valueX,short valueY){
    servoX = valueX;
    servoY = valueY;
    lastAction = esp_timer_get_time() / 1000;
}


void start_servos(void)
{
    servoRunning = true;
    xTaskCreatePinnedToCore(&threadLoop, "servo", 4096, NULL, 10, NULL, tskNO_AFFINITY);
}
