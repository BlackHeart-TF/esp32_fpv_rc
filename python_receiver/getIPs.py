import socket,time


responses = None
def getIPs(timeout=1):
    global responses
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Bind the socket to a specific address and port
    sock.bind(("0.0.0.0", 55556))

    # Broadcast the 0x55 datagram
    sock.sendto(b'\x55', ("192.168.0.255", 55555))
    sock.settimeout(2)
    # Listen for responses from multiple devices
    responses = set()
    starttime = time.time()
    while time.time() - starttime < timeout:
        try:
            data, addr = sock.recvfrom(1024)
            if addr[0] not in responses:
                print(f"Received ping from {addr}")
                responses.add(addr[0])
                # Log the IP address here
            #else:
                #print(f"Ignoring further packets from {addr}")
        except TimeoutError:
            pass
        except KeyboardInterrupt:
            break

    

    # Close the socket
    sock.close()
    return responses

if __name__ == "__main__":
    responses = getIPs()
    # Print all the IP addresses that responded
    print("Devices that responded:")
    for ip in responses:
        print(ip)