from pythonosc import osc_server, udp_client
from pythonosc.dispatcher import Dispatcher
from json import dumps, loads, dump, load
from websocket import WebSocketApp
from pydub.playback import play
from pydub import AudioSegment
from threading import Thread
from string import printable
from customtkinter import *
from os import listdir, getenv
from time import time

import os.path as path
import asyncio
import ssl


get_file = lambda name: path.join(path.dirname(__file__), name)
get_sound = lambda name: AudioSegment.from_wav(get_file("sounds/"+name))


join_sound = get_sound("join.wav")
leave_sound = get_sound("leave.wav")
change_sound = get_sound("change.wav")


default_vrc_dir = path.join(getenv("APPDATA"), "../LocalLow/VRChat/VRChat/OSC/")


def play_sound(sound):
    settings = AppSettings().load_settings("settings.json")
    volume = settings["normal"]["volume"]["value"]

    vol = sound - (20 * (1-volume))
    Thread(target=play, args=(vol,)).start()


def myround(x, prec=2, base=0.0125):
    new_value = round(base * round(x/base), prec)
    return new_value
    # return round(base * round(float(x)/base), prec)


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
    "ScaleTimer",
    "VelocityMagnitude",
    "ScaleFactor",
    "ScaleModified",
    "ScaleFactorInverse",
    "EyeHeightAsMeters",
    "EyeHeightAsPercent",
    "Go/Horizon",
    "Go/JumpAndFall",
    "Go/Pose",
    "Go/Scale",
    "Go/Scaling",
    "Go/ThirdPersonMirror",
    "Go/ThirdPerson",
    "Go/ScaleSave",
    "Go/Stationary",
    "Go/Locomotion",
    "Go/Emote",
    "Go/Float",
    "Go/JSRF/ReadyToGrind",
    "Go/JSRF/Timer",
    "Go/ScaleFloat",
    "Go/Locomotion",
    "Go/IsUpright",
    "Go/Jump",
    "Go/Mirror",
    "Go/SVRB/Grounded",
    "Go/PosePlaySpace",
    "Go/JSRF/WallRun"
]


default_settings = {
    "normal": {
        "update": {
            "name": "Check for updates",
            "value": False
        },
        "autoUpdate": {
            "name": "Auto Update",
            "value": False
        },
        "joinSounds": {
            "name": "Join / Leave sounds",
            "value": True
        },
        "closeSounds": {
            "name": "Sounds on room close",
            "value": True
        },
        "changeSounds": {
            "name": "Sound on parameter change",
            "value": True
        },
        "volume": {
            "name": "Sound volume",
            "value": 0.5
        },
        "changeDelay": {
            "name": "Delay between parameter change sounds",
            "value": 0.13
        }
    },
    "advanced": {
        "host": {
            "name": "Host",
            "value": "wss://crows.world/wss/:8081",
            "type": "text"
        },
        "vrcfolder": {
            "name": "OSC Avatar folder",
            "value": default_vrc_dir,
            "type": "path"
        }
    }
}


def get_root(widget):
    widget = widget
    while not (isinstance(widget, CTk) or isinstance(widget, CTkToplevel)):
        widget = widget.master
    
    return widget


def get_avatars() -> dict:
    folder:str = AppSettings().load_settings(default=default_settings)["advanced"]["vrcfolder"]["value"]
    avatars:dict = {}
    if not path.isdir(folder):
        return avatars        

    for user_folder in listdir(folder):
        if not path.isdir(folder + "/" + user_folder + "/Avatars"):
            continue

        for settings_path in listdir(folder + "/" + user_folder + "/Avatars"):
            filepath = path.join(folder + "/" + user_folder + "/Avatars", settings_path)

            if not settings_path.endswith(".json"):
                continue
            
            with open(filepath, 'rb') as f:
                raw = f.read()
                raw = raw.decode('Windows-1252', 'ignore')
                raw = ''.join([x for x in raw if x in printable])

                json_data = raw[raw.index("{"):]
                data:dict = loads(json_data)
                if not "name" in data:
                    print("Invalid avatar file")
                    continue

                offset:int = 0
                
                for i in range(len(data["parameters"])):
                    name:str = data["parameters"][i-offset]["name"]
                    if name in parameter_ignore_list:
                        data["parameters"].pop(i-offset)
                        offset += 1

                avatars[data["name"]] = data

    return avatars


