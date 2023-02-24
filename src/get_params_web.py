from aiohttp import web, web_request
import json
import threading
import asyncio
from cprint import cprint

# 'Database'
class Data():
    data = []
    result = None

    def clear(self):
        self.data = []
        self.result = None

# Parameter template
#
# &NAME& Becomes parameter name
# &INPUT& Becomes a input type from the types dictionary above
param_html = """
<div class="parameter">
    <p>&NAME&</p>
    <input type="checkbox" name="&NAME&" autocomplete="off">
</div>
"""[1:]

def html(text):
    return web.Response(text=text, content_type="text/html")

# Define globals
parameters = []
routes = web.RouteTableDef()
data = Data()
routes.static("/css","web/css")
routes.static("/js","web/js")

@routes.get('/')
async def handle(request):
    with open("web/select.html") as f:
        raw_html = f.read()

    content = ""
    for param in data.data:
        content += param_html.replace("&NAME&", param[0])

    new_html = raw_html.replace("&CONTENT&", content)
    return html(new_html)


@routes.post("/submit")
async def submit(request:web_request.Request):
    req_data = await request.content.read()
    try:
        # Load json data
        req_data = json.loads(req_data.decode())
    except Exception:
        print("[ERR] Invalid json")
        return web.Response(text="Invalid json")

    if len(req_data) == 0:
        print("[ERR] Not enough parameters")
        return web.Response(text="Select at least one parameter")
        
    data.result = req_data

    # Close async tasks
    for task in asyncio.all_tasks():
        task.cancel()
    
    # Await server shut down
    await asyncio.sleep(100)


def thread_func(out,port:int) -> None:
    # Create app for thread
    app = web.Application()
    app.add_routes(routes)
    data = out

    # Create new event loop for thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        web.run_app(app, host="127.0.0.1", port=port, print=None)
    except asyncio.exceptions.CancelledError:
        # Server closed
        pass

def get_parameters(params:dict, port:int) -> list:
    data.clear()
    data.data = params

    port_add = "" if port == 80 else f":{port}"

    # Create web thread
    cprint(f"\n[GR][INFO][E] Open '[B][U]http://localhost{port_add}[E]' in your browser!")
    web_app = threading.Thread(target=thread_func, args=(data,port,))
    web_app.start()
    web_app.join()

    # Return data
    return data.result