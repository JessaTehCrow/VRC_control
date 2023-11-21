from customtkinter import *
from program_utils import *
import pages

if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))

class Navbar(CTkFrame):
    def __init__(self, master, settings, *args, **kwargs):
        super().__init__(master, corner_radius=0, width=200, fg_color=settings.NAV_COLOR, *args, **kwargs)
        self.navigation_frame_label = CTkLabel(self, text="VRC Control", font=CTkFont(size=25, weight="bold", family="Verdana"), text_color=settings.HEADER_COLOR)
        self.navigation_frame_label.grid(row=0, column=0, padx=20, pady=(20,50))

        self.grid_rowconfigure(5, weight=1)
        self.buttons = {}
        self.master = master
        self.settings = settings

        self.add_button("New Instance", pages.NewInstance)
        self.add_button("Settings", pages.Settings)
    

    def add_button(self, text, page):
        btn = CTkButton(self, text=text, **self.settings.NAV_BAR_BUTTON, command=self.master.page_callback(page))
        btn.grid(row=1 + len(self.buttons), column=0, sticky="ew")

        self.buttons[page.__name__] = btn
    

    def update_buttons(self):
        for (tag,btn) in self.buttons.items():
            if tag == self.settings.ACTIVE_PAGE:
                btn.configure(fg_color=self.settings.NAV_BAR_BUTTON["hover_color"])
            else:
                btn.configure(**self.settings.NAV_BAR_BUTTON)


class App(CTk):
    def __init__(self, main_page):
        super().__init__()
        self.wm_iconbitmap(get_file("data/CTRL.ico"))

        self.display = CTkFrame(self)
        self.settings = StyleSettings()

        AppSettings().root = self
        AppSettings().background_jobs.settings = self.settings

        self.cache = {}
        self.notifications = []

        self.title("VRC Control")
        self.geometry("1000x600")
        self.minsize(1000,600)

        self.configure(fg_color="#0e1320")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.navbar = Navbar(self, self.settings)
        self.navbar.grid(row=0, column=0, sticky="wsn")

        self.set_display(main_page)

        Notification(self, "NOTE: Update checker & Auto updater do not work yet", **self.settings.BAD_NOTIFICATION)


    def notification_callback(self, _):
        self.notification.destroy()


    def set_display(self, page):
        self.settings.ACTIVE_PAGE = page.__name__
        old = self.display

        if page.__name__ in self.cache:
            self.display = self.cache[page.__name__]
        else:
            self.display:CTkFrame = page(self, self.settings)
            self.cache[page.__name__] = self.display

        old.grid_forget()
        self.display.grid(row=0, column=1, sticky="news")

        self.navbar.update_buttons()
        for notification in self.notifications:
            notification.lift(self.display)
    

    def page_callback(self, page):
        def inner():
            self.set_display(page)
        return inner


if __name__ == "__main__":
    AppSettings().background_jobs = BackgroundJobs()
    AppSettings().background_jobs.init_websocket()
    AppSettings().background_jobs.init_osc()

    app = App(pages.NewInstance)    
    try:
        app.mainloop()
    except Exception as e:
        print(e)

    AppSettings().background_jobs.close()