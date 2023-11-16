from customtkinter import *
from pythonosc import osc_server, udp_client
from pythonosc.dispatcher import Dispatcher

import string
import os
import json
import websocket
import threading
import asyncio


def myround(x, prec=2, base=.075):
    return round(base * round(float(x)/base),prec)

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
    "normal":{
        "update": {
            "name":"Check for updates",
            "value":True
        },
        "autoUpdate": {
            "name":"Auto Update",
            "value": True
        },
        "joinSounds": {
            "name":"Join / Leave sounds",
            "value": True
        },
        "closeSounds":{
            "name":"Sounds on room close",
            "value": True
        },
        "volume": {
            "name": "Sound volume",
            "value": 0.5
        }
    },

    "advanced": {
        "host": {
            "name": "Host",
            "value": "https://localhost:8000",
            "type":"text"
        },
        "vrcfolder": {
            "name": "OSC Avatar folder",
            "value": "",
            "type":"path"
        }
    }
}


def get_avatars():
    folder:str = AppSettings().load_settings(default=default_settings)["advanced"]["vrcfolder"]["value"]
    avatars = {}
    if not os.path.isdir(folder):
        return avatars        

    for path in os.listdir(folder):
        if not path.endswith(".json"):
            continue
        
        with open(os.path.join(folder, path), 'rb') as f:
            raw = f.read()
            raw = raw.decode('Windows-1252', 'ignore')
            raw = ''.join([x for x in raw if x in string.printable])

            json_data = raw[raw.index("{"):]
            data = json.loads(json_data)
            if not "name" in data:
                print("Invalid avatar file")
                continue

            offset = 0
            
            for i in range(len(data["parameters"])):
                name = data["parameters"][i-offset]["name"]
                if name in parameter_ignore_list:
                    data["parameters"].pop(i-offset)
                    offset += 1

            avatars[data["name"]] = data

    return avatars


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
            print("NEW VALUE:", value)
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


class StyleSettings():
    def __init__(self):
        self.TEXT_COLOR ="#96c2db"
        self.HEADER_COLOR ="#8ae09f"
        self.NAV_COLOR ="#1d273f"
        self.BACKGROUND_COLOR = "#0e1320"
        self.MENU_COLOR = "#182035"
        self.MENU_TITLE_COLOR = "#43527d"
        self.BUTTON_HOVER = "#232f4f"

        self.SCROLL_BAR = {
            "scrollbar_button_color": "#182035",
            "scrollbar_button_hover_color": "#232f4f"
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
        
        self.background_jobs:BackgroundJobs = None
        self.use_password:bool = False
        self.password:str = ""
        AppSettings.__instance = self


    def _check_file(self, filename="settings.json", default:dict={}):
        settings_file = os.path.join(self.dir, "VRC Control", filename)
        if os.path.isfile(settings_file): 
            return

        if not os.path.isdir(self.dir):
            os.mkdir(os.path.dirname(settings_file))

        with open(settings_file, 'w') as f:
            json.dump(default, f, indent=4)


    def load_settings(self, filename="settings.json", default={}):
        self._check_file(filename, default=default)
        settings_file = os.path.join(self.dir, "VRC Control", filename)
        with open(settings_file, 'r') as f:
            return json.load(f)


    def save_settings(self, value:dict, filename="settings.json"):
        self._check_file(filename)
        settings_file = os.path.join(self.dir, "VRC Control", filename)
        with open(settings_file, 'w') as f:
            json.dump(value, f, indent=4)


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
        self.is_open = not collapsed or not collapsible
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
    

    def init_item(self,item):
        if not item in self.items:
            raise ValueError("Item does not exist")
        
        index = self.items.index(item)

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
        if value:
            self.is_open = value
        else:
            self.is_open = not self.is_open

        if self.is_open == 1:
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


class RoomWindow(CTkToplevel):
    def __init__(self, settings:StyleSettings, close_callback=None, *args, **kwargs):
        super().__init__(*args, fg_color=settings.BACKGROUND_COLOR, **kwargs)
        self.close_callback = close_callback
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.bg_jobs:BackgroundJobs = AppSettings().background_jobs

        self.title("Room")
        self.geometry("400x250")
        self.resizable(0, 0)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.label = CTkLabel(self, text="Connecting...")
        self.label.grid(row=0, column=0)

        self.focus()


    def clear_frame(self):
        for x in self.winfo_children():
            x.grid_forget()

    
    def connect(self):
        self.clear_frame()
        self.label = CTkLabel(self, text="Connecting...")
        self.label.grid(row=0, column=0)


    def focus(self):
        self.state('normal')
        self.label.focus_set()
    

    def on_close(self):
        self.bg_jobs
        if self.close_callback != None:
            self.close_callback()
        
        self.destroy()