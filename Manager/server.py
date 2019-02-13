import time as t
import argparse
import requests
import json
import numpy
import re
from awareness import Awareness
from acquisition import Acquisition
from allocation import Allocation
from websocketserver import A3EWebsocketServerProtocol
import config
from subprocess import check_output
from flask import Flask, request, Response

app = Flask(__name__)
awareness = None
allocation = None
acquisition = None
requests.packages.urllib3.disable_warnings()


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
    # print(response_json)
    return Response(json.dumps(response_json), mimetype='application/json')


@app.route('/monitoring', methods=['POST'])
def monitoring():
    content = request.json
    # get list of installed actions from openwhisk
    raw_actions_list = check_output("{} action list -i".format(config.WSK_PATH), shell=True).splitlines()[1:]
    # print(raw_actions_list)

    parsed_action_list = []
    for raw_action_name in raw_actions_list:
        # /guest/ste23droid/faceDetection                                        private blackbox
        wsk_name = (raw_action_name.split())[0]
        # e.g /guest/ste23droid/faceDetection -> but in the mappings actions are saved with ste23droid/faceDetection
        wsk_name_splitted = wsk_name[7:]
        print(f"Whisk name action splitted: {wsk_name_splitted}")
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


# @app.route('/invoke', methods=['POST'])
# def invoke():
#     content = request.json
#     # print("Received Invoke json: " + str(content))
#     # client_ip = request.remote_addr
#     # print("Received Invoke Request from ip: " + client_ip)
#     # print("Received Invoke json: " + str(content))
#     start = t.time()
#     # response = check_output("{} action invoke {}/{} --param image {} --result --insecure".format(config.WSK_PATH,
#                                                                    # config.WHISK_NAMESPACE,
#                                                                    # content["function"],
#                                                                    # content["image"]), shell=True)
#     json_message = json.dumps(content)
#     response = requests.post("https://{}/api/v1/web/guest/{}".format(config.PRIVATE_HOST_IP, content["function"]),
#                                      data=json_message,
#                                      verify=False,
#                                      headers=config.APPLICATION_JSON_HEADER)
#     # # add metrics to the function metrics db
#     # requests.post("{}/{}_{}".format(config.COUCH_DB_BASE,
#     #                                config.DB_METRICS_BASE_NAME,
#     #                                re.sub("/", "_", content["function"].lower())),
#     #                                  data=json.dumps({"execMs": (t.time() - start)*1000,
#     #                                                   "payloadBytes": len(json_message)}),
#     #                                  verify=False,
#     #                                  headers=config.APPLICATION_JSON_HEADER)
#
#     # add action execution metrics to the metrics db
#     requests.post("{}/{}".format(config.COUCH_DB_BASE, config.DB_METRICS_NAME),
#                   data=json.dumps({"function":  content["function"],
#                                    "execMs": (t.time() - start) * 1000,
#                                    "payloadBytes": len(json_message)}),
#                   verify=False,
#                   headers=config.APPLICATION_JSON_HEADER)
#     return Response(response.content, mimetype='application/json')






# def get_metrics_avg_std(action_name):
#     # todo: see if we can get metrics for all the actions at once, using the same key with multiple values
#     # action name : guest/ste23droid/faceDetection
#     action_name = re.sub("/", "_", action_name)
#     # action_metrics_db_name = "{}_{}_{}".format(config.DB_METRICS_BASE_NAME,
#     #                                            action_name.split('_')[1].lower(),
#     #                                            action_name.split('_')[2].lower())
#     action_metrics_url = "{}/{}/_design/{}/_view/{}?key=\"{}/{}\"".format(config.COUCH_DB_BASE,
#                                                                                 config.DB_METRICS_NAME,
#                                                                                 config.DB_METRICS_DESIGN_DOC,
#                                                                                 config.DB_METRICS_VIEW_NAME,
#                                                                                 action_name.split("_")[1],
#                                                                                 action_name.split("_")[2])
#     metrics_result = requests.get(action_metrics_url)
#     json_result = metrics_result.json()
#
#     # we have saved metrics for the action
#     if len(json_result["rows"]) == 1:
#         metrics_content = json_result["rows"][0]["value"]
#         return {"execTime": {"avg": metrics_content["average"], "stdDev": metrics_content["stdDeviation"]}}
#
#     return None

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

# def is_metrics_db_ready():
#     metrics_db_url = config.COUCH_DB_BASE + "/" + config.DB_METRICS_NAME
#     get_metrics_db = requests.get(metrics_db_url)
#
#     if get_metrics_db.status_code == 200:
#         print("Metrics database found!")
#         return True
#
#     elif get_metrics_db.status_code == 404:
#         print("Metrics database not found, creating it...")
#         create_metrics_db = requests.put(metrics_db_url)
#
#         if create_metrics_db.status_code == 201:
#             print("Metrics database created")
#             return True
#
#         else:
#             print(create_metrics_db.json()["reason"])
#     else:
#         print(get_metrics_db.json()["reason"])
#
#     return False


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


# def are_db_views_ready():
#     metrics_design_doc_url = "{}/{}/_design/{}".format(config.COUCH_DB_BASE,
#                                                        config.DB_METRICS_NAME,
#                                                        config.DB_METRICS_DESIGN_DOC)
#     get_design_doc = requests.get(metrics_design_doc_url)
#
#     if get_design_doc.status_code == 200:
#         print("Design document found!")
#         return True
#
#     elif get_design_doc.status_code == 404:
#         print("Metrics design document not found, creating it...")
#
#         # this will create both design doc and the needed views inside it
#         couch_db_parent_dir = dirname(abspath(__file__))
#         metrics_design_doc_path = join(join(couch_db_parent_dir, "couchdb"), "metrics_design_doc.json")
#         print(metrics_design_doc_path)
#         create_design_doc = requests.put(metrics_design_doc_url,
#                                          data=open(metrics_design_doc_path, "r"),
#                                          headers=config.APPLICATION_JSON_HEADER)
#
#         if create_design_doc.status_code == 201:
#             print("Metrics design document and views created")
#             return True
#
#         else:
#             print(create_design_doc.json()["reason"])
#     else:
#         print(get_design_doc.json()["reason"])
#
#     return False

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

    parsed, ignored = parser.parse_known_args()

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

    if runtimes_ready() and is_mappings_db_ready():
            #and is_metrics_db_ready() \
            #and are_db_views_ready()\

         if config.NODE_TYPE == "local-edge":
            awareness = Awareness()
            awareness.start()

         allocation = Allocation()
         acquisition = Acquisition(allocation)

         # run Websocket server
         websocketserver = A3EWebsocketServerProtocol()
         websocketserver.start()

         # run Flask REST API
         if config.RUN_FLASK:
             app.run(host=config.PRIVATE_HOST_IP, port=config.FLASK_PORT, debug=False)

         t.sleep(config.DEFAULT_EXECUTION_TIME)
         if awareness is not None:
            awareness.stop()

         websocketserver.stop()
    else:
        print("A3E Domain Manager not ready, aborting...")
