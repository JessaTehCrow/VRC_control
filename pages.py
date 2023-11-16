from customtkinter import *
from utils import *


class Settings(CTkScrollableFrame):
    def __init__(self, master, settings, *args, **kwargs):
        super().__init__(master, corner_radius=0, *args, **kwargs, fg_color=settings.BACKGROUND_COLOR, **settings.SCROLL_BAR)
        self.settings:StyleSettings = settings
        self.values = {}
        self.root = master

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.normal = CollapsibleFrame(self, settings, title="Settings", item_settings={"sticky":"ew", "padx":50,}, height=50, fg_color=settings.MENU_COLOR)
        self.normal.grid(row=0, column=0, sticky="ew", padx=20, pady=20)

        self.advanced = CollapsibleFrame(self, settings, title="Advanced", collapsed=True, item_settings={"sticky":"ew","padx":50}, height=50, fg_color=settings.MENU_COLOR)
        self.advanced.grid(row=1, column=0, sticky="ew", padx=20, pady=20)

        self.load_settings()
    

    def load_settings(self):
        self.appsettings = AppSettings().load_settings(default=default_settings)

        def add_setting(frame:CollapsibleFrame, key, data):
            name = data["name"]
            value = data["value"]
            val_type = type(data["value"])
            name = (" "*5) + name

            if val_type == bool:
                self.values[key] = BooleanVar(self, value=value)
                item = frame.add_item(SettingsSwitch, update_callback=self.save_settings, variable=self.values[k], progress_color=self.settings.HEADER_COLOR, text=name, button_color="#5e7197", button_hover_color="#5e7197", button_fg_color=self.settings.BACKGROUND_COLOR, font=CTkFont(size=15),text_color=self.settings.TEXT_COLOR)

            elif val_type == float:
                self.values[key] = DoubleVar(self, value=value)
                item = frame.add_item(SliderWithLabel, update_callback=self.save_settings, slider_width=150, variable=self.values[k], progress_color=self.settings.HEADER_COLOR, text=name, font=CTkFont(size=15), text_color=self.settings.TEXT_COLOR, button_color="#5e7197", button_hover_color="#5e7197", button_fg_color=self.settings.BACKGROUND_COLOR)

            elif val_type == str and data["type"] == "text":
                self.values[key] = StringVar(self, value=value)
                item = frame.add_item(TextboxWithLabel, update_callback=self.save_settings, variable=self.values[k], bg_color=self.settings.BACKGROUND_COLOR, text=name, font=CTkFont(size=15), text_color=self.settings.TEXT_COLOR, box_text_color=self.settings.TEXT_COLOR)
                item.bind_text("<Return>", self.normal.unfocus_all)
            
            elif val_type == str and data["type"] == "path":
                self.values[key] = StringVar(self, value)
                item = frame.add_item(SettingsPath, update_callback=self.save_settings, variable=self.values[k], bg_color=self.settings.BACKGROUND_COLOR, text=name, font=CTkFont(size=15), text_color=self.settings.TEXT_COLOR, box_text_color=self.settings.TEXT_COLOR, button_hover=self.settings.BUTTON_HOVER, **self.settings.SCROLL_BAR)
            
            else:
                print("oh no", data)
            
            item.bind("<Button-1>", self.normal.unfocus_all)

        #open file here or smn
        # self.normal.add_item
        for (k,v) in self.appsettings['normal'].items():
            add_setting(self.normal, k, v)

        for (k,v) in self.appsettings["advanced"].items():
            add_setting(self.advanced, k, v)

        self.normal.initialize()
        self.advanced.initialize()
    

    def save_settings(self, *args, **kwargs):
        for (type, settings) in self.appsettings.items():
            for setting in settings:
                self.appsettings[type][setting]["value"] = self.values[setting].get()
        
        AppSettings().save_settings(self.appsettings)


