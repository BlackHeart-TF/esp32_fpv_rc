

void threadLoop(){
    // while (1)
    // {
    //     struct netbuf *rxbuf;
    //     err = netconn_recv(camera_conn, &rxbuf);
    //     if (err == ERR_OK)
    //     {
    //         uint8_t *data;
    //         u16_t len;
    //         netbuf_data(rxbuf, (void **)&data, &len);
    //         if (len)
    //         {
    //             ESP_LOGI(TAG, "netconn_recv %d", len);
    //             if (data[0] == 0x55)
    //             {
    //                 peer_addr = *netbuf_fromaddr(rxbuf);
    //                 ESP_LOGI(TAG, "peer %lx", peer_addr.u_addr.ip4.addr);

    //                 ESP_LOGI(TAG, "Trigged!");
    //                 netbuf_delete(rxbuf);
    //                 break;
    //             }
    //         }
    //         netbuf_delete(rxbuf);
    //     }
    //     vTaskDelay(pdMS_TO_TICKS(10));
    // }
}