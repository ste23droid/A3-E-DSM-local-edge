from websocketserver import A3EWebsocketServerProtocol
import argparse
import config
import time

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--private-host-ip',
                        type=str,
                        default=config.PRIVATE_HOST_IP,
                        help='The private ip of this machine in the local network')

    parser.add_argument('--public-host-ip',
                        type=str,
                        default=config.PUBLIC_HOST_IP,
                        help='The public ip of this machine')

    parsed, ignored = parser.parse_known_args()

    if parsed.private_host_ip is not None:
        config.PRIVATE_HOST_IP = parsed.private_host_ip

    if parsed.public_host_ip is not None:
        config.PUBLIC_HOST_IP = parsed.public_host_ip

    websocketserver = A3EWebsocketServerProtocol()
    websocketserver.start()
    time.sleep(config.DEFAULT_EXECUTION_TIME)

















