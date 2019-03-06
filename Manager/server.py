import time as t
import argparse
import requests
import json
import numpy
import re
from awareness import Awareness
from acquisition import Acquisition
from allocation import Allocation
from loader_simulator import LoaderSimulator
from websocketserver import A3EWebsocketServerProtocol
import config
from subprocess import check_output
from flask import Flask, request, Response
from multiprocessing import Process
import sys
import subprocess
import os

create = [sys.executable, 'run_ws_server.py']

app = Flask(__name__)
awareness = None
allocation = None
acquisition = None
loadsimulator = None
requests.packages.urllib3.disable_warnings()
start_loader = False

def start_ws_server():
    websocketserver = A3EWebsocketServerProtocol()
    websocketserver.start()

def start_loader_process():
    loadsimulator = LoaderSimulator()
    loadsimulator.start()

@app.route('/')
def entry():
    return 'A3E Domain Manager!'


@app.route('/identification', methods=['POST'])
def identification():
    content = request.json
    # client_ip = request.remote_addr
    # print("Received Identification Request from ip: " + client_ip)
    # print("Received Identification json: " + str(content))
    response_json = acquisition.__parse_request__(content)

    # START LOADER TO TEST THE DOMAIN
    global start_loader
    global loadsimulator
    if not start_loader:
        process_start_load_simulator = Process(target=start_loader_process)
        process_start_load_simulator.start()
        start_loader = True

    # print(response_json)
    return Response(json.dumps(response_json), mimetype='application/json')


@app.route('/monitoring', methods=['POST'])
def monitoring():
    content = request.json
    # get list of installed actions from openwhisk
    if not config.REMAP_PORTS:
        raw_actions_list = check_output("{} action list -i".format(config.WSK_PATH), shell=True).splitlines()[1:]
    else:
        raw_actions_list = check_output("{} --apihost http://localhost:8888 action list -i".format(config.WSK_PATH), shell=True).splitlines()[1:]
    # print(raw_actions_list)

    parsed_action_list = []
    for raw_action_name in raw_actions_list:
        # /guest/ste23droid/faceDetection                                        private blackbox
        wsk_name = (raw_action_name.split())[0]
        # e.g /guest/ste23droid/faceDetection -> but in the mappings actions are saved with ste23droid/faceDetection
        wsk_name_splitted = wsk_name[7:]
        # print(f"Whisk name action splitted: {wsk_name_splitted}")
        parsed_action_list.append(wsk_name_splitted.decode("utf-8"))
    # print(parsed_action_list)

    get_all_mappings_request = requests.get("{}/{}/_all_docs?include_docs=true".format(config.COUCH_DB_BASE, config.DB_MAPPINGS_NAME),
                                             verify=False,
                                             headers=config.APPLICATION_JSON_HEADER)

    response_items = []
    if get_all_mappings_request.status_code == 200:
        mappings = get_all_mappings_request.json()["rows"]
        #print(get_all_mappings_request.json())

        for repo in content["functions"]:
            action_name = None
            for mapping in mappings:
               if mapping["doc"]["repo"] == repo:
                  action_name = mapping["doc"]["actionName"]
                  break

            status = "unavailable"
            exec_time_percentile = None

            # is possible that we have never seen the repo
            if action_name is not None:
                # in any case (function installed or not) we should try to retrieve metrics to update them on the client
                # OLD: exec_time = get_metrics_avg_std(action_name)
                exec_time_percentile = get_exec_time_percentile(action_name)
                if action_name in parsed_action_list:
                    status = "available"
                    #print("Action {} available".format(action_name))

            # there are actual metrics to send to the client
            # the percentile is returned as String (not double) so Gson on client side can know if it's there or not, since String in Java is an object
            if exec_time_percentile is not None:
                response_items.append({"repo": repo,
                                       "status": status,
                                       "execTime": str(exec_time_percentile)})
            else:
                response_items.append({"repo": repo,
                                       "status": status})

    json_response = {"monitorings": response_items}
    return Response(json.dumps(json_response), mimetype='application/json')


