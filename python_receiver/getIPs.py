import socket,time,psutil,ipaddress


def get_broadcast_address():
    net_if_addrs = psutil.net_if_addrs()
    
    for interface_name, addresses in net_if_addrs.items():
        if interface_name == "lo":
            continue  # Skip localhost
        
        for addr in addresses:
            if addr.family == 2: #AF_INET
                ip = addr.address
                netmask = addr.netmask
                network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
                return str(network.broadcast_address), ip, interface_name

    raise ValueError("No suitable network interface found")

responses = None
def getIPs(broadcast_addr,timeout=1):
    global responses
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Bind the socket to a specific address and port
    sock.bind(("0.0.0.0", 55556))

    # Broadcast the 0x55 datagram
    sock.sendto(b'\x55', (broadcast_addr, 55555))
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