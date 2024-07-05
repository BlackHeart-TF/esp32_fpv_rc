import socket

def main():
    # Define the IP and port to listen on
    UDP_IP = "0.0.0.0"
    UDP_PORT = 55557

    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Bind the socket to the address and port
    sock.bind((UDP_IP, UDP_PORT))
    
    print(f"Listening on UDP port {UDP_PORT}")

    try:
        while True:
            # Receive data from the socket
            data, addr = sock.recvfrom(1024)  # Buffer size is 1024 bytes
            print(f"Recv {addr}: {data.decode('utf-8')}")
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        # Close the socket
        sock.close()

if __name__ == "__main__":
    main()
