
DEFAULT_EXECUTION_TIME = 86400  # seconds
HEARTBEAT_INTERVAL = 15  # seconds
# BROADCAST_IP = '10.79.11.255'
BROADCAST_IP = '192.168.1.255'
BROADCAST_PORT = 12345

COUCH_DB_PORT = 5984
COUCH_DB_WHISK_DEFAULT_USER = "ste"
COUCH_DB_WHISK_DEFAULT_PASSWORD = "ste"
COUCH_DB_HOST_IP = "127.0.0.1"

FLASK_HOST_IP = "192.168.1.214"
FLASK_PORT = 5050
FLASK_URL = "http://" + FLASK_HOST_IP + ":" + str(FLASK_PORT)
FLASK_IDENTIFICATION_URL = FLASK_URL + "/identification"
FLASK_MONITORING_URL = FLASK_URL + "/monitoring"

DB_RUNTIMES_NAME = "runtimes"
DB_METRICS_BASE_NAME = "metrics"

COUCH_DB_BASE = "http://{}:{}@".format(COUCH_DB_WHISK_DEFAULT_USER, COUCH_DB_WHISK_DEFAULT_PASSWORD) \
                 + str(COUCH_DB_HOST_IP) + ":" + str(COUCH_DB_PORT)
DEFAULT_RUNTIME_JSON = "{\"name\": \"ste23/whisk-python2action-alpine-opencv-numpy-pillow:prod\", \
                           \"language\": \"python\",  \
                           \"languageVersion\": \"2.7\", \
                           \"dependencies\": [ \
                               {\"lib\": \"numpy\",\
                                \"version\": \"1.15\"}, \
                               {\"lib\": \"pillow\", \
                                \"version\": \"5.3.0\"}, \
                               {\"lib\": \"opencv\",   \
                                \"version\": \"3.4.2\"} ]}"
APPLICATION_JSON_HEADER = {"Content-Type": "application/json"}
CONFIG_FILE_NAME = "a3e_config.json"
# use wsk property get -i to get this information
WHISK_NAMESPACE = "guest"
WHISK_API_HOST = "192.168.1.214"
WHISK_API_VERSION = "v1"
# whick wsk
WSK_PATH = "/Users/stefano/Desktop/incubator-openwhisk-devtools/docker-compose/openwhisk-src/bin/wsk"

REPOS_PATH = "./repositories"
WEBSOCKET_ENDPOINT = "wss://whisknamespace/"