def get_exec_time_percentile(action_name):
    database_name = re.sub("/", "-", action_name).lower()
    get_all_function_metrics = requests.get("{}/{}-{}/_all_docs?include_docs=true".format(
                                                                config.COUCH_DB_BASE,
                                                                config.DB_METRICS_NAME,
                                                                database_name),
                                             verify=False,
                                             headers=config.APPLICATION_JSON_HEADER)
    #print(f"{get_all_function_metrics.json()}")

    if get_all_function_metrics.status_code == 200:
        metrics = get_all_function_metrics.json()["rows"]
        #print(metrics)

        # normal strategy
        metrics_exec_time_interval = []
        # fallback strategy
        metrics_exec_time_all = []

        if len(metrics) != 0:
            for metric in metrics:
                metric_creation_time = metric["doc"]["requestTime"]
                exec_time = metric["doc"]["execTimeSec"]

                # only recent metrics
                if (t.time() - metric_creation_time) < config.METRICS_INTERVAL_SECONDS:
                    metrics_exec_time_interval.append(exec_time)

                # fallback strategy
                metrics_exec_time_all.append(exec_time)

            # compute percentile
            if len(metrics_exec_time_interval) != 0:
                percentile_95 = numpy.percentile(metrics_exec_time_interval, 95)
            else:
                percentile_95 = numpy.percentile(metrics_exec_time_all, 95)
            return percentile_95
        else:
            print(f"No execution time metrics for action {action_name} at the moment")

    return None


def runtimes_ready():
    runtimes_db_url = config.COUCH_DB_BASE + "/" + config.DB_RUNTIMES_NAME
    get_runtimes_db = requests.request("GET", runtimes_db_url)

    if get_runtimes_db.status_code == 200:
        body = get_runtimes_db.json()
        if body["doc_count"] >= 1:
            print("Runtimes found!")
            return True
        else:
            print("Runtimes db existing but no runtimes found in it!!!")

    elif get_runtimes_db.status_code == 404:
        print(get_runtimes_db.json()["reason"])
        print("Creating A3E runtimes database")
        create_runtimes_db = requests.put(runtimes_db_url)
        if create_runtimes_db.status_code == 201:
            print("Created A3E runtimes database")
            print("Adding A3E default runtime")
            add_default_runtime = requests.post(runtimes_db_url,
                                                data=config.DEFAULT_RUNTIME_JSON,
                                                headers=config.APPLICATION_JSON_HEADER)
            # print(add_default_runtime.json())
            if add_default_runtime.status_code == 201:
                print("Added A3E default runtime")
                return True
            else:
                print("Error adding default runtime to runtimes db, " + add_default_runtime.json()["reason"])
        else:
            print("Error creating runtimes database, " + create_runtimes_db.json()["reason"])
    else:
        print(get_runtimes_db.json()["reason"])

    return False


def is_mappings_db_ready():
    mappings_db_url = config.COUCH_DB_BASE + "/" + config.DB_MAPPINGS_NAME
    get_mappings_db = requests.get(mappings_db_url)

    if get_mappings_db.status_code == 200:
        print("Mappings database found!")
        return True

    elif get_mappings_db.status_code == 404:
        print("Mappings database not found, creating it...")
        create_mappings_db = requests.put(mappings_db_url)

        if create_mappings_db.status_code == 201:
            print("Mappings database created")
            return True

        else:
            print(create_mappings_db.json()["reason"])
    else:
        print(get_mappings_db.json()["reason"])

    return False


if __name__ == "__main__":

    # TODO: ADD LOOP ON DOMAIN MANAGER TO CHECK FOR UNUSED ACTIONS: after a timeout we need to uninstall them
    # todo: prendere un path a un config file con la lista di repo whitelisted permesso sul dominio
    # API REST CONFIG: add runtime, get runtimes, add whitelist (auth), get whitelist (auth)
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

    if runtimes_ready() and is_mappings_db_ready():

         # if config.NODE_TYPE == "local-edge":
           # awareness = Awareness()
           # awareness.start()

         #loadsimulator = LoaderSimulator()

         allocation = Allocation()
         acquisition = Acquisition(allocation)

         # run Websocket server
         #websocketserver = A3EWebsocketServerProtocol()
         #websocketserver.start()

         #ws_process = Process(target=start_ws_server)
         #ws_process.start()

         #loader_process = Process(target=start_loader_process)
         #loader_process.start()



         command_line_string = f"--private-host-ip={config.PRIVATE_HOST_IP} --public-host-ip={config.PUBLIC_HOST_IP} --wsk-path={config.WSK_PATH}"



         os.system("python run_ws_server.py")

         # run Flask REST API
         if config.RUN_FLASK:
             app.run(host=config.PRIVATE_HOST_IP, port=config.FLASK_PORT, debug=False)

         t.sleep(config.DEFAULT_EXECUTION_TIME)
         #if awareness is not None:
         #   awareness.stop()

         #websocketserver.stop()
    else:
        print("A3E Domain Manager not ready, aborting...")
