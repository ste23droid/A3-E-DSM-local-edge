import threading
import time
from socket import *


class Awareness:

    DOMAIN_URL = "http://github.com/mainUrl"
    BROADCAST_IP = '255.255.255.255'
    BROADCAST_PORT = '12345'
    INTERVAL = 60  # seconds

    def __init__(self, broadcast_ip, broadcast_port, interval):
        self.BROADCAST_IP = broadcast_ip
        self.BROADCAST_PORT = broadcast_port
        self.INTERVAL = interval
        self.broadcast_socket = socket(AF_INET, SOCK_DGRAM)
        self.broadcast_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.broadcast_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

    def start(self):
        print 'Starting Domain Awareness'
        self.hrtb_t = threading.Thread(target=self.__heartbeat)
        self.hrtb_t.daemon = True
        self.hrtb_t.start()

    def stop(self):
        print 'Stopping Domain Awareness'
        self.hrtb_t.do_run = False
        self.broadcast_socket.close()
        self.hrtb_t.join()

    def __heartbeat(self):
        print 'Domain\'s Advertisement Broadcast Started'
        t = threading.currentThread()
        while getattr(t, "do_run", True):
            print 'Sending Awareness Message'
            self.broadcast_socket.sendto(self.DOMAIN_URL, (self.BROADCAST_IP, self.BROADCAST_PORT))
            time.sleep(self.INTERVAL)