def get_avatar_data(params:dict, selected:dict) -> dict:
    defaults:dict = {
        "bool": False,
        "float": 0.0,
        "int": 0
    }

    out:dict = {}
    for param in params:
        if param["name"] not in selected:
            continue
        
        inp_type:str = param["input"]["type"].lower()
        out[param["name"]] = [inp_type, defaults[inp_type]]
    
    return out


class BackgroundJobs():
    def __init__(self):
        self.initialized = False

        self.settings = None
        
        self.websocket = None
        self.websocket_error = False
        self.websocket_host = None
        self.websocket_error_callbacks = {}
        self.websocket_connect_callbacks = []
        self.connect_attempt = None
        self._web_thread = None
        self.count = 0

        self._osc_data = {}
        self.osc_client = None
        self._osc_server = None
        self._osc_thread = None
        self._osc_dispatch = None

        self.osc_host = "127.0.0.1"
        self.osc_send = 9000
        self.osc_recv = 9001

        self.create_callback = None
        self.roomid = None
        self.closed = False
        self.joinleave_callback = None
        self.last_change_sound = 9999999


    def do_sound(self, sound, event_type=1) -> None:
        settings:dict = AppSettings().load_settings("settings.json")
        do_sound:bool = settings["normal"]["joinSounds"]["value"]

        if do_sound:
            play_sound(sound)

        if self.joinleave_callback != None:
            self.joinleave_callback(event_type)       


    def change(self) -> None:
        settings:dict = AppSettings().load_settings("settings.json")
        do_sound:bool = settings["normal"]["changeSounds"]["value"]
        update_delay:float = settings["normal"]["changeDelay"]["value"]
        delay:float = 1 * max(0.04, update_delay)

        if time() - self.last_change_sound > delay and do_sound:
            self.last_change_sound = time()
            play_sound(change_sound)


    def subscribe_callback(self, callback_type, function) -> None:
        if not callback_type in self.websocket_error_callbacks:
            self.websocket_error_callbacks[callback_type] = []

        self.websocket_error_callbacks[callback_type].append(function)


    def unsubscribe_callback(self, callback_type, function) -> None:
        if not callback_type in self.websocket_error_callbacks:
            return
        if not function in self.websocket_error_callbacks[callback_type]:
            return
        
        self.websocket_error_callbacks[callback_type].remove(function)
        return
    

    def create_room(self, password, data) -> None:
        data = {
            "type":"create",
            "data":{
                "password":password,
                "data": data
            }
        }
        self.bg_send(dumps(data))


    def close(self) -> None:
        self.closed = True
        self._osc_server.shutdown()
        self.websocket.close()


    def init_websocket(self)-> None:
        thread = Thread(target=self._setup_socket)
        thread.start()
        self._web_thread = thread
    

    def bg_send(self, data:str) -> None:
        self.websocket.send(data)


    def init_osc(self) -> None:
        thread = Thread(target=asyncio.run, args=(self._osc_loop(),))
        thread.start()
        self._osc_thread = thread


    def reset_osc_dispatch(self) -> None:
        for param in self._osc_data:
            self._osc_dispatch.unmap(f"/avatar/parameters/{param}", self._osc_handle)


    def map_osc_dispatch(self) -> None:
        for param in self._osc_data:
            self._osc_dispatch.map(f"/avatar/parameters/{param}", self._osc_handle)


    async def _osc_loop(self):
        client = udp_client.SimpleUDPClient(self.osc_host, self.osc_send)
        dispatcher = Dispatcher()
        
        server = osc_server.ThreadingOSCUDPServer(
            (self.osc_host, self.osc_recv), dispatcher)
        
        self.osc_client = client
        self._osc_server = server
        self._osc_dispatch = dispatcher
        server.serve_forever()
    
    
    def _websocket_error(self, socket, error) -> None:
        print(type(error).__name__, error)
        if not self.websocket_error:
            Notification(AppSettings().root, "Failed to connect to server", **self.settings.BAD_NOTIFICATION)

        self.websocket_error:bool = True
        self.initialized:bool = False
        settings:dict = AppSettings().load_settings("settings.json", default_settings)
        host:str = settings["advanced"]["host"]["value"]

        error_type:type = type(error)
        if self.websocket_host != host:
            print("Host changed")
            socket.close()
        
        if not error_type in self.websocket_error_callbacks:
            return
        
        for f in self.websocket_error_callbacks[error_type]:
            f(error)


    def _on_websocket_connect(self, socket) -> None:
        if self.websocket_error:
            Notification(AppSettings().root, "Successfully reconnected to server", **self.settings.GOOD_NOTIFICATION)
        self.initialized = True
        self.websocket_error = False
        self.websocket = socket

        for f in self.websocket_connect_callbacks:
            f()

        print("Connected to socket")


    def _on_websocket_message(self, _, message) -> None:
        # print(message)
        msg = loads(message)
        self._socket_handle_input(msg)


    def _on_websocket_close(self, ws, close_status_code, close_msg) -> None:
        print("Closed!")
        self.initialized = False


    def _setup_socket(self) -> None:
        while not self.closed:
            settings = AppSettings().load_settings("settings.json", default_settings)
            socket_host = settings["advanced"]["host"]["value"]
            self.websocket_host = socket_host

            socket = WebSocketApp(socket_host, on_message=self._on_websocket_message, on_open=self._on_websocket_connect, on_close=self._on_websocket_close, on_error=self._websocket_error)
            self.websocket = socket
            socket.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})  


    def _osc_handle(self, adress:str, value) -> None:
        name:str = adress[len("/avatar/parameters/"):]
        (osc_value, locked) = self._osc_data[name]
        
        if name not in self._osc_data:
            return

        elif value == osc_value:
            return
        
        if type(value) == float:
            value = myround(value)
        
        # Osc data [0] = Value, [1] = Locked
        if locked == True:
            self.osc_client.send_message("/avatar/parameters/" + name, osc_value)
            return

        self._osc_data[name][0] = value
        self.bg_send(dumps({"type":"update","data":{"name":name, "value":value}}))
        self.count += 1


    def _socket_handle_input(self, data:dict) -> None:
        if "message" in data:
            print(data["message"])

        if not "type" in data:
            return

        handle_type:str = data["type"]

        if handle_type == "update":
            req_data = data["data"]
            name:str = req_data["name"]
            value = req_data["value"]
            locked:bool = req_data["locked"]

            if req_data["type"] == "float":
                value:float = myround(value)
            
            if self._osc_data[name][0] == value and self._osc_data[name][1] == locked:
                return

            self.change()
            self._osc_data[name] = [value, locked]
            self.osc_client.send_message("/avatar/parameters/"+name, value)

        elif handle_type == "connected":
            req_data:dict = data["data"]
            self.roomid:str = req_data["id"]
            self._osc_data:dict = {name:value[1:] for (name,value) in req_data["data"].items()}
            self.map_osc_dispatch()

            if self.create_callback != None:
                self.create_callback(self.roomid)

        elif handle_type == "disconnect":
            self.reset_osc_dispatch()
            self.roomid = None
            self._osc_data = {}
        
        elif handle_type == "user_joined":
            self.do_sound(join_sound, 1)
        
        elif handle_type == "user_left":
            self.do_sound(leave_sound, -1)

        else:
            print(data)


