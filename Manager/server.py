from __future__ import print_function
import time
import requests
from awareness import Awareness
from acquisition import Acquisition
import json
from flask import Flask, request, jsonify
import logging

DEFAULT_EXECUTION_TIME = 86400  # seconds
HEARTBEAT_INTERVAL = 10  # seconds
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
IDENTIFICATION_URL = FLASK_URL + "/identification"
MONITORING_URL = FLASK_URL + "/monitoring"

DB_RUNTIMES_NAME = "runtimes"
COUCH_DB_BASE = "http://{}:{}@".format(COUCH_DB_WHISK_DEFAULT_USER, COUCH_DB_WHISK_DEFAULT_PASSWORD) \
                + str(COUCH_DB_HOST_IP) + ":" + str(COUCH_DB_PORT)
DEFAULT_RUNTIME_JSON = "{\"name\": \"ste23/whisk-python2action-alpine-opencv-numpy-pillow:ubuntumac\", \
               \"language\": \"python\",  \
               \"languageVersion\": \"2.7\", \
               \"dependencies\": [ \
                   {\"lib\": \"numpy\",\
                    \"version\": \"1.15\"}, \
                   {\"lib\": \"pillow\", \
                    \"version\": \"5.3.0\"}, \
                   {\"lib\": \"opencv\",   \
                    \"version\": \"3.4.2\"} ]}"
DEFAULT_RUNTIME_URL = None
APPLICATION_JSON_HEADER = {"Content-Type": "application/json"}

app = Flask(__name__)
awareness = None
acquisition = None


@app.route('/')
def entry():
    return 'Entry Point!'


@app.route('/identification', methods=['POST'])
def identification():
    content = request.json
    client_ip = request.remote_addr
    print("Received request by ip: " + client_ip)
    print("Received json: " + str(content))
    response_json = acquisition.__parse_request__(content)
    return jsonify(response_json)


@app.route('/monitoring')
def monitoring():
    return 'Hello World!'


def __runtimes_ready():
    runtimes_url = COUCH_DB_BASE + "/" + DB_RUNTIMES_NAME
    response = requests.request("GET", runtimes_url)
    if response.status_code == 200:
        body = response.json()
        if body["doc_count"] >= 1:
            print("Runtimes found!")
            return True

    elif response.status_code == 404:
        # create a db
        print(response.json()["reason"])
        print("Creating A3E runtimes database")
        response = requests.put(runtimes_url)
        if response.status_code == 201:
            print("Created A3E runtimes database")
            print("Creating A3E default runtime")
            add_default_runtime = requests.post(runtimes_url, data=DEFAULT_RUNTIME_JSON, headers=APPLICATION_JSON_HEADER)
            print(add_default_runtime.json())
            if add_default_runtime.status_code == 201:
                print("Created A3E default runtime")
                DEFAULT_RUNTIME_URL = COUCH_DB_BASE + "/" + DB_RUNTIMES_NAME + "/" + add_default_runtime.json()["id"]
                print("Default runtime url - {}".format(DEFAULT_RUNTIME_URL))
                return True
            else:
                print(add_default_runtime.json()["reason"])
    else:
        print(response.json()["reason"])

    return False


if __name__ == "__main__":

    if __runtimes_ready():
        awareness = Awareness(BROADCAST_IP, BROADCAST_PORT, HEARTBEAT_INTERVAL, IDENTIFICATION_URL)
        awareness.start()
        acquisition = Acquisition()
        app.run(host=FLASK_HOST_IP, port=FLASK_PORT, debug=True)
        time.sleep(DEFAULT_EXECUTION_TIME)
        # awareness.stop()
        # acquisition.stop()
    else:
        print("Runtimes not ready, aborting...")