class NewInstance(CTkScrollableFrame):
    def __init__(self, master, settings:StyleSettings, *args, **kwargs):
        super().__init__(master, corner_radius=0, *args, **kwargs,fg_color=settings.BACKGROUND_COLOR, **settings.SCROLL_BAR)
        self.settings = settings
        self.avatars = get_avatars()
        self.open = False
        self.room_window = None

        self.use_password = BooleanVar(self, False)
        self.password = StringVar(self, "")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.selected = StringVar(self, "Select Avatar")
        self.normal = CTkFrame(self, height=50, fg_color=settings.MENU_COLOR)
        self.normal.grid_rowconfigure(2, weight=1)
        self.normal.grid_columnconfigure(0, weight=1)

        self.normal.grid(row=0, column=0, sticky="we", padx=20, pady=20)
        self.button = CTkButton(self.normal, command=self.load_names, textvariable=self.selected, fg_color=settings.BACKGROUND_COLOR, text_color=settings.TEXT_COLOR, hover_color=settings.BUTTON_HOVER, font=CTkFont(size=20))
        self.button.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        self.select = SelectItems(self.normal, self.settings, variable=self.selected, callback=self.callback_function, bg_color=self.settings.BACKGROUND_COLOR, **self.settings.SCROLL_BAR)

        self.params = CollapsibleFrame(self, settings, title="Select Parameters", collapsed=False, item_settings={"sticky":"ew","padx":50}, height=50, fg_color=settings.MENU_COLOR)
        self.params.grid(row=1, column=0, padx=20, pady=20, sticky="news")

        self.param_select = self.params.add_item(BoolSelect, fg_color=settings.BACKGROUND_COLOR, selected_color=settings.BUTTON_HOVER, text_color=settings.TEXT_COLOR, selected_text_color=settings.HEADER_COLOR, hover_color=settings.NAV_COLOR)

        self.params.add_item(SettingsSwitch, variable=self.use_password, text="Use Password", progress_color=self.settings.HEADER_COLOR, button_color="#5e7197", button_hover_color="#5e7197", button_fg_color=self.settings.BACKGROUND_COLOR, font=CTkFont(size=15),text_color=self.settings.TEXT_COLOR)
        self.params.add_item(TextboxWithLabel, variable=self.password, text="Password", placeholder="Password", max_characters=16, bg_color=self.settings.BACKGROUND_COLOR, font=CTkFont(size=15), text_color=self.settings.TEXT_COLOR, box_text_color=self.settings.TEXT_COLOR)
        self.params.add_item(CTkButton, text="confirm", fg_color=settings.BACKGROUND_COLOR, hover_color=settings.BUTTON_HOVER, text_color=settings.TEXT_COLOR, command=self.create_room)


    def room_closed(self):
        self.selected.set("Select Avatar")
        self.room_window = None
        self.button.configure(command=self.load_names)


    def create_room(self):
        vals = self.param_select.get_values()
        valid = False

        AppSettings().use_password = self.use_password.get()
        AppSettings().password = self.password.get()

        for x in vals:
            valid = vals[x] or valid
        
        if not valid:
            return
        
        else:
            avi_name = self.selected.get()
            values = self.param_select.get_values()
            avi_settings = AppSettings().load_settings("avatars.json")
            avi_settings[avi_name] = values
            AppSettings().save_settings(avi_settings, "avatars.json")

            self.selected.set("Room Already Created")
            self.param_select.reset()
            self.params.grid_forget()
            self._parent_canvas.yview_moveto(0)
            window = RoomWindow(self.settings, close_callback=self.room_closed)
            self.room_window = window
            self.button.configure(command=self.room_window.focus)


    def load_names(self):
        self.params.grid_forget()
        self.button.configure(state="disabled")
        self.select.load_values(sorted(list(self.avatars.keys())))
        self.select.grid(row=1, column=0, sticky="sew", padx=20, pady=(0,20))


    def callback_function(self):
        self._parent_canvas.yview("moveto", 0)
        self.select.grid_forget()
        self.button.configure(state="normal")
        
        avi_name = self.selected.get()
        avi_settings = AppSettings().load_settings("avatars.json")

        values = {x["name"]:False for x in self.avatars[avi_name]["parameters"]}

        if avi_name in avi_settings:
            values = {**values, **avi_settings[avi_name]}
        
        self.param_select.reset()
        self.param_select.load_values(values)

        self.params.initialize()