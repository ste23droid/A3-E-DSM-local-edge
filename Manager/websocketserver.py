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
        self.factory = WebSocketServerFactory(u"ws://{}:{}".format(config.PRIVATE_HOST_IP, config.WEBSOCKET_PORT))
        self.factory.protocol = A3EWebsocketServerProtocol

    async def wrap_db_request(self, request_json, message_json, delta_time):
        return requests.post("{}/{}".format(config.COUCH_DB_BASE, config.DB_METRICS_NAME),
                             data=json.dumps({"function": request_json["function"],
                                              "execMs": delta_time,
                                              "payloadBytes": len(message_json)}),
                             verify=False,
                             headers=config.APPLICATION_JSON_HEADER)

    async def handleRequest(self, json_request, json_message):

        def wrap_exec_request(request_json, message_json):
            # directly make requests to wsk controller, bypass api gateway
            return requests.post("http://{}:8888/api/v1/web/guest/{}?blocking=true&result=true".format(config.PRIVATE_HOST_IP,
                                                                                                       request_json["function"]),
                                                                                                        data=message_json,
                                                                                                        verify=False,
                                                                                                        headers=config.APPLICATION_JSON_HEADER)

        # start = t.time()
        await self.loop.run_in_executor(None, lambda: wrap_exec_request(request_json=json_request,
                                                                        message_json=json_message))
        # delta_time_millis = (t.time() - start) * 1000
        #print(f"Time spent awaiting http response from whisk: {delta_time}")

        # add asynchronously action execution metrics to the metrics db
        # db_start = t.time()
        # loop.create_task(self.wrap_db_request(json_request, json_message, delta_time_millis))
        #db_delta_time = (t.time() - db_start) * 1000
        #print(f"Time spent fire and forget request to db: {db_delta_time}")
        #response_json = exec_response.json()
        #response_json["execTime"] = delta_time_millis

    async def onMessage(self, payload, isBinary):
        print("Websocket received a message")
        if not isBinary:
            json_message = payload.decode('utf8')
            request_json = json.loads(json_message)

            try:
                await self.handleRequest(request_json, json_message)
            except Exception:
                print("Exception on websocket request handling...")
                self.sendClose(1000, "Exception raised on websocket")
            #else:
                #self.sendMessage("Hello".encode('utf-8'))
        else:
            # binary message receive to close ws tests
            self.sendMessage(b"\x00\x01\x03\x04", isBinary=True)

    async def onConnect(self, request):
        print("A client connected to A3E Websocket")


    async def onClose(self, wasClean, code, reason):
        print("Connection with client closed")
        print(f"wasClean: {wasClean}")
        print(f"code: {code}")
        print(f"reason: {reason}")


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
        self.awthread.join()

    # async def handleRequest(self, json_request):
    #
    #     json_message = json.dumps(json_request)
    #     loop = asyncio.get_event_loop()
    #
    #     def wrap_exec_request(request_json, message_json):
    #         return requests.post(
    #             "https://{}/api/v1/web/guest/{}".format(config.PRIVATE_HOST_IP, request_json["function"]),
    #                                                     data=message_json,
    #                                                     verify=False,
    #                                                     headers=config.APPLICATION_JSON_HEADER)
    #
    #     start = t.time()
    #     future_exec_response = loop.run_in_executor(None, lambda: wrap_exec_request(request_json=json_request,
    #                                                                                 message_json=json_message))
    #     exec_response = await future_exec_response
    #     delta_time_millis = (t.time() - start) * 1000
    #     #print(f"Time spent awaiting http response from whisk: {delta_time}")
    #
    #     # add asynchronously action execution metrics to the metrics db
    #     #db_start = t.time()
    #     loop.create_task(self.wrap_db_request(json_request, json_message, delta_time_millis))
    #     #db_delta_time = (t.time() - db_start) * 1000
    #     #print(f"Time spent fire and forget request to db: {db_delta_time}")
    #     response_json = exec_response.json()
    #     response_json["execTime"] = delta_time_millis
    #     # print(response_json)
    #     return json.dumps(response_json).encode('utf-8')

    # async def onMessage(self, payload, isBinary):
    #     print("Websocket received a message")
    #     if not isBinary:
    #         request_json = json.loads(payload.decode('utf8'))
    #         if "function" in request_json:
    #             try:
    #                 response = await self.handleRequest(request_json)
    #             except Exception as e:
    #                 print(f"Exception on websocket request handling..., {e}")
    #                 self.sendClose(1000, "Exception raised: {0}".format(e))
    #             else:
    #                 # the response should be returned in UTF-8 encoding
    #                 print("Websocket server sending response")
    #                 self.sendMessage(response)
    #         else:
    #             self.sendMessage("Error, request not containing function endpoint")
    #     else:
    #         print("A binary message was received from the client, ignoring it ...")
    #         self.sendClose(1000)
