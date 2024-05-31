#include <esp_log.h>
#include "lwip/sockets.h"
#include "lwip/netdb.h"
#include "lwip/api.h"
#include "errno.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

struct netconn *camera_conn;
struct ip_addr peer_addr;
static const char *TAG = "netconn";
bool listenerRunning = false;

void stop_listener(){
    ESP_LOGI(TAG, "Ending Listener loop...");
    listenerRunning = false;
}

void listenThread()
{
    ESP_LOGI(TAG, "Starting listener loop...");
    camera_conn = netconn_new(NETCONN_UDP);
    if (camera_conn == NULL)
    {
        ESP_LOGE(TAG, "netconn_new err");
        stop_listener();
        return;
    }

    err_t err = netconn_bind(camera_conn, IPADDR_ANY, 55555);
    if (err != ERR_OK)
    {
        ESP_LOGE(TAG, "netconn_bind err %d", err);
        netconn_delete(camera_conn);
        stop_listener();
        return;
    }

    while (listenerRunning)
    {
        struct netbuf *rxbuf;
        err = netconn_recv(camera_conn, &rxbuf);
        if (err == ERR_OK)
        {
            uint8_t *data;
            u16_t len;
            netbuf_data(rxbuf, (void **)&data, &len);
            if (len)
            {
                ESP_LOGI(TAG, "netconn_recv %d", len);
                switch (data[0])
                {
                    case 0x54: //servo control first for latency
                        uint16_t valueX = (uint16_t)(data[1]) | ((uint16_t)(data[2]) << 8);
                        uint16_t valueY = (uint16_t)(data[3]) | ((uint16_t)(data[4]) << 8);
                        //SetServo(valueX ,valueY);
                        break;
                    case 0x55: //start stream
                        peer_addr = *netbuf_fromaddr(rxbuf);
                        ESP_LOGI(TAG, "peer %lx", peer_addr.u_addr.ip4.addr);

                        ESP_LOGI(TAG, "Trigged!");
                        break;
                    case 0x56: //stop stream
                        peer_addr.u_addr.ip4.addr = IPADDR_ANY;
                        //SetServo(valueX ,valueY);
                        break;
                    default:
                        ESP_LOGI(TAG, "Unknown command:0x%02X", data[0]);
                }
            }
            netbuf_delete(rxbuf);
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }
    ESP_LOGI(TAG, "Listener loop ended.");
    
}

void start_listener(void)
{
    listenerRunning = true;
    xTaskCreatePinnedToCore(&listenThread, "listener", 4096, NULL, 10, NULL, tskNO_AFFINITY);
}



