from aiohttp import web
import json
from pythonosc.udp_client import SimpleUDPClient
import time
from cprint import cprint

# Webserver's database basically
class Params():
    def clear(self):
        self.put_func = None
        self.get_func = None
        self.cache = None
        self.osc = None
        self.last_update = 0
    
    def set(self, put, get, client) -> None:
        self.put_func = put
        self.get_func = get
        self.osc = client
    
    def get(self, cache=False) -> dict:
        # No cache detected
        if cache and self.cache == None:
            params = self.get_func()
            self.cache = params
            return params

        # Return cache
        elif cache or time.time() - self.last_update < 1:
            return self.cache
        
        self.last_update = time.time()
        self.cache = self.get_func()
        return self.cache

    def put(self, name, val) -> None:
        self.put_func(name, val)

# Input types
types = {
    'Bool' : '<input type="checkbox" name="&NAME&" autocomplete="off">',
    'Float': '<input type="range" name="&NAME&" min="0" max="1" value="0" step="0.05" autocomplete="off">',
    'Int'  : '<input type="range" name="&NAME&" min="0" max="10" value="0" step="1" autocomplete="off">'
}

# Convert from 
get_value = {
    "Bool" : lambda v: v==1,
    "Int"  : lambda v: round(float(v)),
    "Float": float
}

# parameter template
#
# &NAME& Becomes parameter name
# &INPUT& Becomes a input type from the types dictionary above
#
param_html = """
<div class="parameter">
    <p>&NAME&</p>
    &INPUT&
    <img src="images/unlocked.png" name='&NAME&'>
</div>
"""[1:]

def html(text) -> web.Response:
    return web.Response(text=text, content_type="text/html")

# Prepare globals
parameters = Params()
routes = web.RouteTableDef()
app = web.Application()

# Static routes for css / js / images
routes.static("/css","web/css")
routes.static("/js","web/js")
routes.static("/images","web/images")

# /set
#
# Backend API to set / lock parameters
@routes.post("/set")
async def set(request:web.Request):
    data = await request.content.read()
    json_data = json.loads(data.decode())

    # Get updated parameters from database
    params = parameters.get()

    # set parameter value
    if json_data['type'] == "value":
        new_value = params[json_data['name']]
        new_value['value'] = get_value[new_value['type']](json_data['value'])

        # Save in database
        parameters.put(json_data['name'], new_value)
        # Send to vrchat
        parameters.osc.send_message("/avatar/parameters/"+json_data['name'], new_value['value'])

        # Display to console
        cprint(f"[Y][CONTROL] [GR]Set[E] [G]'{json_data['name']}'[E] : [B]{new_value['value']}")
    
    # Toggle parameter locked
    elif json_data['type'] == "lock":
        new_value = params[json_data['name']]
        new_value['locked'] = json_data['value']

        # Save to database
        parameters.put(json_data['name'], new_value)

        # Diisplay to console
        text = "Locked" if new_value['locked'] == 1 else "Unlocked"
        cprint(f"[Y][CONTROL] [R]{text}[E] : [G]'{json_data['name']}'")

    # Success response
    return web.Response(text="success")

# /get
#
# backend API to receive current parameter values
@routes.get("/get")
async def new_values(request): 
    # Get parameters from database
    params = parameters.get()
    # json response
    return web.Response(text=json.dumps(params))


# Index
#
# Base UI for users
@routes.get("/")
async def index(request):
    with open("web/index.html",'r') as f:
        raw_html = f.read()
    
    # Get cached parameters from database
    params = parameters.get(cache=True)

    content = ""
    for name,param in params.items():
        # Get input type from dictionary
        input_html = types[param['type']]
        # Change template to fit parameter
        content += param_html.replace("&INPUT&", input_html).replace("&NAME&", name)
    
    # Add new parameters to HTML
    new_html = raw_html.replace("&CONTENT&", content)
    # Display new HTML
    return html(new_html)


# Apply all routes
app.add_routes(routes)

def run(param_put:callable, param_get:callable, osc_client:SimpleUDPClient, port:int) -> None:
    # Clear database and prepare for new values
    parameters.clear()
    # Set back-end functions 
    parameters.set(param_put, param_get, osc_client)

    portadd = "" if port == 80 else f":{port}"

    cprint(f"[GR][SERVER][E] Webserver running on '[B][U]http://localhost{portadd}[E]'")
    web.run_app(app, host="127.0.0.1", port=port, print=None)
