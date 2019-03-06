from websocketserver import A3EWebsocketServerProtocol
import argparse
import config

#https://stackoverflow.com/a/40624023








if __name__ == "__main__":
    print("Hey man!!!")

    parser = argparse.ArgumentParser()
    parser.add_argument('--private-host-ip',
                        type=str,
                        default=config.PRIVATE_HOST_IP,
                        help='The private ip of this machine in the local network')

    parser.add_argument('--public-host-ip',
                        type=str,
                        default=config.PUBLIC_HOST_IP,
                        help='The public ip of this machine')

    parser.add_argument('--broadcast-ip',
                        type=str,
                        default=config.BROADCAST_IP,
                        help='The broadcast ip of the local network for UDP Awareness')

    parser.add_argument('--broadcast-port',
                        type=int,
                        default=config.BROADCAST_PORT,
                        help='The broadcast port for UDP Awareness')

    parser.add_argument('--ws-port',
                        type=int,
                        default=config.WEBSOCKET_PORT,
                        help='The ws port to reach this Domain Manager')

    parser.add_argument('--couch-db-user',
                        type=str,
                        default=config.COUCH_DB_WHISK_ADMIN_USER,
                        help='The username of the CouchDB admin user on OpenWhisk')

    parser.add_argument('--couch-db-pass',
                        type=str,
                        default=config.COUCH_DB_WHISK_ADMIN_PASSWORD,
                        help='The password of the CouchDB admin user on OpenWhisk')

    parser.add_argument('--node-type',
                        type=str,
                        default=config.NODE_TYPE,
                        help='The node type of this installation')

    parser.add_argument('--wsk-path',
                        type=str,
                        default=config.WSK_PATH,
                        help='Path of the wsk command of the OpenWhisk installation to use')

    parser.add_argument('--flask',
                        type=bool,
                        default=True,
                        help='Whether to start Flask or not')

    parser.add_argument('--flask-port',
                        type=int,
                        default=config.FLASK_PORT,
                        help='The port used by FLASK REST API')

    parser.add_argument('--metrics-interval',
                        type=int,
                        default=config.METRICS_INTERVAL_SECONDS,
                        help='Metrics interval to get percentiles from db metrics')

    parser.add_argument('--remap-port',
                        type=bool,
                        default=False,
                        help='Remap ports')

    parsed, ignored = parser.parse_known_args()

    # https://stackoverflow.com/a/4435179
    if parsed.private_host_ip is not None:
        config.PRIVATE_HOST_IP = parsed.private_host_ip

    if parsed.public_host_ip is not None:
        config.PUBLIC_HOST_IP = parsed.public_host_ip

    if parsed.broadcast_ip is not None:
        config.BROADCAST_IP = parsed.broadcast_ip

    if parsed.broadcast_port is not None:
        config.BROADCAST_PORT = parsed.broadcast_port

    if parsed.ws_port is not None:
        config.WEBSOCKET_PORT = parsed.ws_port

    if parsed.couch_db_user is not None:
        config.COUCH_DB_WHISK_ADMIN_USER = parsed.couch_db_user

    if parsed.couch_db_pass is not None:
        config.COUCH_DB_WHISK_ADMIN_PASSWORD = parsed.couch_db_pass

    if parsed.node_type is not None:
        config.NODE_TYPE = parsed.node_type

    if parsed.wsk_path is not None:
        config.WSK_PATH = parsed.wsk_path

    if parsed.flask is not None:
        config.RUN_FLASK = parsed.flask

    if parsed.flask_port is not None:
        config.FLASK_PORT = parsed.flask_port

    if parsed.metrics_interval is not None:
        config.METRICS_INTERVAL_SECONDS = parsed.metrics_interval

    if parsed.remap_port is not None:
        config.REMAP_PORTS = parsed.remap_port

    websocketserver = A3EWebsocketServerProtocol()
    websocketserver.start()


















