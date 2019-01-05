from autobahn.asyncio.websocket import WebSocketServerProtocol, WebSocketServerFactory
import asyncio
import json
import config
import threading
import requests
import time as t

class A3EWebsocketServerProtocol(WebSocketServerProtocol):

    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.wsthread = threading.Thread(target=self.__run_loop, args=(self.loop,))
        self.factory = WebSocketServerFactory(u"ws://{}:{}".format(config.WEBSOCKET_HOST, config.WEBSOCKET_PORT))
        self.factory.protocol = A3EWebsocketServerProtocol

    async def handleRequest(self, json_request):
        start = t.time()
        json_message = json.dumps(json_request)
        print(json_message)
        #
        # # run request
        # response = await requests.post("https://{}/api/v1/web/guest/{}".format(config.WHISK_API_HOST, json_request["function"]),
        #                          data=json_message,
        #                          verify=False,
        #                          headers=config.APPLICATION_JSON_HEADER)
        #
        # # add action execution metrics to the metrics db
        # await requests.post("{}/{}".format(config.COUCH_DB_BASE, config.DB_METRICS_NAME),
        #               data=json.dumps({"function": json_request["function"],
        #                                "execMs": (t.time() - start) * 1000,
        #                                "payloadBytes": len(json_message)}),
        #               verify=False,
        #               headers=config.APPLICATION_JSON_HEADER)
        return json_message

    async def onMessage(self, payload, isBinary):
        print("Websocket received a message")
        if not isBinary:
            request_json = json.loads(payload.decode('utf8'))
            try:
                response = await self.handleRequest(request_json)
            except Exception as e:
                self.sendClose(1000, "Exception raised: {0}".format(e))
            else:
                self.sendMessage(json.dumps(response).encode('utf8'))
        else:
            print("A binary message was received from the client, ignoring it ...")
            self.sendClose(1000)

    async def onConnect(self, request):
        print("A client connected to A3E Websocket")

    async def onClose(self, wasClean, code, reason):
        print("Connection with client closed")
        print("wasClean: {}".format(wasClean))
        print("code: " + code)
        print("reason: " + reason)


    def __run_loop(self, loop):
        asyncio.set_event_loop(loop)
        # https://stackoverflow.com/questions/26270681/can-an-asyncio-event-loop-run-in-the-background-without-suspending-the-python-in
        coro = loop.create_server(self.factory, config.WEBSOCKET_HOST, config.WEBSOCKET_PORT)
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
        self.awthread.join()
