
DEFAULT_EXECUTION_TIME = 86400  # seconds
HEARTBEAT_INTERVAL = 15  # seconds
BROADCAST_PORT = 12345

#HOST_IP = "10.79.11.222"
#BROADCAST_IP = '10.79.11.255'

HOST_IP = "192.168.1.214"
BROADCAST_IP = '192.168.1.255'

COUCH_DB_PORT = 5984
#COUCH_DB_WHISK_DEFAULT_USER = "ste"
#COUCH_DB_WHISK_DEFAULT_PASSWORD = "ste"

# see docker-compose.yml
COUCH_DB_WHISK_DEFAULT_USER = "whisk_admin"
COUCH_DB_WHISK_DEFAULT_PASSWORD = "some_passw0rd"
COUCH_DB_HOST_IP = "127.0.0.1"
COUCH_DB_BASE = "http://{}:{}@{}:{}".format(COUCH_DB_WHISK_DEFAULT_USER,
                                            COUCH_DB_WHISK_DEFAULT_PASSWORD,
                                            COUCH_DB_HOST_IP,
                                            COUCH_DB_PORT)
DB_RUNTIMES_NAME = "runtimes"
DB_METRICS_NAME = "metrics"
DB_METRICS_DESIGN_DOC = "metrics_doc"
DB_METRICS_VIEW_NAME = "runtime_metrics"

FLASK_HOST_IP = HOST_IP
FLASK_PORT = 5050
FLASK_URL = "http://{}:{}".format(FLASK_HOST_IP, FLASK_PORT)
FLASK_IDENTIFICATION_URL = "{}/identification".format(FLASK_URL)
FLASK_MONITORING_URL = "{}/monitoring".format(FLASK_URL)

DEFAULT_RUNTIME_JSON = "{\"name\": \"ste23/whisk-python2action-alpine-opencv-numpy:prod\", \
                           \"language\": \"python\",  \
                           \"languageVersion\": \"2.7\", \
                           \"dependencies\": [ \
                               {\"lib\": \"numpy\",\
                                \"version\": \"1.15\"}, \
                               {\"lib\": \"opencv\",   \
                                \"version\": \"3.4.2\"} ]}"
APPLICATION_JSON_HEADER = {"Content-Type": "application/json"}

CONFIG_FILE_NAME = "a3e_config.json"
# use "wsk property get -i" to get this information
WHISK_NAMESPACE = "guest"
WHISK_API_HOST = HOST_IP
WHISK_API_VERSION = "v1"
# modify wsk path with the content returned by "which wsk" command
WSK_PATH = "/home/ubuntu/git/incubator-openwhisk-devtools/docker-compose/openwhisk-src/bin/wsk"
# WSK_PATH = "/Users/stefano/Desktop/incubator-openwhisk-devtools/docker-compose/openwhisk-src/bin/wsk"

REPOS_PATH = "./repositories"
WEBSOCKET_HOST = HOST_IP
WEBSOCKET_PORT = "12323"

# can be "local-edge" "mobile-edge" or "cloud"
NODE_TYPE = "cloud"
