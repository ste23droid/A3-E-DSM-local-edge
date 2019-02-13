from autobahn.asyncio.websocket import WebSocketServerProtocol, WebSocketServerFactory
import asyncio
import json
import config
import threading
import requests
import time as t
import re


class A3EWebsocketServerProtocol(WebSocketServerProtocol):

    def __init__(self):
        super().__init__()
        self.loop = asyncio.get_event_loop()
        self.wsthread = threading.Thread(target=self.__run_loop, args=(self.loop,))
        self.factory = WebSocketServerFactory(u"ws://{}:{}".format(config.PRIVATE_HOST_IP, config.WEBSOCKET_PORT))
        self.factory.protocol = A3EWebsocketServerProtocol

    async def wrap_db_request(self, request_json, message_json, delta_time_sec):
        # function_name is for example ste23droid/faceDetection
        function_name = request_json["function"]
        func_name_for_db = re.sub("/", "-", function_name).lower()
        # db name is for example metrics-ste23droid-facedetection
        post_db_request = requests.post("{}/{}-{}".format(config.COUCH_DB_BASE,
                                               config.DB_METRICS_NAME,
                                               func_name_for_db),
                             data=json.dumps({"execTimeSec": delta_time_sec,
                                              "payloadBytes": len(message_json),
                                              "requestTime": t.time()}),
                             verify=False,
                             headers=config.APPLICATION_JSON_HEADER)
        print("Post function exec metrics to db, response code: {}".format(post_db_request))

    async def handleRequest(self, json_request, json_message):
        loop = asyncio.get_event_loop()

        def wrap_exec_request(request_json, message_json):
            # web action important return params https://console.bluemix.net/docs/openwhisk/openwhisk_webactions.html#openwhisk_webactions
            # directly make requests to wsk controller port 8888, bypass api gateway
            # function: repoOwner/functionName e.g ste23droid/faceDetection
            if "auth" not in request_json:
                # WEB ACTION
                return requests.post("http://{}:8888/api/v1/web/guest/{}?blocking=true&result=true"
                                     .format(config.PRIVATE_HOST_IP, request_json["function"]),
                                     data=message_json,
                                     verify=False,
                                     headers=config.APPLICATION_JSON_HEADER)
            else:
                # AUTHENTICATED ACTION: for now we support just Basic Auth
                return requests.post("http://{}@{}:8888/api/v1/namespaces/guest/actions/{}?blocking=true&result=true"
                                     .format(request_json["auth"],
                                             config.PRIVATE_HOST_IP,
                                             request_json["function"]),
                                     data=message_json,
                                     verify=False,
                                     headers=config.APPLICATION_JSON_HEADER)

        # https://docs.python.org/2/library/time.html
        startExec = t.time()
        # http://docs.python-requests.org/en/master/_modules/requests/models/#Response.json
        exec_response_future = self.loop.run_in_executor(None, lambda: wrap_exec_request(request_json=json_request,
                                                                                         message_json=json_message))

        exec_response = await exec_response_future
        #print("Resp code {}".format(exec_response))
        execTimeSec = t.time() - startExec

        # add asynchronously action execution metrics to the function's metrics db
        #db_start = t.time()
        loop.create_task(self.wrap_db_request(json_request, json_message, execTimeSec))
        #db_delta_timeSec = t.time() - db_start
        #print(f"Time spent fire and forget request to db: {db_delta_timeSec}")

        response_json = exec_response.json()
        #print("Response {}".format(response_json))
        # add execTimeSec to the response, so that clients can measure the throughput towards the Domain Manager
        response_json["execTimeSec"] = execTimeSec
        # the response should be returned in UTF-8 encoding!!!
        return json.dumps(response_json).encode('utf-8')

    async def onMessage(self, payload, isBinary):
        print("Websocket received a message")
        json_message = payload.decode('utf-8')
        request_json = json.loads(json_message)
        # print("Func received: {}".format(request_json["function"]))

        try:
            response = await self.handleRequest(request_json, json_message)

        except Exception as e:
            print("Ws exception: {}".format(e))
            self.sendClose(1000)
        else:
            # the response should be returned in UTF-8 encoding!!!
            # print("Websocket sending response")
            self.sendMessage(response)

    async def onConnect(self, request):
        print("A client connected to A3E Websocket")


    async def onClose(self, wasClean, code, reason):
        print("Connection with client closed")
        #print(f"wasClean: {wasClean}")
        #print(f"code: {code}")
        #print(f"reason: {reason}")


    def __run_loop(self, loop):
        asyncio.set_event_loop(loop)
        coro = loop.create_server(self.factory, config.PRIVATE_HOST_IP, config.WEBSOCKET_PORT)
        server = loop.run_until_complete(coro)

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.close()
            loop.close()

    def start(self):
        print("Starting Websocket server...")
        # thread will die when the main thread dies
        self.wsthread.daemon = True
        self.wsthread.start()

    def stop(self):
        print("Stopping Websocket server...")
        self.wsthread.join()