class StyleSettings():
    def __init__(self):
        self.TEXT_COLOR ="#96c2db"
        self.HEADER_COLOR ="#8ae09f"
        self.NAV_COLOR ="#1d273f"
        self.BACKGROUND_COLOR = "#0e1320"
        self.MENU_COLOR = "#182035"
        self.MENU_TITLE_COLOR = "#43527d"
        self.BUTTON_HOVER = "#232f4f"

        self.BAD_NOTIFICATION = {
            "fg_color"  : "#e07575",
            "text_color": "#182035",
            "border_width": 0
        }

        self.GOOD_NOTIFICATION = {
            "fg_color"  : "#8ae09f",
            "text_color": "#182035",
            "border_width": 0
        }

        self.SCROLL_BAR = {
            "scrollbar_button_color": "#182035",
            "scrollbar_button_hover_color": "#232f4f"
        }

        self.BUTTON_STYLE = {
            "fg_color":self.BACKGROUND_COLOR,
            "hover_color":self.BUTTON_HOVER,
            "text_color":self.TEXT_COLOR
        }

        self.NAV_BAR_BUTTON = {
            "text_color": self.TEXT_COLOR,
            "hover_color": "#293653",
            "height":60,
            "corner_radius":0,
            "font":CTkFont(size=18, weight="normal", family="Franklin Gothic Medium"),
            "anchor": "center",
            "fg_color": "transparent",
            "border_spacing":10
        }


