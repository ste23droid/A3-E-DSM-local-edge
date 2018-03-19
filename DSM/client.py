import threading
import time
import os
from socket import *

#Aclien3-E-DSM Classes
from awareness import Awareness
from acquisition import Acquisition

class Client:

    DEFAULT_EXECUTION_TIME = 1000 #seconds
    HEARBEAT_INTERVAL = 5 #seconds
    LOCAL_IP = '10.0.0.4'
    BROADCAST_IP = ''

    def __init__(self):
        self.unicast_socket=socket(AF_INET, SOCK_DGRAM)
        #self.unicast_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.unicast_socket.bind((self.LOCAL_IP, Acquisition.UNICAST_PORT))

        self.broadcast_socket=socket(AF_INET, SOCK_DGRAM)
        #self.broadcast_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        #self.broadcast_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self.broadcast_socket.bind((self.BROADCAST_IP, int(Awareness.BROADCAST_PORT)))

    def start(self):
        print 'Starting Client Emulator'

        self.hrtb_t = threading.Thread(target=self.__awareness)
        self.hrtb_t.start()

    def stop(self):
        print 'Stopping Client Emulator'
        self.hrtb_t.do_run = False
        self.hrtb_t.join()

    def __awareness(self):
        print 'Client Broadcast Receiver Started'
        t = threading.currentThread()
        while getattr(t, "do_run", True):
            data, rcvr = self.broadcast_socket.recvfrom(1024)
            print "Client Receiver: message received"
            if data == Awareness.HELLO_MSG:
                self.identification(rcvr[0])
            elif data == Acquisition.SERVICE_OK_MSG:
                self.confirmation(data)
            else:
                 continue

    #comment out after client is implemented
    server_discovered = False
    def identification(self, server_ip):
        print 'HI received'
        if not self.server_discovered:
            print 'Client Sending Identification ', server_ip
            FUNCTION_URL = 'https://github.com/mgarriga/example-lambda;example-lambda'
            self.unicast_socket.sendto(FUNCTION_URL,(server_ip, int(Acquisition.UNICAST_PORT)))
            self.server_discovered = True

    def confirmation(self, service_name):
        print 'Service confirmation for ' + service_name + ' received'


def main():
    client = Client()
    client.start()

if __name__ == "__main__":
    main()
