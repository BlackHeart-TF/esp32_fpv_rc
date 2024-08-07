#include <esp_log.h>
#include <esp_system.h>
#include <esp_timer.h>
#include <nvs_flash.h>
#include <sys/param.h>
#include <string.h>

#include "lwip/sockets.h"
#include "lwip/netdb.h"
#include "lwip/api.h"
#include "errno.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

// support IDF 5.x
#ifndef portTICK_RATE_MS
#define portTICK_RATE_MS portTICK_PERIOD_MS
#endif

#ifdef CONFIG_CAMERA_FLIP
#define CAMERA_FLIP CONFIG_CAMERA_FLIP
#else
#define CAMERA_FLIP false
#endif
#ifdef CONFIG_CAMERA_MIRROR
#define CAMERA_MIRROR CONFIG_CAMERA_MIRROR
#else
#define CAMERA_MIRROR false
#endif

#include "esp_camera.h"
#include "camera_pins.h"

static const char *TAG = "camera";

esp_err_t init_camera(void)
{
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer = LEDC_TIMER_0;
    config.pin_d0 = Y2_GPIO_NUM;
    config.pin_d1 = Y3_GPIO_NUM;
    config.pin_d2 = Y4_GPIO_NUM;
    config.pin_d3 = Y5_GPIO_NUM;
    config.pin_d4 = Y6_GPIO_NUM;
    config.pin_d5 = Y7_GPIO_NUM;
    config.pin_d6 = Y8_GPIO_NUM;
    config.pin_d7 = Y9_GPIO_NUM;
    config.pin_xclk = XCLK_GPIO_NUM;
    config.pin_pclk = PCLK_GPIO_NUM;
    config.pin_vsync = VSYNC_GPIO_NUM;
    config.pin_href = HREF_GPIO_NUM;
    config.pin_sccb_sda = SIOD_GPIO_NUM;
    config.pin_sccb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn = PWDN_GPIO_NUM;
    config.pin_reset = RESET_GPIO_NUM;
    config.xclk_freq_hz = 24000000;
    // config.xclk_freq_hz = 36000000;
    config.pixel_format = PIXFORMAT_JPEG;
    // config.frame_size = FRAMESIZE_QVGA; // 320 * 240 / 5 = 15,360 < 32,768
    config.frame_size = FRAMESIZE_CIF; // 400 * 296 / 5 = 23,680 < 32,768
    // config.frame_size = FRAMESIZE_HVGA; // 480 * 320 / 5 = 30,720 < 32,768
    config.jpeg_quality = 10;
    config.fb_count = 2;
    config.fb_location = CAMERA_FB_IN_DRAM;
    config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
    // config.grab_mode = CAMERA_GRAB_LATEST;
    config.fragment_mode = true;
    config.zero_padding = false;
    

    // camera init
    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK)
    {
        ESP_LOGE(TAG, "Camera Init Failed error 0x%x", err);
        return err;
    }

    sensor_t *s = esp_camera_sensor_get();

    // drop down frame size for higher initial frame rate
    s->set_framesize(s, FRAMESIZE_CIF);
    // s->set_framesize(s, FRAMESIZE_QVGA);
    // s->set_framesize(s, FRAMESIZE_VGA);
    // s->set_framesize(s, FRAMESIZE_XGA);
    // s->set_framesize(s, FRAMESIZE_HD);
    // s->set_framesize(s, FRAMESIZE_SXGA);

    s->set_hmirror(s, CAMERA_MIRROR);
    s->set_vflip(s, CAMERA_FLIP);
    return ESP_OK;
}


extern struct netconn *camera_conn;
extern struct ip_addr peer_addr;
extern uint16_t peer_port;

static void camera_tx(void *param)
{
    size_t packet_max = 32768;
    struct netbuf *txbuf = netbuf_new();

    uint32_t frame_count = 0;
    uint32_t frame_size_sum = 0;
    int64_t start = esp_timer_get_time();

    while (1)
    {
        if (peer_addr.u_addr.ip4.addr == IPADDR_ANY)
        {
            vTaskDelay(pdMS_TO_TICKS(50));
            continue;
        }
        camera_fb_t *fb = esp_camera_fb_get();
        if (!fb)
        {
            ESP_LOGE(TAG, "Camera capture failed");
            continue;
        }

        uint8_t *buf = fb->buf;
        size_t total = fb->len;
        size_t send = 0;

        // ESP_LOGI(TAG, "send %d", total);

        for (; send < total;)
        {
            size_t txlen = total - send;
            if (txlen > packet_max)
            {
                txlen = packet_max;
            }
            err_t err = netbuf_ref(txbuf, &buf[send], txlen);
            if (err == ERR_OK)
            {
                err = netconn_sendto(camera_conn, txbuf, &peer_addr, 55556);
                if (err == ERR_OK)
                {
                    send += txlen;
                }
                else if (err == ERR_MEM)
                {
                    ESP_LOGW(TAG, "netconn_sendto ERR_MEM");
                    vTaskDelay(pdMS_TO_TICKS(10));
                }
                else
                {
                    ESP_LOGE(TAG, "netconn_sendto err %d", err);
                    break;
                }
            }
            else
            {
                ESP_LOGE(TAG, "netbuf_ref err %d", err);
                break;
            }
        }

        esp_camera_fb_return(fb);

        if (buf[0] == 0xff && buf[1] == 0xd8 && buf[2] == 0xff)
        {
            frame_count++;
        }
        frame_size_sum += total;

        int64_t end = esp_timer_get_time();
        int64_t pasttime = end - start;
        if (pasttime > 1000000)
        {
            start = end;
            float adj = 1000000.0 / (float)pasttime;
            float mbps = (frame_size_sum * 8.0 * adj) / 1024.0 / 1024.0;
            ESP_LOGI(TAG, "%.1f fps %.3f Mbps", frame_count * adj, mbps);
            frame_count = 0;
            frame_size_sum = 0;
        }

        vTaskDelay(pdMS_TO_TICKS(1));
    }
}

void start_camera(void)
{
    xTaskCreatePinnedToCore(&camera_tx, "camera_tx", 4096, NULL, 10, NULL, tskNO_AFFINITY);
}
