from __future__ import print_function
import time
import requests
from awareness import Awareness
from acquisition import Acquisition
import config
from flask import Flask, request, jsonify

app = Flask(__name__)
awareness = None
acquisition = None


@app.route('/')
def entry():
    return 'A3E Domain Manager!'


@app.route('/identification', methods=['POST'])
def identification():
    content = request.json
    client_ip = request.remote_addr
    print("Received Identification Request from ip: " + client_ip)
    print("Received Identification json: " + str(content))
    response_json = acquisition.__parse_request__(content)
    return jsonify(response_json)


@app.route('/monitoring', methods=['POST'])
def monitoring():
    return 'Hello World!'


@app.route('/invoke', methods=['POST'])
def invoke():
    content = request.json


def runtimes_ready():
    runtimes_url = config.COUCH_DB_BASE + "/" + config.DB_RUNTIMES_NAME
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
            add_default_runtime = requests.post(runtimes_url,
                                                data=config.DEFAULT_RUNTIME_JSON,
                                                headers=config.APPLICATION_JSON_HEADER)
            print(add_default_runtime.json())
            if add_default_runtime.status_code == 201:
                print("Created A3E default runtime")
                return True
            else:
                print(add_default_runtime.json()["reason"])
    else:
        print(response.json()["reason"])

    return False


def get_runtimes():
    runtimes = []
    get_list_runtimes = requests.get(config.COUCH_DB_BASE + "/" + config.DB_RUNTIMES_NAME + "/_all_docs")
    if get_list_runtimes.status_code == 200:
        list_runtimes = get_list_runtimes.json()
        # print(type(list_runtimes))
        for elem in list_runtimes["rows"]:
            get_runtime = requests.get(config.COUCH_DB_BASE + "/" + config.DB_RUNTIMES_NAME + "/" + elem["id"])
            if get_runtime.status_code == 200:
                runtimes.append(get_runtime.json())
    else:
        print("Error, unable to get any runtime!!!")
    assert len(runtimes) > 0
    return runtimes


if __name__ == "__main__":

    if runtimes_ready():
         runtimes = get_runtimes()
         #awareness = Awareness()
         #awareness.start()
         acquisition = Acquisition(runtimes)
         acquisition.__acquire__("https://github.com/ste23droid/A3E-OpenWhisk-face-detection/")
         #app.run(host=config.FLASK_HOST_IP, port=config.FLASK_PORT, debug=True)
         time.sleep(config.DEFAULT_EXECUTION_TIME)
        # awareness.stop()
        # acquisition.stop()
    else:
        print("Runtimes not ready, aborting...")