class AppSettings():
    __instance = None
    
    def __new__(cls):
        if AppSettings.__instance == None:
            return super(AppSettings, cls).__new__(cls)
        return AppSettings.__instance

    def __init__(self):
        self.dir = os.getenv("APPDATA")

        if AppSettings.__instance != None:
            return
        
        self.cache = {}
        self.background_jobs:BackgroundJobs = None
        self.use_password:bool = False
        self.password:str = ""
        AppSettings.__instance = self

        self._check_file("settings.json", default=default_settings)


    def _check_file(self, filename:str="settings.json", default:dict={}):
        settings_file:str = path.join(self.dir, "VRC Control", filename)
        if path.isfile(settings_file): 
            return

        if not path.isdir(path.dirname(settings_file)):
            os.mkdir(path.dirname(settings_file))

        with open(settings_file, 'w') as f:
            dump(default, f, indent=4)


    def load_settings(self, filename:str="settings.json", default:dict={}) -> dict:
        if filename in self.cache:
            return self.cache[filename]

        self._check_file(filename, default=default)
        settings_file:str = path.join(self.dir, "VRC Control", filename)
        with open(settings_file, 'r') as f:
            data = load(f)
            self.cache[filename] = data
            return data


    def save_settings(self, value:dict, filename="settings.json"):
        self._check_file(filename)
        settings_file:str = path.join(self.dir, "VRC Control", filename)
        with open(settings_file, 'w') as f:
            dump(value, f, indent=4)

        self.cache[filename] = value


