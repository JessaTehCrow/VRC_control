from threading import Thread, Event
from pythonosc.dispatcher import Dispatcher
from pythonosc import osc_server
import time
from pythonosc import udp_client
import param_control_web
from cprint import cprint
import asyncio
import avatar_params

accessing = Event()

# Base vrc parameters
parameter_ignore_list = [
    "Avatar Scale",
    "Viseme",
    "Voice",
    "GestureLeft",
    "GestureLeftWeight",
    "GestureRight",
    "GestureRightWeight",
    "TrackingType",
    "AFK",
    "Seated",
    "Grounded",
    "Earmuffs",
    "MuteSelf",
    "Upright",
    "AngularY",
    "VRMode",
    "InStation",
    "VelocityX",
    "VelocityY",
    "VelocityZ",
    "VRCEmote",
    "VRCFaceBlendH",
    "VRCFaceBlendV",
    "Sync Scale",
    "IsScaled",
    "ScaleTimer"
]

HOST = "127.0.0.1"
PORT_RECEIVE = 9001
PORT_SEND    = 9000

# Function to make sure the database isn't written to at the same time by two different threads
def wait_for_access(thread):
    while accessing.is_set():
        time.sleep(.1)
        print(thread,"Awaiting access")
    accessing.set()


### OSC THREAD ###

# OSC event from vrchat itself
# (vrc player changed toggles)
def osc_handle(params:dict, client:udp_client.SimpleUDPClient, adress:str, value:float):
    param_name = adress.split('/')[-1]
    wait_for_access("osc")

    # Get data from database
    parameter = params[param_name]
    if parameter['locked'] and parameter['value'] != value:
        # parameter locked, resetting value in vrc
        client.send_message(adress, parameter['value'])

    elif not parameter['locked'] and parameter['value'] != value:
        # Update value in database
        params[param_name]['value'] = value

    accessing.clear()

# Main OSC thread
def osc_func(params):
    # Setup client and server
    client = udp_client.SimpleUDPClient(HOST, PORT_SEND)
    dispatcher = Dispatcher()

    # Create listen events for all user-set parameters
    for param in params:
        dispatcher.map(f"/avatar/parameters/{param}", lambda *a: osc_handle(params, client, *a))
    
    # Prepare server
    server = osc_server.ThreadingOSCUDPServer(
        (HOST, PORT_RECEIVE), dispatcher)

    cprint("[Y]OSC server running....")
    server.serve_forever()


### WEB THREAD ###

def update_param(params, name, value):
    wait_for_access("web")

    params[name] = value
    accessing.clear()

def get_values(params):
    wait_for_access("web")
    copy = dict(params)
    accessing.clear()

    return copy

# Main WEB thread
def web_func(params):
    # prepare functions for thread
    update_func = lambda n,v: update_param(params, n, v)
    get_func    = lambda: get_values(params)

    # prepare osc client
    client      = udp_client.SimpleUDPClient(HOST, PORT_SEND)
    
    # Create new event loop for thread
    loop        = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Run web server
    param_control_web.run(update_func, get_func, client)


### MAIN THREAD ##

def main(data):
    osc = Thread(target=osc_func, args=(data,))
    web = Thread(target=web_func, args=(data,))

    osc.start()
    web.start()

    osc.join()
    web.join()


if __name__ == "__main__":
    import os

    if not os.path.isfile("avatars.json"):
        with open("avatars.json",'w') as f:
            f.write("{}")

    data = avatar_params.get_params(parameter_ignore_list)
    main(data)