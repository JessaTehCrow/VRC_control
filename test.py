from pythonosc import osc_server, udp_client
from pythonosc.dispatcher import Dispatcher

import websocket
import threading
import asyncio
import time
import json
import os

def myround(x, prec=2, base=0.05):
    return round(base * round(float(x)/base),prec)



class BackgroundJobs():
    def __init__(self):
        self.initialized = False

        self.websocket = None
        self._web_thread = None
        self.count = 0

        self._osc_data = {}
        self.osc_client = None
        self._osc_server = None
        self._osc_thread = None

        self.osc_host = "127.0.0.1"
        self.osc_send = 9000
        self.osc_recv = 9001

        self.roomid = None

    def create_room(self):
        data = {
            "type":"create",
            "data":{

            }
        }


    def init_websocket(self):
        thread = threading.Thread(target=self._setup_socket)
        thread.start()
        self._web_thread = thread
    

    def bg_send(self, data:str):
        self.websocket.send(data)


    def init_osc(self):
        thread = threading.Thread(target=asyncio.run, args=(self._osc_loop(),))
        thread.start()
        self._osc_thread = thread


    async def _osc_loop(self):
        client = udp_client.SimpleUDPClient(self.osc_host, self.osc_send)
        dispatcher = Dispatcher()
        
        # Create listen events for all user-set parameters
        for param in self._osc_data:
            dispatcher.map(f"/avatar/parameters/{param}", self._osc_handle)
        
        server = osc_server.ThreadingOSCUDPServer(
            (self.osc_host, self.osc_recv), dispatcher)
        
        self.osc_client = client
        self._osc_server = server
        server.serve_forever()
    

    def _on_websocket_connect(self, socket):
        self.initialized = True
        self.websocket = socket
        print("Connected to socket")


    def _on_websocket_message(self, _, message):
        # print(message)
        msg = json.loads(message)
        self._socket_handle_input(msg)


    def _on_websocket_close(self, ws, close_status_code, close_msg):
        self._setup_socket()
        self.initialized = False


    def _setup_socket(self):
        while True:
            try:
                socket = websocket.WebSocketApp("ws://localhost:8080", on_message=self._on_websocket_message, on_open=self._on_websocket_connect, on_close=self._on_websocket_close)
                socket.run_forever()
            except Exception as e:
                print(e)


    def _osc_handle(self, adress:str, value):
        print(adress, value)
        name = adress[len("/avatar/parameters/"):]
        
        if type(value) == float:
            value = myround(value)

        if name not in self._osc_data:
            return

        elif value == self._osc_data[name][0]:
            return
        

        async def inner():
            self._osc_data[name][0] = value
            self.bg_send(json.dumps({"type":"update","data":{"name":name, "value":value}}))
            self.count += 1
            print(adress, value)

        return asyncio.run(inner())


    def _socket_handle_input(self, data:dict):
        print(data)
        if "message" in data:
            print(data["message"])

        if not "type" in data:
            return

        handle_type = data["type"]

        if handle_type == "update":
            req_data = data["data"]
            name = req_data["name"]
            value = req_data["value"]

            if type(value) == float:
                value = myround(value)
            
            if self._osc_data[name] == value:
                return

            self._osc_data[name][0] = value
            print("NEW VALUE:", value, type(value))
            self.osc_client.send_message("/avatar/parameters/"+name, value)

        elif handle_type == "connected":
            req_data = data["data"]
            self.roomid = req_data["id"]
            self._osc_data = {name:value[1:] for (name,value) in req_data["data"].items()}
        
        elif handle_type == "disconnect":
            self.roomid = None
            self._osc_data = {}

        else:
            print(data)

if __name__ == "__main__":
    bg = BackgroundJobs()
    bg.init_websocket()
    try:
        while not bg.initialized:
            time.sleep(0.1)
    except:
        os._exit(0)

    bg.bg_send('{"type":"connect", "data":{"id":"5VQGZ"}}')
    time.sleep(1)
    bg.init_osc()

    while True:
        try:
            time.sleep(100)
        except:
            break

    print(bg.count)
    os._exit(0)