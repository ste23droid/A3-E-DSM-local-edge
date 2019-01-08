from autobahn.asyncio.websocket import WebSocketServerProtocol, WebSocketServerFactory
import asyncio
import json
import config
import threading
import requests
import time as t


class A3EWebsocketServerProtocol(WebSocketServerProtocol):

    def __init__(self):
        super().__init__
        self.loop = asyncio.get_event_loop()
        self.wsthread = threading.Thread(target=self.__run_loop, args=(self.loop,))
        self.factory = WebSocketServerFactory("ws://{}:{}".format(config.PRIVATE_HOST_IP, config.WEBSOCKET_PORT).encode())
        self.factory.protocol = A3EWebsocketServerProtocol


    async def handleRequest(self, json_request):

        start = t.time()
        json_message = json.dumps(json_request)
        loop = asyncio.get_event_loop()

        # https://stackoverflow.com/questions/22190403/how-could-i-use-requests-in-asyncio
        # https://stackoverflow.com/questions/23946895/requests-in-asyncio-keyword-arguments
        def wrap_exec_request(request_json, message_json):
            return requests.post(
                "https://{}/api/v1/web/guest/{}".format(config.PRIVATE_HOST_IP, request_json["function"]),
                                                        data=message_json,
                                                        verify=False,
                                                        headers=config.APPLICATION_JSON_HEADER)

        def wrap_db_request(request_json, message_json, start_time):
            return requests.post("{}/{}".format(config.COUCH_DB_BASE, config.DB_METRICS_NAME),
                          data=json.dumps({"function": request_json["function"],
                                           "execMs": (t.time() - start_time) * 1000,
                                           "payloadBytes": len(message_json)}),
                          verify=False,
                          headers=config.APPLICATION_JSON_HEADER)

        future_exec_response = loop.run_in_executor(None, lambda: wrap_exec_request(request_json=json_request,
                                                                                    message_json=json_message))
        exec_response = await future_exec_response

        # add action execution metrics to the metrics db
        future_db_response = loop.run_in_executor(None, lambda: wrap_db_request(request_json=json_request,
                                                                               message_json=json_message,
                                                                               start_time=start))
        await future_db_response

        return exec_response.content

    # async def handleRequest(self, json_request):
    #     start = t.time()
    #     json_message = json.dumps(json_request)
    #     loop = asyncio.get_event_loop()
    #
    #     # https://stackoverflow.com/questions/22190403/how-could-i-use-requests-in-asyncio
    #     # https://stackoverflow.com/questions/23946895/requests-in-asyncio-keyword-arguments
    #     def wrap_exec_request(request_json, message_json):
    #         return requests.post(
    #             "https://{}/api/v1/web/guest/{}".format(config.WHISK_API_HOST, "ste23droid/faceDetection"),
    #             data=message_json,
    #             verify=False,
    #             headers=config.APPLICATION_JSON_HEADER)
    #
    #     def wrap_db_request(request_json, message_json, start_time):
    #         return requests.post("{}/{}".format(config.COUCH_DB_BASE, config.DB_METRICS_NAME),
    #                              data=json.dumps({"function": "ste23droid/faceDetection",
    #                                               "execMs": (t.time() - start_time) * 1000,
    #                                               "payloadBytes": len(message_json)}),
    #                              verify=False,
    #                              headers=config.APPLICATION_JSON_HEADER)
    #
    #     future_exec_response = loop.run_in_executor(None, lambda: wrap_exec_request(request_json=json_request,
    #                                                                                 message_json=json_message))
    #     exec_response = await future_exec_response
    #
    #     # add action execution metrics to the metrics db
    #     future_db_response = loop.run_in_executor(None, lambda: wrap_db_request(request_json=json_request,
    #                                                                             message_json=json_message,
    #                                                                             start_time=start))
    #     await future_db_response
    #
    #     return exec_response.content

    async def onMessage(self, payload, isBinary):
        print("Websocket received a message")
        if not isBinary:
            request_json = json.loads(payload.decode('utf8'))
            if "function" in request_json:
                try:
                    response = await self.handleRequest(request_json)
                except Exception as e:
                    print(f"Exception on websocket request handling..., {e}")
                    self.sendClose(1000, "Exception raised: {0}".format(e))
                else:
                    # the response should be returned in UTF-8 encoding
                    print("Websocket server sending response")
                    self.sendMessage(response)
            else:
                self.sendMessage("Error, request not containing function endpoint")
        else:
            print("A binary message was received from the client, ignoring it ...")
            self.sendClose(1000)

    # async def onMessage(self, payload, isBinary):
    #     print("Websocket received a message")
    #     if not isBinary:
    #         request_json = json.loads(payload.decode('utf8'))
    #
    #         try:
    #             response = await self.handleRequest(request_json)
    #         except Exception as e:
    #             print(f"Exception on websocket request handling..., {e}")
    #             self.sendClose(1000, "Exception raised: {0}".format(e))
    #         else:
    #             # the response should be returned in UTF-8 encoding
    #             print("Websocket sending response")
    #             self.sendMessage(response)
    #     else:
    #         print("A binary message was received from the client, ignoring it ...")
    #         self.sendClose(1000)

    # async def onMessage(self, payload, isBinary):
    #     print("Websocket received a message")
    #     if not isBinary:
    #         print("Websocket sending response")
    #         self.sendMessage(payload)
    #     else:
    #         print("A binary message was received from the client, ignoring it ...")
    #         self.sendClose(1000)

    async def onConnect(self, request):
        print("A client connected to A3E Websocket")

    async def onClose(self, wasClean, code, reason):
        print("Connection with client closed")
        print(f"wasClean: {wasClean}")
        print(f"code: {code}")
        print(f"reason: {reason}")


    def __run_loop(self, loop):
        asyncio.set_event_loop(loop)
        # https://stackoverflow.com/questions/26270681/can-an-asyncio-event-loop-run-in-the-background-without-suspending-the-python-in
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
        self.awthread.join()
