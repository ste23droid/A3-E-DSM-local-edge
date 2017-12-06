import time
#A3-E-DSM Classes
from awareness import Awareness
from acquisition import Acquisition

DEFAULT_EXECUTION_TIME = 10 #seconds
HEARBEAT_INTERVAL = 5 #seconds
BROADCAST_IP = '10.0.1.255'
BROADCAST_PORT = 12340
UNICAST_PORT = 12341

def main():
    awareness = Awareness(BROADCAST_IP, BROADCAST_PORT, HEARBEAT_INTERVAL)
    awareness.start()
    acquisition = Acquisition(UNICAST_PORT)
    acquisition.start()
    time.sleep(DEFAULT_EXECUTION_TIME)
    awareness.stop()
    acquisition.stop()    

if __name__ == "__main__":
    main()
