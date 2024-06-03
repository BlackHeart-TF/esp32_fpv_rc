#include "lwip/sockets.h"
#include "lwip/inet.h"

#define UDP_PORT CONFIG_ESP_UDP_LOG_PORT
#define LOG_SERVER_IP CONFIG_ESP_UDP_LOG_IP // Replace with your server's IP address

int udp_socket;
struct sockaddr_in server_addr;

void udp_logging_init() {
    udp_socket = socket(AF_INET, SOCK_DGRAM, 0);
    if (udp_socket < 0) {
        printf("Failed to create UDP socket\n");
        return;
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(UDP_PORT);
    server_addr.sin_addr.s_addr = inet_addr(LOG_SERVER_IP);
}

int udp_log_vprintf(const char *fmt, va_list args) {
    char log_buffer[256];
    int len = vsnprintf(log_buffer, sizeof(log_buffer), fmt, args);
    if (len > 0) {
        sendto(udp_socket, log_buffer, len, 0, (struct sockaddr *)&server_addr, sizeof(server_addr));
    }
    return len;
}

void udp_logging_close() {
    close(udp_socket);
}