class CollapsibleFrame():
    def __init__(self, master, settings, title=None, item_settings={"sticky":"ew", 'padx':20}, collapsible=True, collapsed=False, *args, **kwargs):
        self.title_val = title
        self.frame_collapsed = CTkFrame(master, *args, **kwargs)
        self.frame_collapsed.grid_rowconfigure(1, weight=1)
        self.frame_collapsed.grid_columnconfigure(0, weight=1)

        self.unfold = CTkButton(self.frame_collapsed, text=title, hover=None, text_color=settings.MENU_TITLE_COLOR, fg_color="transparent", command=self.toggle, font=CTkFont(size=12, weight="bold"), anchor="center")
        self.unfold.grid(row=0, column=0, sticky="ew",padx=10)

        self.frame_open = CTkFrame(master, *args, **kwargs)
        self.frame_open.grid_rowconfigure(1, weight=1)
        self.frame_open.grid_columnconfigure(0, weight=1)

        if collapsible:
            self.fold = CTkButton(self.frame_open, text="- Collapse -", hover=None, text_color=settings.MENU_TITLE_COLOR, fg_color="transparent", command=self.toggle, height=1, font=CTkFont(size=10, weight="bold"), anchor="center")
            self.fold.grid(row=0, column=0, sticky="ew", padx=10)

        if title != None:
            self.title = CTkLabel(self.frame_open, text=title, text_color="white", font=CTkFont(size=24, weight="bold", family="Franklin Gothic Medium"))
            self.title.grid(row=collapsible, column=0, sticky="ew", padx=10, pady=(10,0))
            self.title.bind("<Button-1>", self.unfocus_all) 

        self.items = []
        self.item_settings = item_settings
        self.is_open = (not collapsed or not collapsible)
        self.offset = (title != None) + collapsible
        self.frame_grid = []

        self.frame_open.bind("<Button-1>", self.unfocus_all)


    def reset(self):
        for x in self.items:
            x.destroy()

    
    def unfocus_all(self, *args):
        if self.is_open:
            self.frame_open.focus()
        else:
            self.frame_collapsed.focus()

    
    def forget(self, item):
        item.grid_forget()
    

    def init_item(self,item:CTkBaseClass):
        if not item in self.items:
            raise ValueError("Item does not exist")
        
        index:int = self.items.index(item)

        settings = dict(self.item_settings)
        settings["pady"] = (10,0)

        if index == 0 and 0 == len(self.items)-1:
            settings["pady"] = (30,30)
        elif index == len(self.items)-1:
            settings["pady"] = (10, 30)
        elif index == 0:
            settings["pady"] = (30, 0)

        item.grid(row=index + self.offset, column=0, **settings)
        

    def add_item(self, item, *args, **kwargs) -> CTkBaseClass :
        item_var = item(self.frame_open, *args, **kwargs)
        self.items.append(item_var)
        item_var.bind("<Button-1>", self.unfocus_all)
        return item_var

    
    def grid(self, *args, **kwargs):
        self.frame_grid = [args, kwargs]
    

    def grid_forget(self):
        if self.is_open:
            self.frame_open.grid_forget()
        else:
            self.frame_collapsed.grid_forget()


    def toggle(self, value=None):
        if value != None:
            self.is_open = value
        else:
            self.is_open = not self.is_open

        if self.is_open:
            # self.frame_collapsed.grid_forget()
            self.frame_open.grid(*self.frame_grid[0], **self.frame_grid[1])
        else:
            self.frame_open.grid_forget()
            self.frame_collapsed.grid(*self.frame_grid[0], **self.frame_grid[1])


    def initialize(self):
        for item in self.items:
            self.init_item(item)
        
        if len(self.items) == 0 and self.title_val != None:
            self.title.grid(row=self.offset-1, column=0, sticky="ew", padx=10, pady=(10,20))
        
        self.toggle(self.is_open)


class SliderWithLabel(CTkFrame):
    def __init__(self, master, width=250, height=30, fg_color="transparent", text="CTkSlider", variable:Variable=None, text_color="white", font=None, slider_width=100, slider_height=18, progress_color=None, button_color=None, button_hover_color=None, update_callback=None, button_fg_color=None, *args, **kwargs):
        super().__init__(master, width=width, height=height ,fg_color=fg_color, *args, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)

        self.slider = CTkSlider(self, width=slider_width, height=slider_height, variable=variable, progress_color=progress_color, button_color=button_color, button_hover_color=button_hover_color, fg_color=button_fg_color)
        self.slider.grid(row=0, column=0, sticky="sw")
        self.text = CTkLabel(self, text=text, font=font, text_color=text_color)
        self.text.grid(row=0, column=1, sticky="news")
    
        self.slider.bind("<ButtonRelease>", update_callback)


    def bind(self, event, command, add=True):
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        
        self._canvas.bind(event, command)
        self.slider.bind(event, command)
        self.text.bind(event, command)


    def bind_slider(self, event, command):
        self.slider.bind(event, command)


class TextboxWithLabel(CTkFrame):
    def __init__(self, master, width=250, height=30, fg_color="transparent", update_callback=None, box_text_color="white", bg_color=None, text="CTkTextbox", variable:Variable=None, text_color="white", font=None, max_characters=0, placeholder="Placeholder", *args, **kwargs):
        super().__init__(master, width=width, height=height ,fg_color=fg_color, *args, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)

        self.var = variable
        self.max_len = max_characters
        self.box = CTkEntry(self, textvariable=variable, height=20, width=350, fg_color=bg_color, state="normal", border_width=0, text_color=box_text_color, placeholder_text=placeholder)
        self.box.grid(row=0, column=0, sticky="nws")
        self.text = CTkLabel(self, text=(" "*5)+text, font=font, text_color=text_color)
        self.text.grid(row=0, column=1, sticky="news")

        self.box.bind("<FocusOut>", update_callback)
        self.box.bind("<Return>", update_callback)
        variable.trace("w", self.on_change)


    def on_change(self, a, b, c):
        value = self.var.get()
        if len(value) > self.max_len and self.max_len != 0:
            self.var.set(value[:self.max_len])


    def set(self, value:str):
        self.box.delete(0, 'end')
        self.box.insert(0, value)
    
    
    def bind(self, event, command, add=True):
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        
        self._canvas.bind(event, command)
        self.text.bind(event, command)
    

    def bind_text(self, event, command):
        self.box.bind(event, command)


