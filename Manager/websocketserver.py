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
        self.firstReq = None
        self.overheadCumulativeSec = 0.0

    async def wrap_db_request(self, request_json, message_json, delta_time_sec):
        function_name = "function"
        #func_name_for_db = re.sub("/", "-", function_name).lower()
        #requests.post("{}/{}-{}".format(config.COUCH_DB_BASE,
        #                                       config.DB_METRICS_NAME,
        #                                       func_name_for_db),
        #                     data=json.dumps({"execTimeSec": delta_time_sec,
        #                                      "payloadBytes": len(message_json),
        #                                      "requestTime": t.time()}),
        #                     verify=False,
        #                     headers=config.APPLICATION_JSON_HEADER)

    async def handleRequest(self, json_request, json_message):
        startRequest = t.time()
        loop = asyncio.get_event_loop()

        def wrap_exec_request(request_json, message_json):
            return requests.post("http://{}:5050/test"
                                 .format(config.PRIVATE_HOST_IP),
                                 data=message_json,
                                 verify=False,
                                 headers=config.APPLICATION_JSON_HEADER)
        startExec = t.time()
        exec_response_future = self.loop.run_in_executor(None, lambda: wrap_exec_request(request_json=json_request,
                                                                                         message_json=json_message))

        exec_response = await exec_response_future
        execTimeSec = t.time() - startExec

        loop.create_task(self.wrap_db_request(json_request, json_message, execTimeSec))

        response_json = exec_response.json()
        response_json["execTimeSec"] = execTimeSec
        self.overheadCumulativeSec += t.time() - startRequest
        return json.dumps(response_json).encode('utf-8')

    async def onMessage(self, payload, isBinary):
        json_message = payload.decode('utf-8')
        request_json = json.loads(json_message)

        try:
            response = await self.handleRequest(request_json, json_message)

        except Exception as e:
            print("Ws exception: {}".format(e))
            self.sendClose(1000)
        else:
            self.sendMessage(response)

    async def onConnect(self, request):
        print("A client connected to A3E Websocket")


    async def onClose(self, wasClean, code, reason):
        print("Connection with client closed")
        print("Overhead seconds cumulative: {}".format(self.overheadCumulativeSec))
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
