import socket
import threading
import queue
import time

class UDP():
    frame_queues = {}
    listening = False
    sendsock = None

    @classmethod
    def Begin(cls,ListenAddress="0.0.0.0"):
        if not cls.listening:
            cls.listening = True
            thread = threading.Thread(target=cls.udp_recv,args=[ListenAddress])
            thread.start()

    @classmethod
    def udp_recv(cls,ListenAddress="0.0.0.0"):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1)
        sock.bind((ListenAddress, 55556))

        chunks = b''
        while cls.listening:
            try:
                data, addr = sock.recvfrom(2**16)
                addr = addr[0]
            except socket.timeout:
                continue
            if addr not in cls.frame_queues:
                continue # if we arent registered for them, dont waste time on it
            soi = data.find(b'\xff\xd8\xff')
            eoi = data.rfind(b'\xff\xd9')
            #print(time.perf_counter(), len(data), soi, eoi, data[:2], data[-2:])
            if soi >= 0:
                if chunks.startswith(b'\xff\xd8\xff'):
                    if eoi >= 0:
                        chunks += data[:eoi+2]
                        #print(time.perf_counter(), "Complete picture")
                        eoi = -1
                    else:
                        chunks += data[:soi]
                        #print(time.perf_counter(), "Incomplete picture")
                    try:
                        cls.frame_queues[addr].put(chunks, timeout=1)
                        #self.frame_q.put(chunks, timeout=1)
                    except Exception as e:
                        print(e)
                chunks = data[soi:]
            else:
                chunks += data
            if eoi >= 0:
                eob = len(chunks) - len(data) + eoi + 2
                if chunks.startswith(b'\xff\xd8\xff'):
                    byte_frame = chunks[:eob]
                    #print(time.perf_counter(), "Complete picture")
                    try:
                        cls.frame_queues[addr].put(byte_frame, timeout=1)
                        #self.frame_q.put(byte_frame, timeout=1)
                    except Exception as e:
                        print(e)
                else:
                    print(time.perf_counter(), "Invalid picture")
                chunks = chunks[eob:]
        sock.close()
        print('Stop Streaming')
            
            

    def __init__(self, target_addr):
        self.target_addr = target_addr
        self.frame_queue = self.get_frame_queue()

    def __del__(self):
        self.EndStream()

    def get_frame_queue(self):
        if self.target_addr not in UDP.frame_queues:
            UDP.frame_queues[self.target_addr] = queue.Queue()
        return UDP.frame_queues[self.target_addr]

    def BeginStream(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(b'\x55', (self.target_addr, 55555))

    def SendCommand(self,bytes):
        if not UDP.sendsock:
            UDP.sendsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        UDP.sendsock.sendto(bytes, (self.target_addr, 55555))

    def EndStream(self):
        if self.target_addr in UDP.frame_queues:
            UDP.frame_queues.pop(self.target_addr)


if __name__ == "__main__":
    # Start the global listener
    UDP.Begin()

    # Create instances of UDP and begin streaming
    udp = UDP("192.168.2.206")
    udp.BeginStream()

    # udp2 = UDP("target_address_2")
    # udp2.BeginStream()