class SettingsSwitch(CTkFrame):
    def __init__(self, master, width=250, height=30, update_callback=None, fg_color="transparent", button_fg_color=None, button_hover_color=None, button_color=None, progress_color=None, text=None, variable:Variable=None, text_color="white", font=None, *args, **kwargs):
        super().__init__(master, width=width, height=height ,fg_color=fg_color, *args, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.switch = CTkSwitch(self, variable=variable, width=width, height=height, button_hover_color=button_hover_color, button_color=button_color, fg_color=button_fg_color, text=text, progress_color=progress_color, text_color=text_color, font=font)
        self.switch.grid(row=0, column=0, sticky="news")

        self.switch.bind("<ButtonRelease>", update_callback)
    
    def bind(self, event, command, add=True):
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        
        self._canvas.bind(event, command)
        self.switch.bind(event, command)


class SettingsPath(CTkFrame):
    def __init__(self, master, width=250, update_callback=None, height=30, fg_color="transparent", box_text_color="white", bg_color=None, text="CTkTextbox", button_hover=None, variable:Variable=None, text_color="white", font=None, scrollbar_button_color=None, scrollbar_button_hover_color=None, *args, **kwargs):
        super().__init__(master, width=width, height=height ,fg_color=fg_color, *args, **kwargs)
        self.variable = variable
        self.update_callback = update_callback

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.box = CTkScrollableFrame(self, fg_color=bg_color, height=20, width=0, orientation="horizontal", scrollbar_button_color=scrollbar_button_color, scrollbar_button_hover_color=scrollbar_button_hover_color)
        self.directory = CTkLabel(self.box, text_color=box_text_color, textvariable=variable)
        self.directory.grid(row=0, column=0, sticky="news")

        self.box.grid(row=0, column=1, sticky="news")

        self.button = CTkButton(self, text="Change", width=40, font=font, text_color=text_color, fg_color=bg_color, hover_color=button_hover, command=self.get_new_path)
        self.button.grid(row=0, column=2, padx=(20,0), sticky="e")

        self.text = CTkLabel(self, text=text, font=font, text_color=text_color)
        self.text.grid(row=0, column=3, sticky="we")
    

    def get_new_path(self):
        if self.update_callback:
            val = filedialog.askdirectory()
            if val == "": return

            self.variable.set(val)
            self.update_callback()


    def bind(self, event, command, add=True):
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        
        self._canvas.bind(event, command)
        self.box.bind(event, command)
        self.text.bind(event, command)


class SettingsDropdown(CTkFrame):
    def __init__(self, master, width=250, height=30, values=[], fg_color=None, button_fg_color=None, text="CTkOptionsMenu", text_color="white", font=None, *args, **kwargs):
        super().__init__(master, width=width, height=height, fg_color="transparent", *args, **kwargs)

        self.dropdown = CTkOptionMenu(self, values=values, fg_color=fg_color, text_color=text_color, button_color=button_fg_color, dropdown_fg_color=fg_color, dropdown_text_color=text_color, dropdown_hover_color=button_fg_color)
        self.dropdown._dropdown_menu.configure(activeborder=10)
        self.dropdown.grid(row=0, column=0, padx=(20,0), sticky="nws")

        self.text = CTkLabel(self, text=(' '*5) +text, text_color=text_color, font=font)
        self.text.grid(row=0, column=1, sticky="news")


class ButtonWithLabel(CTkFrame):
    def __init__(self, master, width=250, height=30, fg_color="transparent", bg_color="transparent", text=None, label_text="CtkButton", button_hover=None, variable:Variable=None, text_color="white", font=None, command=None, *args, **kwargs):
        super().__init__(master, width=width, height=height ,fg_color=bg_color, *args, **kwargs)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)

        self.button = CTkButton(self, width=width, fg_color=fg_color, text=text, hover_color=button_hover, textvariable=variable,text_color=text_color, font=font, command=command) 
        self.button.grid(row=0, column=0)

        self.label = CTkLabel(self, text_color=text_color, font=font, text=(" "*5)+label_text)
        self.label.grid(row=0, column=1)


    def bind(self, event, command, add=True):
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        
        self._canvas.bind(event, command)
        self.button.bind(event, command)
        self.label.bind(event, command)


