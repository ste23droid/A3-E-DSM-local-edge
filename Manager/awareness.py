import threading
import time
from socket import *
import config


class Awareness:

    def __init__(self):
        self.broadcast_socket = socket(AF_INET, SOCK_DGRAM)
        self.broadcast_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.broadcast_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self.awthread = threading.Thread(target=self.__heartbeat)

    def start(self):
        print('Starting Domain Awareness')
        # thread will die when the main thread dies
        self.awthread.daemon = True
        self.awthread.start()

    def stop(self):
        print('Stopping Domain Awareness')
        self.awthread.do_run = False
        self.broadcast_socket.close()
        self.awthread.join()

    def __heartbeat(self):
        print('Domain\'s Advertisement Broadcast Started')
        t = threading.currentThread()
        while getattr(t, "do_run", True):
            print('Sending Awareness Message')
            self.broadcast_socket.sendto(config.FLASK_IDENTIFICATION_URL.encode(), (config.BROADCAST_IP, config.BROADCAST_PORT))
            time.sleep(config.HEARTBEAT_INTERVAL)
