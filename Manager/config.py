
DEFAULT_EXECUTION_TIME = 86400  # seconds
HEARTBEAT_INTERVAL = 15  # seconds
BROADCAST_PORT = 12345

#PRIVATE_HOST_IP = "10.79.11.222"
#BROADCAST_IP = '10.79.11.255'

PRIVATE_HOST_IP = "192.168.1.214"
BROADCAST_IP = '192.168.1.255'

PUBLIC_HOST_IP = PRIVATE_HOST_IP

COUCH_DB_PORT = 5984
#COUCH_DB_WHISK_ADMIN_USER = "ste"
#COUCH_DB_WHISK_ADMIN_PASSWORD = "ste"

# see docker-compose.yml
COUCH_DB_WHISK_ADMIN_USER = "whisk_admin"
COUCH_DB_WHISK_ADMIN_PASSWORD = "some_passw0rd"
COUCH_DB_HOST_IP = "127.0.0.1"
COUCH_DB_BASE = "http://{}:{}@{}:{}".format(COUCH_DB_WHISK_ADMIN_USER,
                                            COUCH_DB_WHISK_ADMIN_PASSWORD,
                                            COUCH_DB_HOST_IP,
                                            COUCH_DB_PORT)
# db keeping all known runtimes
DB_RUNTIMES_NAME = "runtimes"
DB_METRICS_NAME = "metrics"

# maps an action (function) name to its git repository url
DB_MAPPINGS_NAME = "mappings"
DB_METRICS_DESIGN_DOC = "metrics_doc"
DB_METRICS_VIEW_NAME = "runtime_metrics"

FLASK_PORT = 5050

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
WHISK_API_VERSION = "v1"
# modify wsk path with the content returned by "which wsk" command
WSK_PATH = "/home/ubuntu/git/incubator-openwhisk-devtools/docker-compose/openwhisk-src/bin/wsk"
#WSK_PATH = "/Users/stefano/Desktop/incubator-openwhisk-devtools/docker-compose/openwhisk-src/bin/wsk"

REPOS_PATH = "./repositories"
WEBSOCKET_PORT = "12323"

METRICS_INTERVAL_SECONDS = 600 # 10 minutes

# can be "local-edge" "mobile-edge" or "cloud"
NODE_TYPE = "cloud"
#NODE_TYPE = "local-edge"

# curl -X POST -u 23bc46b1-71f6-4ed5-8c54-816aa4f8c502:123zO3xZCLrMN6v2BKK1dXYFpXlPkccOFqm12CdAsMgRU4VrNZ9lyGVCGuMDGIwP http://172.31.11.231:8888/api/v1/namespaces/guest/actions/helloWorld?blocking=true&result=true

RUN_FLASK = True
REMAP_PORTS = False