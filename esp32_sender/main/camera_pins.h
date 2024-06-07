#if defined(CONFIG_M5STACK_UNITCAM)
#define PWDN_GPIO_NUM     -1
#define RESET_GPIO_NUM    15
#define XCLK_GPIO_NUM     27
#define SIOD_GPIO_NUM     25
#define SIOC_GPIO_NUM     23

#define Y9_GPIO_NUM       19
#define Y8_GPIO_NUM       36
#define Y7_GPIO_NUM       18
#define Y6_GPIO_NUM       39
#define Y5_GPIO_NUM        5
#define Y4_GPIO_NUM       34
#define Y3_GPIO_NUM       35
#define Y2_GPIO_NUM       32
#define VSYNC_GPIO_NUM    22
#define HREF_GPIO_NUM     26
#define PCLK_GPIO_NUM     21

#elif defined(CONFIG_M5STACK_UNITCAM_S3)
#define PWDN_GPIO_NUM     -1
#define RESET_GPIO_NUM    21
#define XCLK_GPIO_NUM     11
#define SIOD_GPIO_NUM     17
#define SIOC_GPIO_NUM     41

#define Y9_GPIO_NUM       13
#define Y8_GPIO_NUM       4
#define Y7_GPIO_NUM       10
#define Y6_GPIO_NUM       5
#define Y5_GPIO_NUM       7
#define Y4_GPIO_NUM       16
#define Y3_GPIO_NUM       15
#define Y2_GPIO_NUM       6
#define VSYNC_GPIO_NUM    42
#define HREF_GPIO_NUM     18
#define PCLK_GPIO_NUM     12

#elif defined(CONFIG_XIAO_ESP32S3_SENSE)
#define PWDN_GPIO_NUM     -1
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM     10
#define SIOD_GPIO_NUM     40
#define SIOC_GPIO_NUM     39

#define Y9_GPIO_NUM       48
#define Y8_GPIO_NUM       11
#define Y7_GPIO_NUM       12
#define Y6_GPIO_NUM       14
#define Y5_GPIO_NUM       16
#define Y4_GPIO_NUM       18
#define Y3_GPIO_NUM       17
#define Y2_GPIO_NUM       15
#define VSYNC_GPIO_NUM    38
#define HREF_GPIO_NUM     47
#define PCLK_GPIO_NUM     13

#elif defined(CONFIG_FREENOVE_ESP32S3_CAM)
#define PWDN_GPIO_NUM -1
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 15
#define SIOD_GPIO_NUM 4
#define SIOC_GPIO_NUM 5

#define Y2_GPIO_NUM 11
#define Y3_GPIO_NUM 9
#define Y4_GPIO_NUM 8
#define Y5_GPIO_NUM 10
#define Y6_GPIO_NUM 12
#define Y7_GPIO_NUM 18
#define Y8_GPIO_NUM 17
#define Y9_GPIO_NUM 16

#define VSYNC_GPIO_NUM 6
#define HREF_GPIO_NUM 7
#define PCLK_GPIO_NUM 13

# has ifs on everything so you can override a preset by leaving the rest blank
#elif defined(CONFIG_CUSTOM_CAMERA_PINS)
#if defined(CONFIG_PWDN_GPIO_NUM)
    #define PWDN_GPIO_NUM CONFIG_PWDN_GPIO_NUM
#endif
#if defined(CONFIG_RESET_GPIO_NUM)
    #define RESET_GPIO_NUM CONFIG_RESET_GPIO_NUM
#endif
#if defined(CONFIG_XCLK_GPIO_NUM)
    #define XCLK_GPIO_NUM CONFIG_XCLK_GPIO_NUM
#endif
#if defined(CONFIG_SIOD_GPIO_NUM)
    #define SIOD_GPIO_NUM CONFIG_SIOD_GPIO_NUM
#endif
#if defined(CONFIG_SIOC_GPIO_NUM)
    #define SIOC_GPIO_NUM CONFIG_SIOC_GPIO_NUM
#endif

#if defined(CONFIG_Y2_GPIO_NUM)
    #define Y2_GPIO_NUM CONFIG_Y2_GPIO_NUM
#endif
#if defined(CONFIG_Y3_GPIO_NUM)
    #define Y3_GPIO_NUM CONFIG_Y3_GPIO_NUM
#endif
#if defined(CONFIG_Y4_GPIO_NUM)
    #define Y4_GPIO_NUM CONFIG_Y4_GPIO_NUM
#endif
#if defined(CONFIG_Y5_GPIO_NUM)
    #define Y5_GPIO_NUM CONFIG_Y5_GPIO_NUM
#endif
#if defined(CONFIG_Y6_GPIO_NUM)
    #define Y6_GPIO_NUM CONFIG_Y6_GPIO_NUM
#endif
#if defined(CONFIG_Y7_GPIO_NUM)
    #define Y7_GPIO_NUM CONFIG_Y7_GPIO_NUM
#endif
#if defined(CONFIG_Y8_GPIO_NUM)
    #define Y8_GPIO_NUM CONFIG_Y8_GPIO_NUM
#endif
#if defined(CONFIG_Y9_GPIO_NUM)
    #define Y9_GPIO_NUM CONFIG_Y9_GPIO_NUM
#endif

#if defined(CONFIG_VSYNC_GPIO_NUM)
    #define VSYNC_GPIO_NUM CONFIG_VSYNC_GPIO_NUM
#endif
#if defined(CONFIG_HREF_GPIO_NUM)
    #define HREF_GPIO_NUM CONFIG_HREF_GPIO_NUM
#endif
#if defined(CONFIG_PCLK_GPIO_NUM)
    #define PCLK_GPIO_NUM CONFIG_PCLK_GPIO_NUM
#endif
#endif
