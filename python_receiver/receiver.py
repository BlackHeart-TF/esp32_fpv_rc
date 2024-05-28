import cv2
import numpy as np
import socket
import select
import threading
import queue
import time
import traceback

class udp_transitter():
    def __init__(self,target_addr,listen_addr="0.0.0.0"):
        self.frame_q = queue.Queue()
        self.running = False
        self.Address = target_addr
        self.ListenAddress = listen_addr

    def Begin(self):
        self.running = True
        thread = threading.Thread(target=self.udp_recv)
        thread.start()

    def udp_recv(self):

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1)
        sock.bind((self.ListenAddress, 55556))

        print('Start Streaming...')

        chunks = b''
        while self.running:
            try:
                msg, address = sock.recvfrom(2**16)
            except Exception as e:
                # print('sock.recvfrom',e)
                sock.sendto(b'\x55', (self.Address, 55555))
                continue
            soi = msg.find(b'\xff\xd8\xff')
            eoi = msg.rfind(b'\xff\xd9')
            print(time.perf_counter(), len(msg), soi, eoi, msg[:2], msg[-2:])
            if soi >= 0:
                if chunks.startswith(b'\xff\xd8\xff'):
                    if eoi >= 0:
                        chunks += msg[:eoi+2]
                        print(time.perf_counter(), "Complete picture")
                        eoi = -1
                    else:
                        chunks += msg[:soi]
                        print(time.perf_counter(), "Incomplete picture")
                    try:
                        self.frame_q.put(chunks, timeout=1)
                    except Exception as e:
                        print(e)
                chunks = msg[soi:]
            else:
                chunks += msg
            if eoi >= 0:
                eob = len(chunks) - len(msg) + eoi + 2
                if chunks.startswith(b'\xff\xd8\xff'):
                    byte_frame = chunks[:eob]
                    print(time.perf_counter(), "Complete picture")
                    try:
                        self.frame_q.put(byte_frame, timeout=1)
                    except Exception as e:
                        print(e)
                else:
                    print(time.perf_counter(), "Invalid picture")
                chunks = chunks[eob:]
        sock.close()
        print('Stop Streaming')

def main(args):
    udp = udp_transitter(args.target,args.listen)
    thread = threading.Thread(target=udp.udp_recv)
    thread.start()

    winname = 'frame'
    if args.fullscreen:
        cv2.namedWindow(winname, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(winname, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    writer = None
    img = None
    next_write = 0
    while(True):

        try:
            if args.write:
                if not udp.frame_q.empty():
                    img = None
            else:
                img = None
            if img is None:
                while True:
                    byte_frame = udp.frame_q.get(block=True, timeout=1)
                    if udp.frame_q.empty() or args.grab_all:
                        break
                    print(time.perf_counter(), 'Skip picture')
                print(time.perf_counter(), 'Decode picture')
                img = cv2.imdecode(np.frombuffer(byte_frame, dtype=np.uint8), 1)

                # rotate
                # img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
                # img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)

                # resize
                # width = 800
                # h, w = img.shape[:2]
                # if w < width:
                #     print(time.perf_counter(), 'Resize picture')
                #     height = round(h * (width / w))
                #     img = cv2.resize(img, dsize=(width, height))

            if args.write:
                if writer is None:
                    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
                    writer = cv2.VideoWriter(args.write, fourcc, args.fps, (img.shape[1], img.shape[0]))
                if time.perf_counter() > next_write:
                    next_write += 1/args.fps
                    print(time.perf_counter(), 'Write picture')
                    writer.write(img)

            print(time.perf_counter(), 'Show picture')
            cv2.imshow(winname,img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except queue.Empty as e:
            pass
        except Exception as e:
            print(traceback.format_exc())
        except KeyboardInterrupt as e:
            print('KeyboardInterrupt')
            break

    if writer:
        writer.release()
    print('Waiting for recv thread to end')
    udp.running = False
    thread.join()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("listen", type=str)
    parser.add_argument("target", type=str)
    parser.add_argument("--fullscreen", action='store_true')
    parser.add_argument("--write", type=str)
    parser.add_argument("--fps", type=int, default=60)
    parser.add_argument("--grab-all", action='store_true', default=False)
    args = parser.parse_args()
    main(args)
