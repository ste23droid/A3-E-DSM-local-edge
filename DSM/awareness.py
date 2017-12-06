import threading
import time
import os
from socket import *

class Awareness:

    HELLO_MSG = 'HI'
    BROADCAST_IP = '255.255.255.255'
    BROADCAST_PORT = '12345'
    INTERVAL = 5

    def __init__(self, broadcast_ip, broadcast_port, interval):
        self.BROADCAST_IP = broadcast_ip
        self.BROADCAST_PORT = broadcast_port
        self.INTERVAL = interval
        self.broadcast_socket=socket(AF_INET, SOCK_DGRAM)
        self.broadcast_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.broadcast_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

    def start(self):
        print 'Starting Domain Awareness'
        self.hrtb_t = threading.Thread(target=self.__heartbeat)
        self.hrtb_t.start()

    def stop(self):
        print 'Stopping Domain Awareness'
        self.hrtb_t.do_run = False
        self.hrtb_t.join()

    def __heartbeat(self):
        print 'Domain\'s Advertisement Broadcast Started'
        t = threading.currentThread()
        while getattr(t, "do_run", True):
            print 'Sending ' + self.HELLO_MSG
            self.broadcast_socket.sendto(self.HELLO_MSG,(self.BROADCAST_IP, self.BROADCAST_PORT))
            time.sleep(self.INTERVAL)
