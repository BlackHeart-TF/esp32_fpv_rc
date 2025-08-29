#include <esp_log.h>
#include "lwip/sockets.h"
#include "lwip/netdb.h"
#include "lwip/api.h"
#include "errno.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

struct netconn *camera_conn;
struct ip_addr peer_addr;
uint16_t peer_port;

static const char *TAG = "netconn";
bool listenerRunning = false;

void SetServo(short valueX,short valueY);

void stop_listener(){
    ESP_LOGI(TAG, "Ending Listener loop...");
    listenerRunning = false;
}

void listenThread()
{
    ESP_LOGI(TAG, "Starting listener loop...");
    camera_conn = netconn_new(NETCONN_UDP);
    struct netbuf *txbuf = netbuf_new();
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
    struct ip_addr temp_addr;
    uint16_t temp_port;

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
                ESP_LOGI(TAG, "netconn_recv 0x%02X %d",data[0], len);
                switch (data[0])
                {
                    case 0x54: //servo control first for latency
                        uint16_t valueX = (uint16_t)(data[1]) | ((uint16_t)(data[2]) << 8);
                        uint16_t valueY = (uint16_t)(data[3]) | ((uint16_t)(data[4]) << 8);
                        ESP_LOGI(TAG, "netconn_recv servo %d %d",valueX, valueY);
                        SetServo(valueX ,valueY);
                        break;
                    
                    case 0x55: //Client Detection
                        temp_addr = *netbuf_fromaddr(rxbuf);
                        temp_port = netbuf_fromport(rxbuf);
                        //ESP_LOGI(TAG, "Got Client: %lx : %d", peer_addr.u_addr.ip4.addr,peer_port);
                        char addr_str[16]; // Enough to hold an IPv4 address in string format
                        strcpy(addr_str, ipaddr_ntoa(&temp_addr));
                        ESP_LOGI(TAG, "Got Client: %s : %d", addr_str,temp_port);
                        // Test static 
                        uint8_t num = 0x55;
                        netbuf_ref(txbuf, &num, 1);
                        err = netconn_sendto(camera_conn, txbuf, &temp_addr, 55556);
                        err = netconn_sendto(camera_conn, txbuf, &temp_addr, temp_port);
                        break;
                    case 0x56: //stop stream
                        peer_addr.u_addr.ip4.addr = IPADDR_ANY;
                        peer_port = 0;
                        break;
                    case 0x57: //start stream
                        struct ip_addr temp2_addr = *netbuf_fromaddr(rxbuf);
                        uint16_t temp2_port = netbuf_fromport(rxbuf);
                        
                        if (temp2_addr.u_addr.ip4.addr == temp_addr.u_addr.ip4.addr )
                        {
                            peer_addr = temp2_addr;
                            peer_port = temp2_port;
                        }
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