class SelectItems(CTkScrollableFrame):
    def __init__(self, master, settings, variable=None, callback=None, bg_color=None,scrollbar_button_color=None, scrollbar_button_hover_color=None):
        super().__init__(master, height=0, fg_color=bg_color, corner_radius=0, scrollbar_button_color=scrollbar_button_color, scrollbar_button_hover_color=scrollbar_button_hover_color)
        self.settings = settings
        self.var = variable
        self.items = []
        self.callback = callback

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)


    def load_values(self, values):
        settings = self.settings
        for i,x in enumerate(values):
            button = CTkButton(master=self, text=str(x), corner_radius=0, height=25, fg_color=settings.BACKGROUND_COLOR, hover_color=settings.BUTTON_HOVER, text_color=settings.TEXT_COLOR, font=CTkFont(size=16), command=self.select(x))
            button.grid(row=i, column=0, padx=0, sticky="ew")
            self.items.append(button)



    def select(self, value):
        def inner():
            self._parent_canvas.yview_moveto(0)
            self.configure(height=1)
            if self.var != None:
                self.var.set(value)

            for item in self.items:
                item.destroy()

            self.configure(height=0)

            self.items = []

            if self.callback != None:
                self.callback()
        return inner
    

class BoolSelect(CTkFrame):
    def __init__(self, master, fg_color="#888", selected_color="#bbb", text_color="black", selected_text_color="black", hover_color="#aaa"):
        super().__init__(master, fg_color="transparent", height=1)
        self.fg_color = fg_color
        self.selected_color = selected_color
        self.text_color = text_color
        self.selected_text_color = selected_text_color
        self.hover_color = hover_color

        self.style = {
            True: {"fg_color":self.selected_color, "text_color":self.selected_text_color},
            False: {"fg_color":self.fg_color, "text_color":self.text_color}
        }

        self.grid_columnconfigure((1,2,3), weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.items = {}
    

    def callback_function(self, frame, value):
        def inner(a):
            val = self.items[value]["selected"]
            self.items[value]["selected"] = not val
            frame.configure(**self.style[not val])

        return inner
    

    def get_values(self):
        temp = {}
        for (name, item) in self.items.items():
            if item["selected"]:
                temp[name] = item["selected"]

        return temp


    def reset(self):
        for (k,item) in self.items.items():
            item["item"].destroy()
        self.items = {}


    def load_values(self, values:dict):
        self.grid_rowconfigure(len(values), weight=1)

        for (name, selected) in values.items():
            label = CTkButton(self, width=300, text=name, corner_radius=0, hover_color=self.hover_color, **self.style[selected])
            label.grid(row=0, column=0, sticky="we")
            label.bind("<Button-1>", self.callback_function(label, name))

            index = len(self.items)
            label.grid(row=index//3, column=index%3+1)
            self.items[name] = {
                "selected":selected,
                "item":label
            }


class Notification(CTkFrame):
    def __init__(self, master, text:str="", fg_color=None, border_color=None, text_color=None, border_width=2, **kwargs):
        self.root = get_root(master)
        super().__init__(self.root, corner_radius=10, fg_color=fg_color, border_color=border_color, border_width=border_width, cursor="hand2", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.label = CTkLabel(self, height=60, text=text, text_color=text_color, justify=LEFT, font=CTkFont(size=16))
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="news")
        self.label.bind("<Button-1>", self.click_callback)

        self.bind("<Button-1>", self.click_callback)
        self.root.notifications.append(self)
        self.place(relx=0.5, x=100, y=35, anchor="center", relwidth=0.6)
        
    
    def click_callback(self, _):
        self.root.notifications.remove(self)
        self.destroy()
        
        