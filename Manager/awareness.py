from __future__ import print_function
import threading
import time
import sys
from socket import *


class Awareness:

    def __init__(self, broadcast_ip, broadcast_port, interval, identification_url):
        self.BROADCAST_IP = broadcast_ip
        self.BROADCAST_PORT = broadcast_port
        self.INTERVAL = interval
        self.DOMAIN_IDENTIFICATION_URL = identification_url
        self.broadcast_socket = socket(AF_INET, SOCK_DGRAM)
        self.broadcast_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.broadcast_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

    def start(self):
        print('Starting Domain Awareness')
        self.hrtb_t = threading.Thread(target=self.__heartbeat)
        self.hrtb_t.daemon = True
        self.hrtb_t.start()

    def stop(self):
        print('Stopping Domain Awareness')
        self.hrtb_t.do_run = False
        self.broadcast_socket.close()
        self.hrtb_t.join()

    def __heartbeat(self):
        print('Domain\'s Advertisement Broadcast Started')
        t = threading.currentThread()
        while getattr(t, "do_run", True):
            print('Sending Awareness Message')
            self.broadcast_socket.sendto(self.DOMAIN_IDENTIFICATION_URL, (self.BROADCAST_IP, self.BROADCAST_PORT))
            time.sleep(self.INTERVAL)
